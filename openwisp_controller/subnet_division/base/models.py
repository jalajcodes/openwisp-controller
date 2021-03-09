from ipaddress import ip_network

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from swapper import get_model_name

from openwisp_users.mixins import OrgMixin
from openwisp_utils.base import TimeStampedEditableModel


class AbstractSubnetDivisionRule(TimeStampedEditableModel, OrgMixin):
    SUBNET_DIVISION_TYPES = [('vpn', 'VPN')]

    type = models.CharField(max_length=30, choices=SUBNET_DIVISION_TYPES)
    label = models.CharField(max_length=30)
    number_of_subnets = models.PositiveIntegerField()
    number_of_ips = models.PositiveIntegerField()
    size = models.IntegerField()
    # NOTE: Make master_subnet a cached_property since it is utilized often?
    master_subnet = models.ForeignKey(
        get_model_name('openwisp_ipam', 'Subnet'), on_delete=models.CASCADE
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['organization', 'label'], name='unique_label_per_organization',
            ),
        ]

    def __str__(self):
        return f'{self.label}'

    def clean(self):
        self._validate_master_subnet_consistency()
        self._validate_ip_address_consistency()

    def _validate_master_subnet_consistency(self):
        master_subnet_prefix = ip_network(self.master_subnet.subnet).prefixlen
        # Validate size of generated subnet is not greater than size of master subnet
        if master_subnet_prefix >= self.size:
            raise ValidationError(
                {'size': _('Subnet size exceed the size of master subnet')}
            )

        # Validate master subnet can accommodate required number of generated subnets
        if self.number_of_subnets > (2 ** (self.size - master_subnet_prefix)):
            raise ValidationError(
                {
                    'number_of_subnets': _(
                        f'Master subnet cannot accommodate {self.number_of_subnets} '
                        f'subnets of size /{self.size}'
                    )
                }
            )

    def _validate_ip_address_consistency(self):
        # Validate individual generated subnet can accommodate required number of IPs
        try:
            next(
                ip_network(str(self.master_subnet.subnet)).subnets(new_prefix=self.size)
            )[self.number_of_ips]
        except IndexError:
            raise ValidationError(
                {
                    'number_of_ips': _(
                        f'Generated subnets of size /{self.size} cannot accommodate '
                        f'{self.number_of_ips} IP Addresses.'
                    )
                }
            )

    @property
    def prefixlen(self):
        return self.size


class AbstractSubnetDivisionIndex(models.Model):
    keyword = models.CharField(max_length=30)
    subnet = models.ForeignKey(
        get_model_name('openwisp_ipam', 'Subnet'), on_delete=models.CASCADE, null=True,
    )
    ip = models.ForeignKey(
        get_model_name('openwisp_ipam', 'IpAddress'),
        on_delete=models.CASCADE,
        null=True,
    )
    rule = models.ForeignKey(
        get_model_name('subnet_division', 'SubnetDivisionRule'),
        on_delete=models.CASCADE,
    )
    config = models.ForeignKey(
        get_model_name('config', 'Config'), on_delete=models.CASCADE, null=True
    )

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['keyword']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['keyword', 'subnet', 'ip', 'config'],
                name='unique_subnet_division_index',
            ),
        ]
