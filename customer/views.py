import math
import json
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from kafka import KafkaProducer
from User.permissions import IsCustomer
from .models import CustomerAddress, Booking, Transaction
from chat.models import Conversation, Message
from .serializers import CustomerAddressSerializer, BookingSerializer, TherapistDetailSerializer, CustomerProfileSerializer, TransactionSerializer
from chat.serializers import ConversationSerializer, MessageSerializer
from therapist.models import Services as TherapistServices, Location

@api_view(['GET', 'POST', 'PUT'])
@permission_classes([IsCustomer])
def customer_address_view(request):
    addr = CustomerAddress.objects.filter(customer=request.user).first()
    if request.method == 'GET':
        if addr:
            return Response(CustomerAddressSerializer(addr).data, status=status.HTTP_200_OK)
        return Response({}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'POST':
        serializer = CustomerAddressSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(customer=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    if request.method == 'PUT':
        if not addr:
            return Response({'error': 'Address not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CustomerAddressSerializer(addr, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsCustomer])
def book_therapist(request):
    serializer = BookingSerializer(data=request.data)
    if serializer.is_valid():
        booking = serializer.save(customer=request.user)
        producer = KafkaProducer(bootstrap_servers='localhost:9092', value_serializer=lambda v: json.dumps(v).encode('utf-8'))
        data = {'booking_id': str(booking.id), 'customer_id': request.user.id, 'latitude': booking.latitude, 'longitude': booking.longitude, 'services': booking.services}
        producer.send('service_requests', data)
        producer.flush()
        return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsCustomer])
def therapist_detail_view(request, therapist_id):
    User = get_user_model()
    therapist = get_object_or_404(User, id=therapist_id)
    loc = None
    serv_obj = None
    data = {
        'id': therapist.id,
        'name': therapist.get_full_name() or therapist.username,
        'email': therapist.email,
        'address': loc.address if loc else '',
        'services': serv_obj.services if serv_obj else []
    }
    serializer = TherapistDetailSerializer(data)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsCustomer])
def cancel_booking_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, customer=request.user)
    booking.status = 'cancelled'
    booking.cancellation_reason = request.data.get('reason', '')
    booking.save()
    return Response(BookingSerializer(booking).data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsCustomer])
def customer_profile_view(request):
    user = request.user
    bookings = Booking.objects.filter(customer=user)
    transactions = Transaction.objects.filter(booking__customer=user)
    data = {
        'id': user.id,
        'name': user.get_full_name() or user.username,
        'email': user.email,
        'bookings': BookingSerializer(bookings, many=True).data,
        'transactions': TransactionSerializer(transactions, many=True).data
    }
    serializer = CustomerProfileSerializer(data)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsCustomer])
def search_therapists_view(request):
    lat = request.query_params.get('latitude')
    lon = request.query_params.get('longitude')
    services_param = request.query_params.get('services')
    radius = request.query_params.get('radius', '10') 
    
    if not lat or not lon or not services_param:
        return Response({'error': 'Missing parameters'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user_lat = float(lat)
        user_lon = float(lon)
        search_radius = float(radius)
    except ValueError:
        return Response({'error': 'Invalid coordinates or radius'}, status=status.HTTP_400_BAD_REQUEST)
    
    service_list = [s.strip() for s in services_param.split(',') if s.strip()]
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371 
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
    
    qs = TherapistServices.objects.all()
    query = Q(services__icontains=service_list[0]) if service_list else None
    for s in service_list[1:]:
        query |= Q(services__icontains=s)
    if query:
        qs = qs.filter(query)
    
    therapist_ids = qs.values_list('user_id', flat=True)
    locations = Location.objects.filter(user_id__in=therapist_ids)
    results = []
    
    for loc in locations:
        if loc.latitude is None or loc.longitude is None:
            continue
        
        distance = haversine(user_lat, user_lon, float(loc.latitude), float(loc.longitude))
        
        if distance <= search_radius and distance <= float(loc.service_radius):
            therapist = loc.user
            serv_obj = TherapistServices.objects.filter(user=therapist).first()
            data = {
                'id': therapist.id,
                'name': therapist.name, 
                'email': therapist.email,
                'address': loc.address,
                'distance': round(distance, 2),
                'services': serv_obj.services if serv_obj else []
            }
            results.append(data)
    
    serializer = TherapistDetailSerializer(results, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)