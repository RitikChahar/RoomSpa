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
from django.shortcuts import get_object_or_404
from User.permissions import IsTherapist, IsCustomer
from .models import Location, Pictures, Services, BankDetails, Order, Earnings, TherapistReview
from chat.models import Conversation, Message
from .serializers import LocationSerializer, PicturesSerializer, ServicesSerializer, BankDetailsSerializer, TherapistProfileSerializer, OrderSerializer, OrderUpdateSerializer, TherapistReviewSerializer, TherapistReviewSummarySerializer
from chat.serializers import ConversationSerializer, MessageSerializer
from User.functions.image_handler import upload_image

def handle_uploaded_file(file, subfolder):
    file_path = os.path.join(settings.MEDIA_ROOT, file.name)
    with open(file_path, "wb+") as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    return upload_image(file_path, f"therapist/{subfolder}")

@api_view(['GET', 'POST', 'PUT'])
@permission_classes([IsTherapist])
def location_view(request):
    if request.method == 'GET':
        location = get_object_or_404(Location, user=request.user)
        serializer = LocationSerializer(location)
        return Response(serializer.data)
    if request.method in ['POST', 'PUT']:
        instance = Location.objects.filter(user=request.user).first()
        serializer = LocationSerializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED if not instance else status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsTherapist])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def pictures_view(request):
    if request.method == 'GET':
        pictures = get_object_or_404(Pictures, user=request.user)
        serializer = PicturesSerializer(pictures)
        return Response(serializer.data)
    if request.method == 'POST':
        uploaded = {}
        if 'profile_picture' in request.FILES:
            url = handle_uploaded_file(request.FILES['profile_picture'], "profile")
            if url:
                uploaded['profile_picture'] = url
        if 'certificate' in request.FILES:
            url = handle_uploaded_file(request.FILES['certificate'], "certificates")
            if url:
                uploaded['certificate'] = url
        if 'national_id' in request.FILES:
            url = handle_uploaded_file(request.FILES['national_id'], "documents")
            if url:
                uploaded['national_id'] = url
        if 'more_pictures' in request.FILES:
            more_urls = []
            for pic in request.FILES.getlist('more_pictures'):
                url = handle_uploaded_file(pic, "additional")
                if url:
                    more_urls.append(url)
            if more_urls:
                uploaded['more_pictures'] = more_urls
        pictures = Pictures.objects.filter(user=request.user).first()
        if pictures:
            if 'profile_picture' in uploaded:
                pictures.profile_picture = uploaded['profile_picture']
            if 'certificate' in uploaded:
                pictures.certificate = uploaded['certificate']
            if 'national_id' in uploaded:
                pictures.national_id = uploaded['national_id']
            if 'more_pictures' in uploaded:
                if len(pictures.more_pictures) >= 6 or len(pictures.more_pictures) + len(uploaded['more_pictures']) > 6:
                    return Response({"error": "Exceeded maximum limit of 6 images"}, status=status.HTTP_400_BAD_REQUEST)
                pictures.more_pictures.extend(uploaded['more_pictures'])
            pictures.save()
        else:
            required = ['profile_picture', 'certificate', 'national_id']
            for field in required:
                if field not in uploaded and field not in request.data:
                    return Response({"error": f"Missing required field: {field}"}, status=status.HTTP_400_BAD_REQUEST)
            data = {'user': request.user, **uploaded}
            for field in required:
                if field not in uploaded and field in request.data:
                    data[field] = request.data[field]
            if 'more_pictures' not in uploaded and 'more_pictures' in request.data:
                data['more_pictures'] = request.data['more_pictures'] if isinstance(request.data['more_pictures'], list) else []
            pictures = Pictures.objects.create(**data)
        serializer = PicturesSerializer(pictures)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    if request.method == 'DELETE':
        url = request.data.get('url')
        if not url:
            return Response({"error": "Image URL is required"}, status=status.HTTP_400_BAD_REQUEST)
        pictures = get_object_or_404(Pictures, user=request.user)
        if url in pictures.more_pictures:
            pictures.more_pictures.remove(url)
            pictures.save()
            return Response({"message": "Image deleted", "more_pictures": pictures.more_pictures})
        return Response({"error": "Image URL not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET', 'POST', 'PUT'])
@permission_classes([IsTherapist])
def services_view(request):
    if request.method == 'GET':
        services = get_object_or_404(Services, user=request.user)
        serializer = ServicesSerializer(services)
        return Response(serializer.data)
    if request.method in ['POST', 'PUT']:
        instance = Services.objects.filter(user=request.user).first()
        serializer = ServicesSerializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED if not instance else status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST', 'PUT'])
@permission_classes([IsTherapist])
def bank_details_view(request):
    if request.method == 'GET':
        details = get_object_or_404(BankDetails, user=request.user)
        serializer = BankDetailsSerializer(details)
        return Response(serializer.data)
    if request.method in ['POST', 'PUT']:
        instance = BankDetails.objects.filter(user=request.user).first()
        serializer = BankDetailsSerializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED if not instance else status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
@permission_classes([IsTherapist])
def therapist_profile_view(request):
    if request.method == 'GET':
        data = {
            'location': LocationSerializer(Location.objects.filter(user=request.user).first()).data if Location.objects.filter(user=request.user).exists() else {},
            'pictures': PicturesSerializer(Pictures.objects.filter(user=request.user).first()).data if Pictures.objects.filter(user=request.user).exists() else {},
            'services': ServicesSerializer(Services.objects.filter(user=request.user).first()).data if Services.objects.filter(user=request.user).exists() else {},
            'bank_details': BankDetailsSerializer(BankDetails.objects.filter(user=request.user).first()).data if BankDetails.objects.filter(user=request.user).exists() else {}
        }
        return Response(data)
    serializer = TherapistProfileSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsTherapist])
