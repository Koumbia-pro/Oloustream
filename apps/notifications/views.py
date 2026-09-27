from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.core.utils import safe_redirect

from .models import Notification
from .services import mark_all_notifications_as_read, mark_notification_as_read


@login_required
def notification_list_view(request):
    base_qs = Notification.objects.filter(user=request.user).select_related("actor")
    qs = base_qs

    filter_status = request.GET.get('status', '')
    if filter_status == 'unread':
        qs = qs.filter(is_read=False)

    page_obj = Paginator(qs, 15).get_page(request.GET.get('page'))

    template = "admin/notifications/list.html" if request.user.is_staff else "user/notifications.html"
    return render(request, template, {
        "page_obj": page_obj,
        "filter_status": filter_status,
        "total_count": base_qs.count(),
        "unread_count": base_qs.filter(is_read=False).count(),
    })


@login_required
def notification_mark_read_view(request, notif_id):
    notif = get_object_or_404(Notification, pk=notif_id, user=request.user)
    mark_notification_as_read(notif)
    return safe_redirect(request, notif.link, 'notifications:list')


@login_required
@require_POST
def notification_mark_all_read_view(request):
    mark_all_notifications_as_read(request.user)
    return redirect('notifications:list')
