from rest_framework import serializers
from .models import Conversation, Message
from User.serializers import UserMinimalSerializer

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