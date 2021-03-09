from django.test import TestCase
from openwisp_ipam.tests import CreateModelsMixin as SubnetIpamMixin
from swapper import load_model

from ...config.tests.utils import CreateConfigTemplateMixin, TestVpnX509Mixin
from .helpers import SubnetDivisionTestMixin

Subnet = load_model('openwisp_ipam', 'Subnet')
IpAddress = load_model('openwisp_ipam', 'IpAddress')
SubnetDivisionRule = load_model('subnet_division', 'SubnetDivisionRule')
SubnetDivisionIndex = load_model('subnet_division', 'SubnetDivisionIndex')


class TestSubnetDivisionRule(
    SubnetIpamMixin,
    SubnetDivisionTestMixin,
    TestVpnX509Mixin,
    CreateConfigTemplateMixin,
    TestCase,
):
    def test_provisioned_subnets(self):
        org = self._get_org()
        master_subnet = self._get_master_subnet()
        rule = self._get_vpn_subdivision_rule()
        vpn_server = self._create_vpn(subnet=master_subnet, organization=org)
        template = self._create_template(
            name='vpn-test', type='vpn', vpn=vpn_server, organization=org
        )
        config = self._create_config(organization=org)

        self.assertEqual(Subnet.objects.filter(organization=org).count(), 1)
        self.assertEqual(IpAddress.objects.count(), 1)

        config.templates.add(template)

        self.assertEqual(
            Subnet.objects.filter(
                organization=org, master_subnet=master_subnet
            ).count(),
            rule.number_of_subnets,
        )
        self.assertEqual(
            IpAddress.objects.count(), 1 + (rule.number_of_subnets * rule.number_of_ips)
        )

        # Verify context of config
        context = config.get_subnet_division_context()
        self.assertIn(f'{rule.label}_prefixlen', context)
        for subnet_id in range(1, rule.number_of_subnets + 1):
            self.assertIn(f'{rule.label}_subnet{subnet_id}', context)
            for ip_id in range(1, rule.number_of_ips + 1):
                self.assertIn(f'{rule.label}_subnet{subnet_id}_ip{ip_id}', context)


class TestSubnetDivsionIndex(SubnetIpamMixin, SubnetDivisionTestMixin, TestCase):
    def test_prefixlen_index_created(self):
        # Test entry for prefixlen is created
        # when a SubnetDivisionRule is created

        self.assertEqual(SubnetDivisionIndex.objects.count(), 0)
        rule = self._get_vpn_subdivision_rule()
        self.assertEqual(SubnetDivisionIndex.objects.count(), 1)
        index = SubnetDivisionIndex.objects.get(rule=rule)
        self.assertEqual(index.keyword, f'{rule.label}_prefixlen')
