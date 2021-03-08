from celery import shared_task
from django.utils.translation import ugettext_lazy as _
from swapper import load_model

Subnet = load_model('openwisp_ipam', 'Subnet')
IpAddress = load_model('openwisp_ipam', 'IpAddress')
SubnetDivisionIndex = load_model('subnet_division', 'SubnetDivisionIndex')


@shared_task
def create_subnet_ip_division_rule_index(
    required_subnet,
    required_subnet_id,
    required_ip,
    required_ip_id,
    organization_id,
    rule_id,
    rule_label,
    master_subnet_id,
):
    subnet = Subnet.objects.get_or_create(
        name=f'{rule_label}_subnet{required_subnet_id}',
        subnet=str(required_subnet),
        description=_(
            f'Automatically generated for {rule_label} Subnet Division Rule.'
        ),
        master_subnet_id=master_subnet_id,
        organization_id=organization_id,
    )[0]

    ip = IpAddress.objects.get_or_create(
        subnet_id=subnet.id,
        ip_address=required_ip,
        description=f'Automatically generated for {rule_label} Subnet Division Rule.',
    )[0]

    SubnetDivisionIndex.objects.create(
        subnet_id=subnet.id,
        ip_id=ip.id,
        rule_id=rule_id,
        keyword=f'{rule_label}_subnet{required_subnet_id}_ip{required_ip_id}',
    )
