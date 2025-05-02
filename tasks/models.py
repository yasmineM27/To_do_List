from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class Tag(models.Model):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=20, default='blue')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tags')
    
    def __str__(self):
        return self.name

class ToDoList(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='todo_lists')
    
    def __str__(self):
        return self.title
    
    def get_incomplete_tasks_count(self):
        return self.tasks.filter(is_completed=False).count()
    
    def get_completed_tasks_count(self):
        return self.tasks.filter(is_completed=True).count()

class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    todo_list = models.ForeignKey(ToDoList, on_delete=models.CASCADE, related_name='tasks')
    tags = models.ManyToManyField(Tag, blank=True, related_name='tasks')
    
    def __str__(self):
        return self.title
    
    def mark_completed(self):
        self.is_completed = True
        self.completed_at = timezone.now()
        self.save()
    
    def mark_incomplete(self):
        self.is_completed = False
        self.completed_at = None
        self.save()
    
    def is_overdue(self):
        if self.due_date and not self.is_completed:
            return timezone.now() > self.due_date
        return False