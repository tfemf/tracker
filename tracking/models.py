from django.core.exceptions import ValidationError
from django.db import models
from colorfield.fields import ColorField
from .gtfs_rt import gtfs_realtime_pb2
import uuid


class Stop(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, unique=True, default=uuid.uuid4)
    code = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    internal = models.BooleanField(default=False, blank=True)
    url = models.URLField(blank=True, null=True, verbose_name="URL")

    def __str__(self):
        if self.code:
            return f"{self.code} - {self.name}"

        return self.name

    def save(self, *args, **kwargs):
        from . import gtfs_tasks
        super().save(*args, **kwargs)
        gtfs_tasks.generate_gtfs_schedule.delay()


class Route(models.Model):
    TYPE_TRAM = 0
    TYPE_SUBWAY = 1
    TYPE_RAIL = 2
    TYPE_BUS = 3
    TYPE_FERRY = 4
    TYPE_CABLE_TRAM = 5
    TYPE_AERIAL_LIFT = 6
    TYPE_FUNICULAR = 7
    TYPE_TROLLEYBUS = 11
    TYPE_MONORAIL = 12

    TYPES = (
        (TYPE_TRAM, "Tram, Streetcar, Light rail"),
        (TYPE_SUBWAY, "Subway, Metro"),
        (TYPE_RAIL, "Rail"),
        (TYPE_BUS, "Bus"),
        (TYPE_FERRY, "Ferry"),
        (TYPE_CABLE_TRAM, "Cable tram"),
        (TYPE_AERIAL_LIFT, "Aerial lift"),
        (TYPE_FUNICULAR, "Funicular"),
        (TYPE_TROLLEYBUS, "Trolleybus"),
        (TYPE_MONORAIL, "Monorail"),
    )

    id = models.UUIDField(primary_key=True, editable=False, unique=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    type = models.PositiveSmallIntegerField(choices=TYPES)
    url = models.URLField(blank=True, null=True, verbose_name="URL")
    color = ColorField(blank=True, null=True)
    text_color = ColorField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0, blank=True, null=False)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order']

    def save(self, *args, **kwargs):
        from . import gtfs_tasks
        super().save(*args, **kwargs)
        gtfs_tasks.generate_gtfs_schedule.delay()


class Vehicle(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, unique=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    registration_plate = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} ({self.registration_plate})"


class VehiclePosition(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, unique=True, default=uuid.uuid4)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="positions")
    timestamp = models.DateTimeField()
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return f"{self.vehicle} - {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']


