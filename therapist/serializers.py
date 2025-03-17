from rest_framework import serializers
from .models import Location, Pictures, Services, BankDetails

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