from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conversation_list(request):
    user = request.user
    conversations = Conversation.objects.filter(participants=user).order_by('-updated_at')
    serializer = ConversationSerializer(conversations, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conversation_messages(request):
    conversation_id = request.query_params.get('conversation_id', '').strip()
    if not conversation_id:
        return Response({'message': 'conversation_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        conversation = Conversation.objects.get(id=conversation_id)
    except Conversation.DoesNotExist:
        return Response({'message': 'Conversation not found.'}, status=status.HTTP_404_NOT_FOUND)
    if request.user not in conversation.participants.all():
        return Response({'message': 'User not a participant of this conversation.'}, status=status.HTTP_403_FORBIDDEN)
    messages = Message.objects.filter(conversation=conversation)
    serializer = MessageSerializer(messages, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)