class Journey(models.Model):
    DIRECTION_INBOUND = 0
    DIRECTION_OUTBOUND = 1

    DIRECTIONS = (
        (DIRECTION_INBOUND, "Inbound"),
        (DIRECTION_OUTBOUND, "Outbound"),
    )

    id = models.UUIDField(primary_key=True, editable=False, unique=True, default=uuid.uuid4)
    code = models.CharField(max_length=255)
    route = models.ForeignKey(Route, on_delete=models.SET_NULL, blank=True, null=True)
    direction = models.PositiveSmallIntegerField(choices=DIRECTIONS, blank=True, null=True)
    date = models.DateField()
    public = models.BooleanField(default=True, blank=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, blank=True, null=True)
    forms_from = models.OneToOneField(
        "Journey", on_delete=models.SET_NULL, blank=True, null=True, related_name="forms_to"
    )
    shape = models.ForeignKey("Shape", on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        if self.route:
            return f"{self.code} ({self.route}) - {self.date} - {self.get_direction_display()}"

        return f"{self.code} - {self.date}"

    class Meta:
        ordering = ['date', 'code']
        unique_together = ['code', 'date']

    def save(self, *args, **kwargs):
        from . import gtfs_tasks
        super().save(*args, **kwargs)
        gtfs_tasks.generate_gtfs_schedule.delay()


class JourneyPoint(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, unique=True, default=uuid.uuid4)
    journey = models.ForeignKey(Journey, on_delete=models.CASCADE, related_name="points")
    stop = models.ForeignKey(Stop, on_delete=models.CASCADE)
    arrival_time = models.TimeField(blank=True, null=True)
    departure_time = models.TimeField(blank=True, null=True)
    timing_point = models.BooleanField(default=True, blank=True)
    order = models.PositiveIntegerField(default=0, blank=True, null=False)

    def __str__(self):
        return f"{self.journey.code} - {self.stop}: arr {self.arrival_time} dep {self.departure_time}"

    class Meta:
        ordering = ['order']

    def validate_constraints(self, exclude=None):
        if not self.arrival_time and not self.departure_time:
            raise ValidationError("Arrival time or departure time must be set")


class Shape(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, unique=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        from . import gtfs_tasks
        super().save(*args, **kwargs)
        gtfs_tasks.generate_gtfs_schedule.delay()

    def __str__(self):
        return self.name


class ShapePoint(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, unique=True, default=uuid.uuid4)
    shape = models.ForeignKey(Shape, on_delete=models.CASCADE, related_name="points")
    latitude = models.FloatField()
    longitude = models.FloatField()
    order = models.PositiveIntegerField(default=0, blank=True, null=False)

    class Meta:
        ordering = ['order']


class ServiceAlert(models.Model):
    CAUSES = (
        (gtfs_realtime_pb2.Alert.Cause.OTHER_CAUSE, "Other cause"),
        (gtfs_realtime_pb2.Alert.Cause.TECHNICAL_PROBLEM, "Technical problem"),
        (gtfs_realtime_pb2.Alert.Cause.STRIKE, "Strike"),
        (gtfs_realtime_pb2.Alert.Cause.DEMONSTRATION, "Demonstration"),
        (gtfs_realtime_pb2.Alert.Cause.ACCIDENT, "Accident"),
        (gtfs_realtime_pb2.Alert.Cause.HOLIDAY, "Holiday"),
        (gtfs_realtime_pb2.Alert.Cause.WEATHER, "Weather"),
        (gtfs_realtime_pb2.Alert.Cause.MAINTENANCE, "Maintenance"),
        (gtfs_realtime_pb2.Alert.Cause.CONSTRUCTION, "Construction"),
        (gtfs_realtime_pb2.Alert.Cause.POLICE_ACTIVITY, "Police activity"),
        (gtfs_realtime_pb2.Alert.Cause.MEDICAL_EMERGENCY, "Medical emergency"),
    )

    EFFECTS = (
        (gtfs_realtime_pb2.Alert.Effect.NO_SERVICE, "No service"),
        (gtfs_realtime_pb2.Alert.Effect.REDUCED_SERVICE, "Reduced service"),
        (gtfs_realtime_pb2.Alert.Effect.SIGNIFICANT_DELAYS, "Significant delays"),
        (gtfs_realtime_pb2.Alert.Effect.DETOUR, "Detour"),
        (gtfs_realtime_pb2.Alert.Effect.ADDITIONAL_SERVICE, "Additional service"),
        (gtfs_realtime_pb2.Alert.Effect.MODIFIED_SERVICE, "Modified service"),
        (gtfs_realtime_pb2.Alert.Effect.OTHER_EFFECT, "Other effect"),
        (gtfs_realtime_pb2.Alert.Effect.STOP_MOVED, "Stop moved"),
        (gtfs_realtime_pb2.Alert.Effect.NO_EFFECT, "No effect"),
        (gtfs_realtime_pb2.Alert.Effect.ACCESSIBILITY_ISSUE, "Accessibility issue"),
    )

    SEVERITIES = (
        (gtfs_realtime_pb2.Alert.SeverityLevel.INFO, "Info"),
        (gtfs_realtime_pb2.Alert.SeverityLevel.WARNING, "Warning"),
        (gtfs_realtime_pb2.Alert.SeverityLevel.SEVERE, "Severe"),
    )

    id = models.UUIDField(primary_key=True, editable=False, unique=True, default=uuid.uuid4)
    header = models.CharField(max_length=255)
    description = models.TextField()
    url = models.URLField(blank=True, null=True, verbose_name="URL")
    severity = models.PositiveSmallIntegerField(choices=SEVERITIES, blank=True, null=True)
    cause = models.PositiveSmallIntegerField(choices=CAUSES, blank=True, null=True)
    effect = models.PositiveSmallIntegerField(choices=EFFECTS, blank=True, null=True)

    def __str__(self):
        return self.header


class ServiceAlertPeriod(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, unique=True, default=uuid.uuid4)
    service_alert = models.ForeignKey(ServiceAlert, on_delete=models.CASCADE, related_name="periods")
    start = models.DateTimeField(blank=True, null=True)
    end = models.DateTimeField(blank=True, null=True)


class ServiceAlertSelector(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, unique=True, default=uuid.uuid4)
    service_alert = models.ForeignKey(ServiceAlert, on_delete=models.CASCADE, related_name="selectors")
    route = models.ForeignKey(Route, on_delete=models.CASCADE, blank=True, null=True)
    journey = models.ForeignKey(Journey, on_delete=models.CASCADE, blank=True, null=True)
    stop = models.ForeignKey(Stop, on_delete=models.CASCADE, blank=True, null=True)
