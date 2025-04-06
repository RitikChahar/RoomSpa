from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .models import Conversation, Message
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = 'chat_%s' % self.conversation_id
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        sender_id = data['sender_id']
        receiver_id = data['receiver_id']
        msg = await self.create_message(self.conversation_id, sender_id, receiver_id, message)
        msg_data = {'id': msg.id, 'conversation': msg.conversation.id, 'sender': msg.sender.id, 'receiver': msg.receiver.id, 'content': msg.content, 'created_at': msg.created_at.strftime("%Y-%m-%d %H:%M:%S")}
        await self.channel_layer.group_send(self.room_group_name, {'type': 'chat_message', 'message': msg_data})

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['message']))

    @database_sync_to_async
    def create_message(self, conversation_id, sender_id, receiver_id, content):
        User = get_user_model()
        conversation = Conversation.objects.get(id=conversation_id)
        sender = User.objects.get(id=sender_id)
        receiver = User.objects.get(id=receiver_id)
        msg = Message.objects.create(conversation=conversation, sender=sender, receiver=receiver, content=content)
        conversation.last_message = msg
        conversation.save()
        return msg