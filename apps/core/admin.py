from django.contrib import admin

from .models import ContactRequest


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ("full_name", "company", "subject", "email", "phone", "status", "created_at")
    list_filter = ("status", "subject", "created_at")
    search_fields = ("full_name", "company", "email", "phone", "message")
    list_editable = ("status",)
    readonly_fields = ("ip_address", "created_at")
    date_hierarchy = "created_at"


from django.utils.html import format_html  # noqa: E402

from .models import VideoRealisation  # noqa: E402


@admin.register(VideoRealisation)
class VideoRealisationAdmin(admin.ModelAdmin):
    list_display = ("apercu", "title", "category", "show_on_home", "is_published", "order")
    list_display_links = ("apercu", "title")
    list_editable = ("category", "show_on_home", "is_published", "order")
    list_filter = ("category", "show_on_home", "is_published")
    search_fields = ("title", "description", "tags")
    readonly_fields = ("apercu_grand",)
    fieldsets = (
        (None, {"fields": ("youtube_url", "apercu_grand", "title", "subtitle", "description", "tags")}),
        ("Affichage", {"fields": ("category", "show_on_home", "is_published", "order")}),
    )

    @admin.display(description="Aperçu")
    def apercu(self, obj):
        if not obj.youtube_id:
            return "—"
        return format_html('<img src="{}" alt="" style="width:120px;border-radius:6px">', obj.thumbnail_url)

    @admin.display(description="Aperçu de la vidéo")
    def apercu_grand(self, obj):
        if not obj.pk or not obj.youtube_id:
            return "L'aperçu apparaît après l'enregistrement."
        return format_html('<a href="{}" target="_blank" rel="noopener"><img src="{}" alt="" style="width:320px;border-radius:8px"></a>',
                           obj.watch_url, obj.thumbnail_url)


from .models import Testimonial  # noqa: E402


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("__str__", "is_published", "order")
    list_editable = ("is_published", "order")
    search_fields = ("quote", "author_name", "organization")
