from swapper import load_model

SubnetDivisionRule = load_model('subnet_division', 'SubnetDivisionRule')
SubnetDivisionIndex = load_model('subnet_division', 'SubnetDivisionIndex')
Subnet = load_model('openwisp_ipam', 'Subnet')


class SubnetDivisionTestMixin:
    def _create_subnet_division_rule(self, **kwargs):
        options = dict()
        options.update(self._get_extra_fields(**kwargs))
        options.update(kwargs)
        instance = SubnetDivisionRule(**options)
        instance.full_clean()
        instance.save()
        return instance

    def _get_subnet_division_rule(self, type):
        return self._create_subnet_division_rule(
            label='OW',
            size=28,
            master_subnet=self._get_master_subnet(),
            number_of_ips=2,
            number_of_subnets=2,
            type=type,
        )

    def _get_vpn_subdivision_rule(self):
        return self._get_subnet_division_rule(type='vpn')

    def _get_master_subnet(self, subnet='10.0.0.0/16'):
        try:
            return Subnet.objects.get(subnet='10.0.0.0/16')
        except Subnet.DoesNotExist:
            return self._create_subnet(subnet=subnet)
