from apps.messaging import routing as messaging_routing

websocket_urlpatterns = [
    *messaging_routing.websocket_urlpatterns,
]