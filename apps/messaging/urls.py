from django.urls import path
from .views import (
    user_chat_view,
    admin_conversation_list_view,
    admin_conversation_chat_view,
)

app_name = "messaging"

urlpatterns = [
    # Chat utilisateur
    path('chat/', user_chat_view, name='user_chat'),

    # Admin
    path('admin/conversations/', admin_conversation_list_view, name='admin_conversations_list'),
    path('admin/conversations/<int:conversation_id>/', admin_conversation_chat_view, name='admin_conversation_chat'),
]