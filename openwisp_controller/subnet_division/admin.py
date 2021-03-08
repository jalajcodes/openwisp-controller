from django.contrib import admin
from reversion.admin import VersionAdmin
from swapper import load_model

from openwisp_users.multitenancy import MultitenantAdminMixin, MultitenantOrgFilter
from openwisp_utils.admin import TimeReadonlyAdminMixin

SubnetDivisionRule = load_model('subnet_division', 'SubnetDivisionRule')


@admin.register(SubnetDivisionRule)
class SubnetDivisionRuleAdmin(
    VersionAdmin, MultitenantAdminMixin, TimeReadonlyAdminMixin, admin.ModelAdmin
):
    app_label = 'openwisp_ipam'
    list_display = [
        'label',
        'organization',
        'master_subnet',
        'created',
        'modified',
    ]
    list_filter = [('organization', MultitenantOrgFilter)]
    autocomplete_fields = ['master_subnet']
    search_fields = ['master_subnet', 'label']
    list_select_related = ['organization', 'master_subnet']
