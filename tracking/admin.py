import xml.etree.ElementTree

from django.contrib import admin
from adminsortable2.admin import SortableAdminMixin, SortableInlineAdminMixin, SortableAdminBase
from django.core.checks import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path
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
    change_list_template = "tracking/shape_changelist.html"

    inlines = [ShapePointAdmin]

    def get_urls(self):
        urls = super().get_urls()
        urls = [
            path("import_shape/", self.admin_site.admin_view(self.import_shape), name="tracking_shape_import"),
        ] + urls
        return urls

    def import_shape(self, request):
        if request.method == "POST":
            try:
                self.handle_import(request)
            except ValidationError as e:
                self.message_user(request, e.message, level=messages.ERROR)
            else:
                return redirect("admin:tracking_shape_changelist")

        context = dict(
            self.admin_site.each_context(request),
        )
        return TemplateResponse(request, "tracking/shape_import.html", context)

    def handle_import(self, request):
        if not request.FILES.get("kml_file"):
            raise ValidationError("No file uploaded")

        file = request.FILES["kml_file"]
        try:
            d = xml.etree.ElementTree.fromstring(file.read())
        except xml.etree.ElementTree.ParseError:
            raise ValidationError("Invalid XML")

        namespaces = {
            "kml": "http://www.opengis.net/kml/2.2"
        }

        placemarks = d.findall("kml:Document/kml:Placemark", namespaces=namespaces)
        if not placemarks:
            raise ValidationError("No Placemarks found")

        name = None
        line_string = None
        for placemark in placemarks:
            name = placemark.find("kml:name", namespaces=namespaces)
            line_string = placemark.find("kml:LineString", namespaces=namespaces)
            if line_string is not None:
                break

        if line_string is None:
            raise ValidationError("No LineString found")

        coordinates = line_string.find("kml:coordinates", namespaces=namespaces)
        coordinates = coordinates.text.strip().split("\n")

        if not coordinates:
            raise ValidationError("No coordinates found")

        with transaction.atomic():
            shape = models.Shape.objects.create(name=name.text.strip() if name is not None else "Unnamed")
            for i, coordinate in enumerate(coordinates):
                parts = coordinate.split(',')
                if len(parts) != 3:
                    raise ValidationError("Invalid coordinate")
                lat, long, _ = parts
                lat = float(lat)
                long = float(long)
                models.ShapePoint.objects.create(
                    shape=shape,
                    latitude=lat,
                    longitude=long,
                    order=i,
                )


class ServiceAlertPeriodAdmin(admin.TabularInline):
    model = models.ServiceAlertPeriod


class ServiceAlertSelectorAdmin(admin.TabularInline):
    model = models.ServiceAlertSelector


@admin.register(models.ServiceAlert)
class ServiceAlertAdmin(admin.ModelAdmin):
    inlines = [ServiceAlertPeriodAdmin, ServiceAlertSelectorAdmin]
