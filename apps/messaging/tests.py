from channels.db import database_sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase

from apps.messaging.models import Conversation
from apps.messaging.routing import websocket_urlpatterns
from apps.core.tests.factories import make_staff, make_user


class ChatConsumerAccessTests(TransactionTestCase):
    async def _connect(self, user, conversation_id):
        communicator = WebsocketCommunicator(URLRouter(websocket_urlpatterns), f"/ws/chat/{conversation_id}/")
        communicator.scope["user"] = user
        connected, _ = await communicator.connect()
        await communicator.disconnect()
        return connected

    async def test_only_owner_and_staff_can_join(self):
        owner = await database_sync_to_async(make_user)("owner")
        intruder = await database_sync_to_async(make_user)("intrus")
        staff = await database_sync_to_async(make_staff)("staff")
        conversation = await database_sync_to_async(Conversation.objects.create)(user=owner)

        self.assertTrue(await self._connect(owner, conversation.pk))
        self.assertTrue(await self._connect(staff, conversation.pk))
        self.assertFalse(await self._connect(intruder, conversation.pk))
