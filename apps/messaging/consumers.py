import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from apps.notifications.services import notify_new_chat_message

from .models import Conversation, Message

MAX_MESSAGE_LENGTH = 4000


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
            return

        self.conversation_id = int(self.scope['url_route']['kwargs']['conversation_id'])

        # Seul le client propriétaire de la conversation ou l'équipe peut s'y connecter
        if not await self.user_can_access(user, self.conversation_id):
            await self.close()
            return

        self.room_group_name = f"chat_{self.conversation_id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    @database_sync_to_async
    def user_can_access(self, user, conversation_id):
        try:
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return False
        return user.is_staff or conversation.user_id == user.id

    @database_sync_to_async
    def save_message_and_notify(self, user, conversation_id, content):
        msg = Message.objects.create(
            conversation_id=conversation_id,
            sender=user,
            content=content,
        )
        notify_new_chat_message(msg)
        return msg

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data or "")
        except (TypeError, ValueError):
            return

        message = str(data.get('message', '')).strip()[:MAX_MESSAGE_LENGTH]
        if not message:
            return

        user = self.scope['user']
        msg = await self.save_message_and_notify(user, self.conversation_id, message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "user_id": user.id,
                "sent_at": msg.sent_at.isoformat(),
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "message": event["message"],
            "user_id": event["user_id"],
            "sent_at": event.get("sent_at"),
        }))
