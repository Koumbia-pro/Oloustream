from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Exists, Max, OuterRef, Q, Subquery
from django.shortcuts import get_object_or_404, redirect, render

from apps.notifications.services import notify_new_chat_message

from .models import Conversation, Message

MAX_MESSAGE_LENGTH = 4000


def _post_message(request, conversation):
    content = request.POST.get('message', '').strip()[:MAX_MESSAGE_LENGTH]
    if content:
        msg = Message.objects.create(conversation=conversation, sender=request.user, content=content)
        notify_new_chat_message(msg)


# ---------- CHAT UTILISATEUR ----------

@login_required
def user_chat_view(request):
    """Chaque utilisateur dispose d'une conversation unique avec l'équipe Oloustream."""
    conversation = Conversation.objects.filter(user=request.user).order_by('created_at').first()
    if conversation is None:
        conversation = Conversation.objects.create(user=request.user)

    if request.method == "POST":
        _post_message(request, conversation)
        return redirect('messaging:user_chat')

    # Les réponses de l'équipe sont marquées comme lues à l'ouverture
    conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    # NB : « chat_messages » et non « messages », qui est réservé au système de messages Django
    return render(request, "user/chat.html", {
        "conversation": conversation,
        "chat_messages": conversation.messages.select_related('sender').order_by('sent_at'),
    })


# ---------- CHAT ADMIN : LISTE & DÉTAIL ----------

@staff_member_required
def admin_conversation_list_view(request):
    last_message = Message.objects.filter(conversation=OuterRef('pk')).order_by('-sent_at')
    unread_from_client = Message.objects.filter(
        conversation=OuterRef('pk'), is_read=False, sender=OuterRef('user'),
    )
    conversations = (
        Conversation.objects
        .select_related('user', 'admin')
        .annotate(
            last_sent=Max('messages__sent_at'),
            messages_count=Count('messages'),
            last_content=Subquery(last_message.values('content')[:1]),
            last_sender_id=Subquery(last_message.values('sender_id')[:1]),
            has_unread=Exists(unread_from_client),
        )
        .filter(messages_count__gt=0)
        .order_by('-last_sent')
    )

    q = request.GET.get('q', '').strip()
    if q:
        conversations = conversations.filter(
            Q(user__username__icontains=q) | Q(user__first_name__icontains=q)
            | Q(user__last_name__icontains=q) | Q(user__email__icontains=q)
            | Q(messages__content__icontains=q)
        ).distinct()

    only_unread = request.GET.get('only_unread', '') == 'yes'
    if only_unread:
        conversations = conversations.filter(has_unread=True)

    conversations = list(conversations)
    return render(request, "admin/messages/list.html", {
        "conversations": conversations,
        "q": q,
        "only_unread": only_unread,
        "total_conversations": len(conversations),
        "unread_conversations": sum(1 for c in conversations if c.has_unread),
    })


@staff_member_required
def admin_conversation_chat_view(request, conversation_id):
    conversation = get_object_or_404(Conversation.objects.select_related('user', 'admin'), pk=conversation_id)

    if conversation.admin is None:
        conversation.admin = request.user
        conversation.save(update_fields=['admin'])

    if request.method == "POST":
        _post_message(request, conversation)
        return redirect('messaging:admin_conversation_chat', conversation_id=conversation.id)

    conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    return render(request, "admin/messages/chat.html", {
        "conversation": conversation,
        "chat_messages": conversation.messages.select_related('sender').order_by('sent_at'),
        "client_reservations": conversation.user.reservations.order_by('-created_at')[:5],
    })
