from django.contrib import admin
from .models import ToDoList, Task, Tag

@admin.register(ToDoList)
class ToDoListAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'created_at']
    list_filter = ['user', 'created_at']
    search_fields = ['title', 'description']

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'todo_list', 'is_completed', 'due_date', 'priority']
    list_filter = ['is_completed', 'priority', 'due_date', 'todo_list__user']
    search_fields = ['title', 'description']
    readonly_fields = ['id']
    filter_horizontal = ['tags']

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'user']
    list_filter = ['user', 'color']
    search_fields = ['name']