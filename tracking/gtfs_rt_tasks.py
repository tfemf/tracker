from django.core.files.base import ContentFile
from django.utils import timezone
import emf_bus_tracking.celery
from django.core.files.storage import default_storage
from celery import shared_task
from .gtfs_rt import gtfs_realtime_pb2
from . import models


@emf_bus_tracking.celery.app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(10.0, generate_gtfs_rt.s())


@shared_task(ignore_result=True)
def generate_gtfs_rt():
    now = timezone.now()

    output_message = gtfs_realtime_pb2.FeedMessage(
        header=gtfs_realtime_pb2.FeedHeader(
            gtfs_realtime_version="2.0",
            incrementality=gtfs_realtime_pb2.FeedHeader.FULL_DATASET,
            timestamp=int(now.timestamp()),
        )
    )

    add_alerts(output_message)
    add_vehicle_positions(output_message)

    default_storage.save('gtfs-rt.pb', ContentFile(output_message.SerializeToString()))


def add_alerts(msg: gtfs_realtime_pb2.FeedMessage):
    for alert in models.ServiceAlert.objects.all():
        msg.entity.append(gtfs_realtime_pb2.FeedEntity(
            id=str(alert.id),
            alert=gtfs_realtime_pb2.Alert(
                active_period=map(lambda p: gtfs_realtime_pb2.TimeRange(
                    start=int(p.start.timestamp()) if p.start else None,
                    end=int(p.end.timestamp()) if p.end else None,
                ), alert.periods.all()),
                informed_entity=map(lambda e: gtfs_realtime_pb2.EntitySelector(
                    route_id=str(e.route.id) if e.route else None,
                    trip=gtfs_realtime_pb2.TripDescriptor(
                        trip_id=str(e.journey.id)
                    ) if e.journey else None,
                    stop_id=str(e.stop.id) if e.stop else None,
                ), alert.selectors.all()),
                cause=alert.cause if alert.cause else gtfs_realtime_pb2.Alert.Cause.UNKNOWN_CAUSE,
                effect=alert.effect if alert.effect else gtfs_realtime_pb2.Alert.Effect.UNKNOWN_EFFECT,
                url=gtfs_realtime_pb2.TranslatedString(
                    translation=[gtfs_realtime_pb2.TranslatedString.Translation(
                        text=alert.url,
                    )]
                ) if alert.url else None,
                header_text=gtfs_realtime_pb2.TranslatedString(
                    translation=[gtfs_realtime_pb2.TranslatedString.Translation(
                        text=alert.header,
                    )]
                ) if alert.header else None,
                description_text=gtfs_realtime_pb2.TranslatedString(
                    translation=[gtfs_realtime_pb2.TranslatedString.Translation(
                        text=alert.description,
                    )]
                ) if alert.description else None,
                severity_level=alert.severity if alert.severity else
                gtfs_realtime_pb2.Alert.SeverityLevel.UNKNOWN_SEVERITY,
            )
        ))


def add_vehicle_positions(msg: gtfs_realtime_pb2.FeedMessage):
    cutoff = timezone.now() - timezone.timedelta(minutes=15)

    for vehicle in models.Vehicle.objects.all():
        last_position = vehicle.positions.order_by('-timestamp').first()
        if last_position and last_position.timestamp > cutoff:
            msg.entity.append(gtfs_realtime_pb2.FeedEntity(
                id=str(last_position.id),
                vehicle=gtfs_realtime_pb2.VehiclePosition(
                    vehicle=gtfs_realtime_pb2.VehicleDescriptor(
                        id=str(vehicle.id),
                        label=vehicle.name,
                        license_plate=vehicle.registration_plate,
                    ),
                    position=gtfs_realtime_pb2.Position(
                        latitude=last_position.latitude,
                        longitude=last_position.longitude,
                    ),
                    timestamp=int(last_position.timestamp.timestamp()),
                )
            ))