def incoming_orders_view(request):
    orders = Order.objects.filter(therapist=request.user, status='pending')
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsTherapist])
def order_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, therapist=request.user)
    serializer = OrderSerializer(order)
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsTherapist])
def update_order_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, therapist=request.user)
    serializer = OrderUpdateSerializer(order, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsTherapist])
def accept_order_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, therapist=request.user, status='pending')
    order.status = 'accepted'
    order.accepted_at = timezone.now()
    order.save()
    serializer = OrderSerializer(order)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsTherapist])
def start_service_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, therapist=request.user, status='accepted')
    order.status = 'started'
    order.started_at = timezone.now()
    order.save()
    serializer = OrderSerializer(order)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsTherapist])
def complete_order_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, therapist=request.user, status='started')
    order.status = 'completed'
    order.completed_at = timezone.now()
    order.save()
    fee = Decimal('0.20')
    Earnings.objects.create(
        user=request.user,
        order=order,
        amount=order.price,
        platform_fee=order.price * fee,
        net_amount=order.price - order.price * fee
    )
    serializer = OrderSerializer(order)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsTherapist])
def cancel_order_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, therapist=request.user, status__in=['pending', 'accepted'])
    order.status = 'cancelled'
    order.cancelled_at = timezone.now()
    order.save()
    serializer = OrderSerializer(order)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsTherapist])
