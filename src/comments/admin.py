from django.contrib import admin

# Register your models here.
from .models import Comment, Document

class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', '__str__', 'text']
    class Meta:
        model = Comment

admin.site.register(Comment, CommentAdmin)
admin.site.register(Document)
