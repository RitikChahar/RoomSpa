from kafka import KafkaConsumer
import json
from .models import Location
from django.contrib.auth import get_user_model
import math
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    from math import radians, sin, cos, atan2, sqrt
    phi1 = radians(lat1)
    phi2 = radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi/2)**2 + cos(phi1)*cos(phi2)*sin(dlambda/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def consume_service_requests():
    consumer = KafkaConsumer('service_requests', bootstrap_servers='localhost:9092', value_deserializer=lambda m: json.loads(m.decode('utf-8')))
    channel_layer = get_channel_layer()
    User = get_user_model()
    for msg in consumer:
        data = msg.value
        lat = data.get('latitude')
        lon = data.get('longitude')
        customer_id = data.get('customer_id')
        booking_id = data.get('booking_id')
        therapists = Location.objects.filter(latitude__isnull=False, longitude__isnull=False)
        for therapist in therapists:
            distance = haversine(float(lat), float(lon), float(therapist.latitude), float(therapist.longitude))
            if distance <= float(therapist.service_radius):
                async_to_sync(channel_layer.group_send)('therapist_%s' % therapist.user.id, {'type': 'service_request', 'data': data})