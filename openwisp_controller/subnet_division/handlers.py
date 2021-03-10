from django.db.models import Q
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from netaddr import IPNetwork
from swapper import load_model

from .exceptions import InvalidVariableName
from .tasks import create_subnet_ip_division_rule_index

Subnet = load_model('openwisp_ipam', 'Subnet')
IpAddress = load_model('openwisp_ipam', 'IpAddress')
SubnetDivisionRule = load_model('subnet_division', 'SubnetDivisionRule')
SubnetDivisionIndex = load_model('subnet_division', 'SubnetDivisionIndex')
VpnClient = load_model('config', 'VpnClient')


@receiver(
    post_save, sender=SubnetDivisionRule, dispatch_uid='subnet_division_index_prefixlen'
)
def add_subnet_division_rule_prefixlen(sender, instance, created, **kwargs):
    if created:
        SubnetDivisionIndex.objects.create(
            keyword=f'{instance.label}_prefixlen', rule_id=instance.id
        )
    else:
        SubnetDivisionIndex.objects.filter(
            rule_id=instance.id, subnet_id=None, ip_id=None
        ).update(keyword=f'{instance.label}_prefixlen')

        # TODO: Update labels for rest of the entries


@receiver(post_save, sender=VpnClient, dispatch_uid='vpn_client_provision_subnet')
def provision_subnets_ips(instance, **kwargs):
    try:
        division_rule = instance.vpn.subnet.subnetdivisionrule_set.get(
            organization_id=instance.vpn.organization_id, type='vpn',
        )
    except AttributeError:
        return

    # Check subnets and IPs are already provisioned for this Config
    if SubnetDivisionIndex.objects.filter(
        config_id=instance.config_id, rule_id=division_rule.id,
    ).count() == (
        division_rule.number_of_subnets
        + division_rule.number_of_subnets * division_rule.number_of_ips
        + 1
    ):
        return

    master_subnet = division_rule.master_subnet
    generated_subnets = []
    generated_ips = []
    generated_indexes = []

    max_subnet = (
        # Get the highest subnet created for SubnetDivisionRule of this subnet.
        SubnetDivisionIndex.objects.filter(
            subnet__master_subnet=master_subnet, subnet__isnull=False, ip__isnull=True
        )
        .select_related('subnet')
        .order_by('-subnet__subnet')
        .first()
    )

    if max_subnet is None:
        # TODO: Clean this!!!
        required_subnet = next(
            IPNetwork(str(master_subnet.subnet)).subnet(prefixlen=division_rule.size)
        ).previous()
    else:
        required_subnet = IPNetwork(str(max_subnet.subnet.subnet))

    for subnet_id in range(1, division_rule.number_of_subnets + 1):
        required_subnet = required_subnet.next()
        subnet_obj = Subnet(
            name=f'{division_rule.label}_subnet{subnet_id}',
            subnet=str(required_subnet),
            description=_(f'Automatically generated using {division_rule.label} rule.'),
            master_subnet_id=division_rule.master_subnet_id,
            organization_id=instance.vpn.organization_id,
        )
        generated_subnets.append(subnet_obj)
        generated_indexes.append(
            SubnetDivisionIndex(
                keyword=f'{division_rule.label}_subnet{subnet_id}',
                subnet_id=subnet_obj.id,
                rule_id=division_rule.id,
                config_id=instance.config_id,
            )
        )

        for ip_id in range(1, division_rule.number_of_ips + 1):
            ip_obj = IpAddress(
                subnet_id=subnet_obj.id, ip_address=str(required_subnet[ip_id]),
            )
            generated_ips.append(ip_obj)

            generated_indexes.append(
                SubnetDivisionIndex(
                    keyword=f'{division_rule.label}_subnet{subnet_id}_ip{ip_id}',
                    subnet_id=subnet_obj.id,
                    ip_id=ip_obj.id,
                    rule_id=division_rule.id,
                    config_id=instance.config_id,
                )
            )
    Subnet.objects.bulk_create(generated_subnets)
    IpAddress.objects.bulk_create(generated_ips)
    SubnetDivisionIndex.objects.bulk_create(generated_indexes)


@receiver(post_delete, sender=VpnClient, dispatch_uid='vpn_client_provision_subnet')
def clear_subnets_ips(instance, **kwargs):
    # TODO: What to do when a device is deleted or VPN client template is removed from
    # a device?
    # Possible solution: Clean up generated subnets and IPs, but then we will create
    # patches of unallocated subnets
    pass
