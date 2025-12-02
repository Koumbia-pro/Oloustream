from django.urls import path
from .views import (
    notification_list_view,
    notification_mark_read_view,
    notification_mark_all_read_view,
)

app_name = "notifications"

urlpatterns = [
    path('', notification_list_view, name='list'),
    path('<int:notif_id>/read/', notification_mark_read_view, name='mark_read'),
    path('read-all/', notification_mark_all_read_view, name='mark_all_read'),
]