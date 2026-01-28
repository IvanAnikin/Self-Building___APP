from django.contrib import admin
from .models import ChatMessage, CodeSnippet, FeatureRequest

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'message_preview', 'is_user', 'timestamp')
    list_filter = ('is_user', 'timestamp')
    search_fields = ('message', 'response')
    ordering = ('-timestamp',)
    
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'

@admin.register(CodeSnippet)
class CodeSnippetAdmin(admin.ModelAdmin):
    list_display = ('id', 'filename', 'language', 'created_at', 'updated_at')
    list_filter = ('language', 'created_at', 'updated_at')
    search_fields = ('filename', 'code')
    ordering = ('-updated_at',)

@admin.register(FeatureRequest)
class FeatureRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'description_preview', 'status', 'created_at', 'completed_at')
    list_filter = ('status', 'created_at')
    search_fields = ('description',)
    ordering = ('-created_at',)
    
    def description_preview(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_preview.short_description = 'Description'
