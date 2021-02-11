from django.test import TestCase

from openwisp_utils.admin_theme.dashboard import DASHBOARD_CHARTS


class TestCustomAdminDashboard(TestCase):
    def test_config_status_chart_registered(self):
        expected_config = {
            'name': 'Configuration Status',
            'query_params': {
                'app_label': 'config',
                'model': 'device',
                'group_by': 'config__status',
            },
            'colors': {'applied': '#267126', 'modified': '#ffb442', 'error': '#a72d1d'},
            'labels': {'applied': 'applied', 'error': 'error', 'modified': 'modified'},
        }
        chart_config = DASHBOARD_CHARTS.get(1, None)
        self.assertIsNotNone(chart_config)
        self.assertDictEqual(chart_config, expected_config)

    def test_geo_chart_registered(self):
        chart_config = DASHBOARD_CHARTS.get(2, None)
        self.assertIsNotNone(chart_config)
        self.assertIn('labels', chart_config)
        query_params = chart_config['query_params']
        self.assertIn('annotate', query_params)
        self.assertIn('aggregate', query_params)
        self.assertIn('filters', chart_config)
        filters = chart_config['filters']
        self.assertIn('key', filters)
        self.assertIn('with_geo__sum', chart_config['filters'])
        self.assertIn('without_geo__sum', chart_config['filters'])
