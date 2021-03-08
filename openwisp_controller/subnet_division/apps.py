from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class SubnetDivisionConfig(AppConfig):
    name = 'openwisp_controller.subnet_division'
    verbose_name = _('Subnet Division')

    def ready(self):
        super().ready()
        from . import handlers  # noqa
