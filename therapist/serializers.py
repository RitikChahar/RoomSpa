from rest_framework import serializers
from .models import Location, Pictures, Services, BankDetails, Order, Message, Conversation
from User.serializers import UserMinimalSerializer

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
        
        location_data = validated_data.get('location')
        if location_data:
            Location.objects.update_or_create(
                user=user,
                defaults=location_data
            )
        
        pictures_data = validated_data.get('pictures')
        if pictures_data:
            Pictures.objects.update_or_create(
                user=user,
                defaults=pictures_data
            )
        
        services_data = validated_data.get('services')
        if services_data:
            Services.objects.update_or_create(
                user=user,
                defaults=services_data
            )
        
        bank_details_data = validated_data.get('bank_details')
        if bank_details_data:
            BankDetails.objects.update_or_create(
                user=user,
                defaults=bank_details_data
            )
        
        return {
            'location': location_data,
            'pictures': pictures_data,
            'services': services_data,
            'bank_details': bank_details_data
        }
    
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
        return Message.objects.filter(
            receiver=user,
            sender__in=obj.participants.all().exclude(id=user.id),
            is_read=False
        ).count()