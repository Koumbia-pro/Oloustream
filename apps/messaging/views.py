from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Max

from .models import Conversation, Message
from apps.notifications.models import Notification, NotificationTypeChoices
from apps.notifications.services import notify_new_chat_message


# ---------- CHAT UTILISATEUR (HTTP) ----------

@login_required
def user_chat_view(request):
    """
    Un utilisateur a UNE conversation unique.
    Envoi du message via HTTP (POST) + notification pour l'admin.
    """
    conversation = Conversation.objects.filter(user=request.user).order_by('created_at').first()
    if conversation is None:
        conversation = Conversation.objects.create(user=request.user)

    if request.method == "POST":
        content = request.POST.get('message', '').strip()
        if content:
            msg = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
            # Notification de chat (vers admin)
            notify_new_chat_message(msg)
        return redirect('messaging:user_chat')

    messages_qs = conversation.messages.select_related('sender').order_by('sent_at')

    return render(request, "user/chat.html", {
        "conversation": conversation,
        "messages": messages_qs,
    })


# ---------- CHAT ADMIN : LISTE & DÉTAIL ----------

@staff_member_required
def admin_conversation_list_view(request):
    """
    Liste des conversations avec :
    - dernier message,
    - badge non lus,
    - recherche,
    - filtre "avec non lus".
    """
    # Annoter la dernière date de message
    conversations = (
        Conversation.objects
        .select_related('user', 'admin')
        .annotate(last_sent=Max('messages__sent_at'))
        .order_by('-last_sent', '-created_at')
    )

    # Recherche sur client / dernier message
    q = request.GET.get('q', '').strip()
    if q:
        conversations = conversations.filter(
            Q(user__username__icontains=q) |
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(user__email__icontains=q) |
            Q(messages__content__icontains=q)
        ).distinct()

    # Filtre "non lus"
    only_unread = request.GET.get('only_unread', '') == 'yes'
    if only_unread:
        # au moins un message non lu pour l'admin
        conversations = conversations.filter(
            messages__is_read=False
        ).exclude(messages__sender=request.user).distinct()

    # Construire des infos dérivées pour l’affichage
    conv_data = []
    for c in conversations:
        last_msg = c.messages.select_related('sender').order_by('-sent_at').first()
        has_unread = c.messages.filter(is_read=False).exclude(sender=request.user).exists()

        conv_data.append({
            "conversation": c,
            "last_message": last_msg,
            "has_unread": has_unread,
        })

    context = {
        "conversations_data": conv_data,
        "q": q,
        "only_unread": only_unread,
        "unread_notifications_count": Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count(),
        "unread_messages_count": Notification.objects.filter(
            user=request.user,
            notification_type=NotificationTypeChoices.MESSAGE_RECEIVED,
            is_read=False
        ).count(),
    }
    return render(request, "admin/messages/list.html", context)


@staff_member_required
def admin_conversation_chat_view(request, conversation_id):
    """
    Vue admin pour discuter dans une conversation donnée.
    Envoi du message via HTTP + notification pour l’utilisateur.
    Marque les messages reçus comme lus.
    """
    conversation = get_object_or_404(
        Conversation.objects.select_related('user', 'admin'),
        pk=conversation_id
    )

    # Assigner automatiquement l'admin à la conversation si pas encore défini
    if conversation.admin is None and request.user.is_staff:
        conversation.admin = request.user
        conversation.save(update_fields=['admin'])

    if request.method == "POST":
        content = request.POST.get('message', '').strip()
        if content:
            msg = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
            # Notification de chat (vers l'utilisateur)
            notify_new_chat_message(msg)
        return redirect('messaging:admin_conversation_chat', conversation_id=conversation.id)

    # Marquer comme lus les messages non lus envoyés par l’autre (l’utilisateur)
    Message.objects.filter(
        conversation=conversation,
        is_read=False
    ).exclude(sender=request.user).update(is_read=True)

    messages_qs = conversation.messages.select_related('sender').order_by('sent_at')

    context = {
        "conversation": conversation,
        "messages": messages_qs,
        "unread_notifications_count": Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count(),
        "unread_messages_count": Notification.objects.filter(
            user=request.user,
            notification_type=NotificationTypeChoices.MESSAGE_RECEIVED,
            is_read=False
        ).count(),
    }
    return render(request, "admin/messages/chat.html", context)