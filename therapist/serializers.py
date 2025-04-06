from rest_framework import serializers
from .models import Location, Pictures, Services, BankDetails, Order, Message, Conversation, TherapistReview
from User.serializers import UserMinimalSerializer
from django.contrib.auth import get_user_model
from django.db.models import Avg

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['address', 'service_radius', 'latitude', 'longitude']

class PicturesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pictures
        fields = ['profile_picture', 'more_pictures', 'certificate', 'national_id']

class ServicesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Services
        fields = ['services']

class BankDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankDetails
        fields = ['bank_name', 'account_number', 'swift_code']

class TherapistProfileSerializer(serializers.Serializer):
    location = LocationSerializer(required=False)
    pictures = PicturesSerializer(required=False)
    services = ServicesSerializer(required=False)
    bank_details = BankDetailsSerializer(required=False)
    
    def create(self, validated_data):
        user = self.context['request'].user
        if 'location' in validated_data:
            Location.objects.update_or_create(user=user, defaults=validated_data.get('location'))
        if 'pictures' in validated_data:
            Pictures.objects.update_or_create(user=user, defaults=validated_data.get('pictures'))
        if 'services' in validated_data:
            Services.objects.update_or_create(user=user, defaults=validated_data.get('services'))
        if 'bank_details' in validated_data:
            BankDetails.objects.update_or_create(user=user, defaults=validated_data.get('bank_details'))
        return validated_data
    
class OrderSerializer(serializers.ModelSerializer):
    client_details = UserMinimalSerializer(source='client', read_only=True)
    therapist_details = UserMinimalSerializer(source='therapist', read_only=True)
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ('id', 'therapist', 'created_at', 'accepted_at', 'started_at', 'completed_at', 'cancelled_at')

class OrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']

class MessageSerializer(serializers.ModelSerializer):
    sender_details = UserMinimalSerializer(source='sender', read_only=True)
    class Meta:
        model = Message
        fields = '__all__'
        read_only_fields = ('id', 'sender', 'created_at')

class ConversationSerializer(serializers.ModelSerializer):
    participants_details = UserMinimalSerializer(source='participants', many=True, read_only=True)
    last_message_content = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    class Meta:
        model = Conversation
        fields = '__all__'
        read_only_fields = ('id', 'updated_at')
    def get_last_message_content(self, obj):
        if obj.last_message:
            return MessageSerializer(obj.last_message).data
        return None
    def get_unread_count(self, obj):
        user = self.context['request'].user
        return Message.objects.filter(receiver=user, sender__in=obj.participants.exclude(id=user.id), is_read=False).count()
    
class TherapistReviewSerializer(serializers.ModelSerializer):
    client_name = serializers.SerializerMethodField()
    service_type = serializers.SerializerMethodField()
    class Meta:
        model = TherapistReview
        fields = ['id', 'client_name', 'rating', 'comment', 'service_quality', 'punctuality', 'professionalism', 'service_type', 'created_at']
        read_only_fields = ['id', 'client_name', 'service_type', 'created_at']
    def get_client_name(self, obj):
        return obj.client.get_full_name() or obj.client.username
    def get_service_type(self, obj):
        if obj.order:
            return obj.order.service_type
        return None

class TherapistReviewSummarySerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    service_quality_avg = serializers.SerializerMethodField()
    punctuality_avg = serializers.SerializerMethodField()
    professionalism_avg = serializers.SerializerMethodField()
    recent_reviews = serializers.SerializerMethodField()
    class Meta:
        model = get_user_model()
        fields = ['id', 'average_rating', 'review_count', 'service_quality_avg', 'punctuality_avg', 'professionalism_avg', 'recent_reviews']
    def get_average_rating(self, obj):
        return TherapistReview.objects.filter(therapist=obj).aggregate(avg=Avg('rating'))['avg'] or 0
    def get_review_count(self, obj):
        return TherapistReview.objects.filter(therapist=obj).count()
    def get_service_quality_avg(self, obj):
        return TherapistReview.objects.filter(therapist=obj, service_quality__isnull=False).aggregate(avg=Avg('service_quality'))['avg'] or 0
    def get_punctuality_avg(self, obj):
        return TherapistReview.objects.filter(therapist=obj, punctuality__isnull=False).aggregate(avg=Avg('punctuality'))['avg'] or 0
    def get_professionalism_avg(self, obj):
        return TherapistReview.objects.filter(therapist=obj, professionalism__isnull=False).aggregate(avg=Avg('professionalism'))['avg'] or 0
    def get_recent_reviews(self, obj):
        recent = TherapistReview.objects.filter(therapist=obj).order_by('-created_at')[:5]
        return TherapistReviewSerializer(recent, many=True).data