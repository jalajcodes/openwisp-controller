from django.contrib import admin
from django.urls import reverse
from django.utils.html import mark_safe
from openwisp_ipam.admin import SubnetAdmin
from reversion.admin import VersionAdmin
from swapper import load_model

from openwisp_controller.config.admin import DeviceAdmin
from openwisp_users.multitenancy import MultitenantAdminMixin
from openwisp_utils.admin import TimeReadonlyAdminMixin

from .filters import DeviceFilter, SubnetFilter

SubnetDivisionRule = load_model('subnet_division', 'SubnetDivisionRule')
SubnetDivisionIndex = load_model('subnet_division', 'SubnetDivisionIndex')
Subnet = load_model('openwisp_ipam', 'Subnet')


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
    autocomplete_fields = ['master_subnet']
    search_fields = ['master_subnet', 'label']
    list_select_related = ['organization', 'master_subnet']


# Monkey patching DeviceAdmin to allow filtering using subnet
DeviceAdmin.list_filter.append(SubnetFilter)

# NOTE: Monkey patching SubnetAdmin didn't work for adding readonly_field
# to change_view because of TimeReadonlyAdminMixin.

admin.site.unregister(Subnet)


@admin.register(Subnet)
class ModifiedSubnetAdmin(SubnetAdmin):
    readonly_fields = SubnetAdmin.readonly_fields + ('related_device',)
    list_display = SubnetAdmin.list_display + ['related_device']
    list_filter = SubnetAdmin.list_filter + [DeviceFilter]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        subnet_division_index_qs = (
            SubnetDivisionIndex.objects.filter(
                subnet_id__in=qs.filter(master_subnet__isnull=False).values('id'),
                ip__isnull=True,
            )
            .select_related('config__device')
            .values_list('subnet_id', 'config__device__name')
        )
        self._lookup = {}
        for subnet_id, device_name in subnet_division_index_qs:
            self._lookup[subnet_id] = device_name
        return qs

    def related_device(self, obj):
        url = reverse('admin:config_device_changelist')
        if obj.master_subnet is None:
            return None
        else:
            device = self._lookup[obj.id]
            return mark_safe(f'<a href="{url}?subnet={str(obj.subnet)}">{device}</a>')
