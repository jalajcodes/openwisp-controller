from django.contrib import admin
from swapper import load_model

SubnetDivisionIndex = load_model('subnet_division', 'SubnetDivisionIndex')


class InputFilter(admin.SimpleListFilter):
    template = 'admin/input_filter.html'

    def lookups(self, request, model_admin):
        # Required to show the filter.
        return [tuple()]

    def choices(self, changelist):
        # Grab only the "all" option.
        all_choice = next(super().choices(changelist))
        all_choice['query_parts'] = (
            (k, v)
            for k, v in changelist.get_filters_params().items()
            if k != self.parameter_name
        )
        yield all_choice


class SubnetFilter(InputFilter):
    parameter_name = 'subnet'
    title = 'Subnet'

    def queryset(self, request, queryset):
        if self.value() is not None:
            subnet_text = self.value()
            return queryset.filter(
                config__subnetdivisionindex__subnet__subnet=subnet_text
            ).distinct()


class DeviceFilter(InputFilter):
    """
    Filters Subnet queryset for input device name
    using SubnetDivisionIndex
    """

    parameter_name = 'device'
    title = 'Device'

    def queryset(self, request, queryset):
        if self.value() is not None:
            device_text = self.value()

            return queryset.filter(
                id__in=SubnetDivisionIndex.objects.filter(
                    config__device__name=device_text
                ).values_list('subnet_id')
            )
