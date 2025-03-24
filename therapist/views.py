from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum, Count, Q, Avg
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from decimal import Decimal
import datetime
import os
from User.permissions import IsTherapist
from .models import Location, Pictures, Services, BankDetails, Order, Earnings, Message, Conversation
from .serializers import (
    LocationSerializer, 
    PicturesSerializer, 
    ServicesSerializer, 
    BankDetailsSerializer,
    TherapistProfileSerializer,
    OrderSerializer, 
    OrderUpdateSerializer,
    MessageSerializer, 
    ConversationSerializer
)
from User.functions.image_handler import upload_image

@api_view(['GET', 'POST', 'PUT'])
@permission_classes([IsTherapist])
def location_view(request):
    if request.method == 'GET':
        try:
            location = Location.objects.get(user=request.user)
            serializer = LocationSerializer(location)
            return Response(serializer.data)
        except Location.DoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)

    elif request.method == 'POST':
        serializer = LocationSerializer(data=request.data)
        if serializer.is_valid():
            location, created = Location.objects.update_or_create(
                user=request.user,
                defaults=serializer.validated_data
            )
            return Response(LocationSerializer(location).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        try:
            location = Location.objects.get(user=request.user)
            serializer = LocationSerializer(location, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Location.DoesNotExist:
            return Response({"error": "Location not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsTherapist])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def pictures_view(request):
    if request.method == 'GET':
        try:
            pictures = Pictures.objects.get(user=request.user)
            serializer = PicturesSerializer(pictures)
            return Response(serializer.data)
        except Pictures.DoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        
    elif request.method == 'POST':
        uploaded_urls = {}

        if 'profile_picture' in request.FILES:
            file = request.FILES['profile_picture']
            file_path = os.path.join(settings.MEDIA_ROOT, file.name)
            with open(file_path, "wb+") as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            profile_pic_url = upload_image(file_path, "therapist/profile")
            if profile_pic_url:
                uploaded_urls['profile_picture'] = profile_pic_url

        if 'certificate' in request.FILES:
            file = request.FILES['certificate']
            file_path = os.path.join(settings.MEDIA_ROOT, file.name)
            with open(file_path, "wb+") as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            certificate_url = upload_image(file_path, "therapist/certificates")
            if certificate_url:
                uploaded_urls['certificate'] = certificate_url

        if 'national_id' in request.FILES:
            file = request.FILES['national_id']
            file_path = os.path.join(settings.MEDIA_ROOT, file.name)
            with open(file_path, "wb+") as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            national_id_url = upload_image(file_path, "therapist/documents")
            if national_id_url:
                uploaded_urls['national_id'] = national_id_url

        if 'more_pictures' in request.FILES:
            more_pictures = request.FILES.getlist('more_pictures')
            more_picture_urls = []

            for picture in more_pictures:
                file_path = os.path.join(settings.MEDIA_ROOT, picture.name)
                with open(file_path, "wb+") as destination:
                    for chunk in picture.chunks():
                        destination.write(chunk)
                pic_url = upload_image(file_path, "therapist/additional")
                if pic_url:
                    more_picture_urls.append(pic_url)

            if more_picture_urls:
                uploaded_urls['more_pictures'] = more_picture_urls

        try:
            pictures = Pictures.objects.get(user=request.user)
            
            if 'profile_picture' in uploaded_urls:
                pictures.profile_picture = uploaded_urls['profile_picture']
            
            if 'certificate' in uploaded_urls:
                pictures.certificate = uploaded_urls['certificate']
            
            if 'national_id' in uploaded_urls:
                pictures.national_id = uploaded_urls['national_id']
            
            if 'more_pictures' in uploaded_urls:
                current_count = len(pictures.more_pictures)
                new_count = len(uploaded_urls['more_pictures'])
                if current_count >= 6:
                    return Response(
                        {"error": "Max images can only be 6, delete any image to add new image"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                if current_count + new_count > 6:
                    return Response(
                        {"error": "Adding these images exceeds the maximum limit of 6, please delete some images first."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                pictures.more_pictures.extend(uploaded_urls['more_pictures'])
            
            pictures.save()

        except Pictures.DoesNotExist:
            required_fields = ['profile_picture', 'certificate', 'national_id']

            for field in required_fields:
                if field not in uploaded_urls and field not in request.data:
                    return Response({"error": f"Missing required field: {field}"}, status=status.HTTP_400_BAD_REQUEST)
            
            pictures_data = {'user': request.user, **uploaded_urls}
            
            for field in ['profile_picture', 'certificate', 'national_id']:
                if field not in uploaded_urls and field in request.data:
                    pictures_data[field] = request.data[field]
            
            if 'more_pictures' not in uploaded_urls and 'more_pictures' in request.data:
                if isinstance(request.data['more_pictures'], list):
                    pictures_data['more_pictures'] = request.data['more_pictures']
                else:
                    try:
                        import json
                        pictures_data['more_pictures'] = json.loads(request.data['more_pictures'])
                    except:
                        pictures_data['more_pictures'] = []
            
            pictures = Pictures.objects.create(**pictures_data)
        
        serializer = PicturesSerializer(pictures)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    elif request.method == 'DELETE':
        url_to_delete = request.data.get('url')
        if not url_to_delete:
            return Response({"error": "Image URL is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            pictures = Pictures.objects.get(user=request.user)
            if url_to_delete in pictures.more_pictures:
                pictures.more_pictures.remove(url_to_delete)
                pictures.save()
                return Response({"message": "Image deleted successfully", "more_pictures": pictures.more_pictures}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Image URL not found in more_pictures"}, status=status.HTTP_404_NOT_FOUND)
        except Pictures.DoesNotExist:
            return Response({"error": "Pictures not found"}, status=status.HTTP_404_NOT_FOUND)
        
@api_view(['GET', 'POST', 'PUT'])
@permission_classes([IsTherapist])
def services_view(request):
    if request.method == 'GET':
        try:
            services = Services.objects.get(user=request.user)
            serializer = ServicesSerializer(services)
            return Response(serializer.data)
        except Services.DoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
    
    elif request.method == 'POST':
        serializer = ServicesSerializer(data=request.data)
        if serializer.is_valid():
            services, created = Services.objects.update_or_create(
                user=request.user,
                defaults=serializer.validated_data
            )
            return Response(ServicesSerializer(services).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        try:
            services = Services.objects.get(user=request.user)
            serializer = ServicesSerializer(services, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Services.DoesNotExist:
            return Response({"error": "Services not found"}, status=status.HTTP_404_NOT_FOUND)
        
@api_view(['GET', 'POST', 'PUT'])
@permission_classes([IsTherapist])
def bank_details_view(request):
    if request.method == 'GET':
        try:
            bank_details = BankDetails.objects.get(user=request.user)
            serializer = BankDetailsSerializer(bank_details)
            return Response(serializer.data)
        except BankDetails.DoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
    
    elif request.method == 'POST':
        serializer = BankDetailsSerializer(data=request.data)
        if serializer.is_valid():
            bank_details, created = BankDetails.objects.update_or_create(
                user=request.user,
                defaults=serializer.validated_data
            )
            return Response(BankDetailsSerializer(bank_details).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        try:
            bank_details = BankDetails.objects.get(user=request.user)
            serializer = BankDetailsSerializer(bank_details, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except BankDetails.DoesNotExist:
            return Response({"error": "Bank details not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET', 'POST'])
@permission_classes([IsTherapist])
def therapist_profile_view(request):
    if request.method == 'GET':
        try:
            location = Location.objects.get(user=request.user)
            location_data = LocationSerializer(location).data
        except Location.DoesNotExist:
            location_data = {}
            
        try:
            pictures = Pictures.objects.get(user=request.user)
            pictures_data = PicturesSerializer(pictures).data
        except Pictures.DoesNotExist:
            pictures_data = {}
            
        try:
            services = Services.objects.get(user=request.user)
            services_data = ServicesSerializer(services).data
        except Services.DoesNotExist:
            services_data = {}
            
        try:
            bank_details = BankDetails.objects.get(user=request.user)
            bank_details_data = BankDetailsSerializer(bank_details).data
        except BankDetails.DoesNotExist:
            bank_details_data = {}
        
        profile_data = {
            'location': location_data,
            'pictures': pictures_data,
            'services': services_data,
            'bank_details': bank_details_data
        }
        
        return Response(profile_data)
    
    elif request.method == 'POST':
        serializer = TherapistProfileSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            result = serializer.save()
            return Response(result, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
@permission_classes([IsTherapist])
def incoming_orders_view(request):
    pending_orders = Order.objects.filter(therapist=request.user, status='pending')
    serializer = OrderSerializer(pending_orders, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsTherapist])
def order_detail_view(request, order_id):
    try:
        order = Order.objects.get(id=order_id, therapist=request.user)
        serializer = OrderSerializer(order)
        return Response(serializer.data)
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['PUT'])
@permission_classes([IsTherapist])
def update_order_view(request, order_id):
    try:
        order = Order.objects.get(id=order_id, therapist=request.user)
        serializer = OrderUpdateSerializer(order, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsTherapist])
def accept_order_view(request, order_id):
    try:
        order = Order.objects.get(id=order_id, therapist=request.user, status='pending')
        order.status = 'accepted'
        order.accepted_at = timezone.now()
        order.save()
        serializer = OrderSerializer(order)
        return Response(serializer.data)
    except Order.DoesNotExist:
        return Response({"error": "Order not found or already processed"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsTherapist])
def start_service_view(request, order_id):
    try:
        order = Order.objects.get(id=order_id, therapist=request.user, status='accepted')
        order.status = 'started'
        order.started_at = timezone.now()
        order.save()
        serializer = OrderSerializer(order)
        return Response(serializer.data)
    except Order.DoesNotExist:
        return Response({"error": "Order not found or not in accepted status"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsTherapist])
def complete_order_view(request, order_id):
    try:
        order = Order.objects.get(id=order_id, therapist=request.user, status='started')
        order.status = 'completed'
        order.completed_at = timezone.now()
        order.save()
        platform_fee_percentage = Decimal('0.20')
        platform_fee = order.price * platform_fee_percentage
        net_amount = order.price - platform_fee
        Earnings.objects.create(
            user=request.user,
            order=order,
            amount=order.price,
            platform_fee=platform_fee,
            net_amount=net_amount
        )
        serializer = OrderSerializer(order)
        return Response(serializer.data)
    except Order.DoesNotExist:
        return Response({"error": "Order not found or not in started status"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsTherapist])
def cancel_order_view(request, order_id):
    try:
        order = Order.objects.get(id=order_id, therapist=request.user, status__in=['pending', 'accepted'])
        order.status = 'cancelled'
        order.cancelled_at = timezone.now()
        order.save()
        serializer = OrderSerializer(order)
        return Response(serializer.data)
    except Order.DoesNotExist:
        return Response({"error": "Order not found or cannot be cancelled"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsTherapist])
def earnings_summary_view(request):
    period = request.query_params.get('period', 'week')
    earnings_query = Earnings.objects.filter(user=request.user)
    total_earnings = earnings_query.aggregate(total=Sum('net_amount'), orders=Count('id'))
    today = timezone.now().date()
    if period == 'day':
        start_date = today - datetime.timedelta(days=6)
        earnings_over_time = earnings_query.filter(created_at__date__gte=start_date).annotate(day=TruncDay('created_at')).values('day').annotate(amount=Sum('net_amount'), count=Count('id')).order_by('day')
    elif period == 'week':
        start_date = today - datetime.timedelta(weeks=3)
        earnings_over_time = earnings_query.filter(created_at__date__gte=start_date).annotate(week=TruncWeek('created_at')).values('week').annotate(amount=Sum('net_amount'), count=Count('id')).order_by('week')
    elif period == 'month':
        start_date = (today.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
        start_date = start_date.replace(day=1) - datetime.timedelta(days=150)
        earnings_over_time = earnings_query.filter(created_at__date__gte=start_date).annotate(month=TruncMonth('created_at')).values('month').annotate(amount=Sum('net_amount'), count=Count('id')).order_by('month')
    else:
        earnings_over_time = []
    recent_orders = Order.objects.filter(therapist=request.user, status='completed').order_by('-completed_at')[:5]
    recent_orders_data = OrderSerializer(recent_orders, many=True).data
    response_data = {
        'total_earnings': total_earnings.get('total') or 0,
        'total_orders': total_earnings.get('orders') or 0,
        'earnings_over_time': list(earnings_over_time),
        'recent_orders': recent_orders_data
    }
    return Response(response_data)

@api_view(['GET'])
@permission_classes([IsTherapist])
def conversations_view(request):
    conversations = Conversation.objects.filter(participants=request.user)
    serializer = ConversationSerializer(conversations, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsTherapist])
def conversation_detail_view(request, conversation_id):
    try:
        conversation = Conversation.objects.get(id=conversation_id, participants=request.user)
        Message.objects.filter(receiver=request.user, sender__in=conversation.participants.all().exclude(id=request.user.id), is_read=False).update(is_read=True)
        messages = Message.objects.filter(
            (Q(sender=request.user) & Q(receiver__in=conversation.participants.all().exclude(id=request.user.id))) |
            (Q(receiver=request.user) & Q(sender__in=conversation.participants.all().exclude(id=request.user.id)))
        ).order_by('created_at')
        messages_serializer = MessageSerializer(messages, many=True)
        conversation_serializer = ConversationSerializer(conversation, context={'request': request})
        return Response({'conversation': conversation_serializer.data, 'messages': messages_serializer.data})
    except Conversation.DoesNotExist:
        return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsTherapist])
def send_message_view(request, conversation_id):
    try:
        conversation = Conversation.objects.get(id=conversation_id, participants=request.user)
        recipient = conversation.participants.exclude(id=request.user.id).first()
        message = Message.objects.create(
            sender=request.user,
            receiver=recipient,
            content=request.data.get('content', '')
        )
        conversation.last_message = message
        conversation.save()
        serializer = MessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except Conversation.DoesNotExist:
        return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsTherapist])
def therapist_stats_view(request):
    orders = Order.objects.filter(therapist=request.user)
    total_orders = orders.count()
    completed_orders = orders.filter(status='completed').count()
    cancelled_orders = orders.filter(status='cancelled').count()
    rated_orders = orders.filter(status='completed', rating__isnull=False)
    avg_rating = rated_orders.aggregate(avg=Avg('rating'))['avg'] or 0
    response_rate = 0
    if orders.exclude(status='pending').count() > 0:
        response_rate = (orders.filter(status__in=['accepted', 'started', 'completed']).count() / orders.exclude(status='pending').count()) * 100
    completion_rate = 0
    if orders.filter(status__in=['completed', 'cancelled']).count() > 0:
        completion_rate = (orders.filter(status='completed').count() / orders.filter(status__in=['completed', 'cancelled']).count()) * 100
    response_data = {
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,
        'avg_rating': round(avg_rating, 1),
        'response_rate': round(response_rate, 1),
        'completion_rate': round(completion_rate, 1)
    }
    return Response(response_data)