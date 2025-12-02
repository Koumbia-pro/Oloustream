import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

from .models import Conversation, Message
from apps.notifications.services import notify_new_chat_message

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
            return

        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f"chat_{self.conversation_id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    @database_sync_to_async
    def save_message_and_notify(self, user, conversation_id, content):
        conversation = Conversation.objects.get(id=conversation_id)
        msg = Message.objects.create(
            conversation=conversation,
            sender=user,
            content=content
        )
        # ICI : création de la notif
        notify_new_chat_message(msg)
        print("DEBUG: notification chat créée potentiellement")
        return msg.id

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data)
        except Exception:
            return

        message = data.get('message', '').strip()
        if not message:
            return

        user = self.scope['user']
        user_id = user.id

        # Sauvegarder + notifier
        await self.save_message_and_notify(user, int(self.conversation_id), message)

        # Diffuser à tous les clients de la conversation
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "user_id": user_id,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "message": event["message"],
            "user_id": event["user_id"],
        }))