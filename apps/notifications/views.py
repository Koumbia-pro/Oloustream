from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator

from .models import Notification
from .services import mark_notification_as_read, mark_all_notifications_as_read


@login_required
def notification_list_view(request):
    qs = Notification.objects.filter(user=request.user).order_by('-created_at')

    # Filtre simple : tout, non lues
    filter_status = request.GET.get('status', '')
    if filter_status == 'unread':
        qs = qs.filter(is_read=False)

    paginator = Paginator(qs, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "admin/notifications/list.html", {
        "page_obj": page_obj,
        "filter_status": filter_status,
    })


@login_required
def notification_mark_read_view(request, notif_id):
    notif = get_object_or_404(Notification, pk=notif_id, user=request.user)
    mark_notification_as_read(notif)

    # Redirection : si notif.link existe, on l’utilise
    if notif.link:
        return redirect(notif.link)
    return redirect('notifications:list')


@login_required
def notification_mark_all_read_view(request):
    mark_all_notifications_as_read(request.user)
    return redirect('notifications:list')