def earnings_summary_view(request):
    period = request.query_params.get('period', 'week')
    earnings = Earnings.objects.filter(user=request.user)
    total = earnings.aggregate(total=Sum('net_amount'), orders=Count('id'))
    today = timezone.now().date()
    if period == 'day':
        start = today - datetime.timedelta(days=6)
        timeline = earnings.filter(created_at__date__gte=start).annotate(day=TruncDay('created_at')).values('day').annotate(amount=Sum('net_amount'), count=Count('id')).order_by('day')
    elif period == 'week':
        start = today - datetime.timedelta(weeks=3)
        timeline = earnings.filter(created_at__date__gte=start).annotate(week=TruncWeek('created_at')).values('week').annotate(amount=Sum('net_amount'), count=Count('id')).order_by('week')
    elif period == 'month':
        start = (today.replace(day=1) - datetime.timedelta(days=150)).replace(day=1)
        timeline = earnings.filter(created_at__date__gte=start).annotate(month=TruncMonth('created_at')).values('month').annotate(amount=Sum('net_amount'), count=Count('id')).order_by('month')
    else:
        timeline = []
    recent = Order.objects.filter(therapist=request.user, status='completed').order_by('-completed_at')[:5]
    data = {
        'total_earnings': total.get('total') or 0,
        'total_orders': total.get('orders') or 0,
        'earnings_over_time': list(timeline),
        'recent_orders': OrderSerializer(recent, many=True).data
    }
    return Response(data)

@api_view(['GET'])
@permission_classes([IsTherapist])
def conversations_view(request):
    convs = Conversation.objects.filter(participants=request.user)
    serializer = ConversationSerializer(convs, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsTherapist])
def conversation_detail_view(request, conversation_id):
    conv = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    Message.objects.filter(receiver=request.user, sender__in=conv.participants.exclude(id=request.user.id), is_read=False).update(is_read=True)
    msgs = Message.objects.filter(
        Q(sender=request.user, receiver__in=conv.participants.exclude(id=request.user.id)) |
        Q(receiver=request.user, sender__in=conv.participants.exclude(id=request.user.id))
    ).order_by('created_at')
    return Response({'conversation': ConversationSerializer(conv, context={'request': request}).data, 'messages': MessageSerializer(msgs, many=True).data})

@api_view(['POST'])
@permission_classes([IsTherapist])
def send_message_view(request, conversation_id):
    conv = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    recipient = conv.participants.exclude(id=request.user.id).first()
    msg = Message.objects.create(sender=request.user, receiver=recipient, content=request.data.get('content', ''))
    conv.last_message = msg
    conv.save()
    return Response(MessageSerializer(msg).data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsTherapist])
def therapist_stats_view(request):
    orders = Order.objects.filter(therapist=request.user)
    total = orders.count()
    completed = orders.filter(status='completed').count()
    cancelled = orders.filter(status='cancelled').count()
    rated = orders.filter(status='completed', rating__isnull=False)
    avg_rating = rated.aggregate(avg=Avg('rating'))['avg'] or 0
    non_pending = orders.exclude(status='pending').count()
    response_rate = (orders.filter(status__in=['accepted', 'started', 'completed']).count() / non_pending * 100) if non_pending else 0
    finished = orders.filter(status__in=['completed', 'cancelled']).count()
    completion_rate = (completed / finished * 100) if finished else 0
    data = {
        'total_orders': total,
        'completed_orders': completed,
        'cancelled_orders': cancelled,
        'avg_rating': round(avg_rating, 1),
        'response_rate': round(response_rate, 1),
        'completion_rate': round(completion_rate, 1)
    }
    return Response(data)

@api_view(['GET'])
@permission_classes([IsTherapist])
def therapist_reviews_list(request):
    reviews = TherapistReview.objects.filter(therapist=request.user)
    if request.query_params.get('min_rating'):
        reviews = reviews.filter(rating__gte=request.query_params.get('min_rating'))
    if request.query_params.get('max_rating'):
        reviews = reviews.filter(rating__lte=request.query_params.get('max_rating'))
    return Response(TherapistReviewSerializer(reviews, many=True).data)

@api_view(['GET'])
@permission_classes([IsTherapist])
def therapist_review_summary(request):
    serializer = TherapistReviewSummarySerializer(request.user)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsTherapist])
def therapist_review_detail(request, review_id):
    review = get_object_or_404(TherapistReview, id=review_id, therapist=request.user)
    return Response(TherapistReviewSerializer(review).data)

@api_view(['POST'])
@permission_classes([IsCustomer])
def post_therapist_review(request):
    serializer = TherapistReviewSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(client=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)