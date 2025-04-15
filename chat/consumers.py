import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from chat.models import Conversation, Message

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']
        self.customer_id = self.scope['url_route']['kwargs']['customer_id']
        self.therapist_id = self.scope['url_route']['kwargs']['therapist_id']
        if not user.is_authenticated:
            await self.close()
            return
        if user.role == 'customer' and str(user.id) != self.customer_id:
            await self.close()
            return
        if user.role == 'therapist' and str(user.id) != self.therapist_id:
            await self.close()
            return
        if user.role not in ['customer', 'therapist']:
            await self.close()
            return
        self.room_group_name = f'chat_{self.customer_id}_{self.therapist_id}'
        self.conversation = await self.get_or_create_conversation(self.customer_id, self.therapist_id)
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message', '')
        username = self.scope['user'].username
        sender_id = self.scope['user'].id
        receiver_id = self.therapist_id if self.scope['user'].role == 'customer' else self.customer_id
        msg_obj = await self.create_message(self.conversation, sender_id, receiver_id, message)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username,
                'message_id': str(msg_obj.id),
            }
        )
    
    async def chat_message(self, event):
        message = event['message']
        username = event.get('username', 'Anonymous')
        await self.send(text_data=json.dumps({'message': message, 'username': username}))
    
    @database_sync_to_async
    def get_or_create_conversation(self, customer_id, therapist_id):
        conversation = Conversation.objects.filter(participants__id=customer_id).filter(participants__id=therapist_id).first()
        if not conversation:
            conversation = Conversation.objects.create()
            conversation.participants.add(customer_id, therapist_id)
        return conversation
    
    @database_sync_to_async
    def create_message(self, conversation, sender_id, receiver_id, content):
        sender = User.objects.get(id=sender_id)
        receiver = User.objects.get(id=receiver_id)
        message_obj = Message.objects.create(conversation=conversation, sender=sender, receiver=receiver, content=content)
        conversation.last_message = message_obj
        conversation.save()
        return message_obj