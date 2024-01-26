from django.contrib import admin
from adminsortable2.admin import SortableAdminMixin, SortableInlineAdminMixin, SortableAdminBase
from . import models


@admin.register(models.Stop)
class StopAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Route)
class RouteAdmin(SortableAdminMixin, admin.ModelAdmin):
    pass


class JourneyPointAdmin(SortableInlineAdminMixin, admin.TabularInline):
    model = models.JourneyPoint


@admin.register(models.Journey)
class JourneyAdmin(SortableAdminBase, admin.ModelAdmin):
    inlines = [JourneyPointAdmin]


class ShapePointAdmin(SortableInlineAdminMixin, admin.TabularInline):
    model = models.ShapePoint


@admin.register(models.Shape)
class ShapeAdmin(SortableAdminBase, admin.ModelAdmin):
    inlines = [ShapePointAdmin]


class ServiceAlertPeriodAdmin(admin.TabularInline):
    model = models.ServiceAlertPeriod


class ServiceAlertSelectorAdmin(admin.TabularInline):
    model = models.ServiceAlertSelector


@admin.register(models.ServiceAlert)
class ServiceAlertAdmin(admin.ModelAdmin):
    inlines = [ServiceAlertPeriodAdmin, ServiceAlertSelectorAdmin]
