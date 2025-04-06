import math
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.conf import settings
from django.shortcuts import get_object_or_404
from therapist.models import Location, Services as TherapistServices
from django.contrib.auth import get_user_model
from User.permissions import IsCustomer
from .models import CustomerAddress, Booking, Transaction
from chat.models import Conversation, Message
from .serializers import CustomerAddressSerializer, BookingSerializer, TherapistDetailSerializer, CustomerProfileSerializer, TransactionSerializer
from chat.serializers import ConversationSerializer, MessageSerializer

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
        serializer.save(customer=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsCustomer])
def therapist_detail_view(request, therapist_id):
    User = get_user_model()
    therapist = get_object_or_404(User, id=therapist_id)
    loc = Location.objects.filter(user=therapist).first()
    serv_obj = TherapistServices.objects.filter(user=therapist).first()
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
    if not lat or not lon or not services_param:
        return Response({'error': 'Missing parameters'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user_lat = float(lat)
        user_lon = float(lon)
    except ValueError:
        return Response({'error': 'Invalid coordinates'}, status=status.HTTP_400_BAD_REQUEST)
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
    query = Q()
    for s in service_list:
        query |= Q(services__icontains=s)
    qs = qs.filter(query)
    therapist_ids = qs.values_list('user_id', flat=True)
    locations = Location.objects.filter(user_id__in=therapist_ids)
    results = []
    for loc in locations:
        if loc.latitude is None or loc.longitude is None:
            continue
        distance = haversine(user_lat, user_lon, float(loc.latitude), float(loc.longitude))
        if distance <= float(loc.service_radius):
            therapist = loc.user
            serv_obj = TherapistServices.objects.filter(user=therapist).first()
            data = {
                'id': therapist.id,
                'name': therapist.get_full_name() or therapist.username,
                'email': therapist.email,
                'address': loc.address,
                'distance': round(distance, 2),
                'services': serv_obj.services if serv_obj else []
            }
            results.append(data)
    serializer = TherapistDetailSerializer(results, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsCustomer])
def customer_conversations_view(request):
    convs = Conversation.objects.filter(participants=request.user)
    serializer = ConversationSerializer(convs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsCustomer])
def customer_conversation_detail(request, conversation_id):
    conv = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    msgs = Message.objects.filter(conversation=conv).order_by('created_at')
    return Response(MessageSerializer(msgs, many=True).data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsCustomer])
def send_customer_message(request, conversation_id):
    conv = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    receiver_id = request.data.get('receiver_id')
    content = request.data.get('content', '')
    User = get_user_model()
    receiver = get_object_or_404(User, id=receiver_id)
    msg = Message.objects.create(conversation=conv, sender=request.user, receiver=receiver, content=content)
    conv.last_message = msg
    conv.save()
    return Response(MessageSerializer(msg).data, status=status.HTTP_201_CREATED)