from rest_framework import serializers
from .models import CustomerAddress, Booking, Transaction

class CustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerAddress
        fields = ['name', 'address', 'latitude', 'longitude']

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

class TherapistDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.EmailField(allow_null=True)
    address = serializers.CharField()
    services = serializers.JSONField()

class CustomerProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.EmailField(allow_null=True)
    bookings = BookingSerializer(many=True)
    transactions = TransactionSerializer(many=True)
