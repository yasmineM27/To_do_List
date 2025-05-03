from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import icalendar
from datetime import datetime, timedelta

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
    # New fields for collaboration
    is_shared = models.BooleanField(default=False)
    shared_with = models.ManyToManyField(User, related_name='shared_lists', blank=True)
    share_code = models.CharField(max_length=20, blank=True, null=True, unique=True)
    
    def __str__(self):
        return self.title
    
    def get_incomplete_tasks_count(self):
        return self.tasks.filter(is_completed=False).count()
    
    def get_completed_tasks_count(self):
        return self.tasks.filter(is_completed=True).count()
    
    def get_tasks_by_status(self):
        """Return tasks grouped by status for kanban view"""
        return {
            'todo': self.tasks.filter(status='todo'),
            'in_progress': self.tasks.filter(status='in_progress'),
            'done': self.tasks.filter(is_completed=True)
        }
    
    def generate_ical(self):
        """Generate iCal calendar for this todo list"""
        cal = icalendar.Calendar()
        cal.add('prodid', '-//TaskFlow//taskflow.app//')
        cal.add('version', '2.0')
        cal.add('x-wr-calname', f'TaskFlow: {self.title}')
        
        for task in self.tasks.all():
            if task.due_date:
                event = icalendar.Event()
                event.add('summary', task.title)
                event.add('description', task.description)
                event.add('dtstart', task.due_date.date())
                event.add('dtend', (task.due_date + timedelta(hours=1)).date())
                event.add('dtstamp', datetime.now())
                event.add('uid', str(task.id))
                event.add('priority', 5)  # Medium priority
                if task.is_completed:
                    event.add('status', 'COMPLETED')
                cal.add_component(event)
        
        return cal.to_ical()

class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
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
    # New field for kanban status
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='todo')
    # For drag and drop ordering
    position = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['position']
    
    def __str__(self):
        return self.title
    
    def mark_completed(self):
        self.is_completed = True
        self.status = 'done'
        self.completed_at = timezone.now()
        self.save()
    
    def mark_incomplete(self):
        self.is_completed = False
        self.status = 'todo'
        self.completed_at = None
        self.save()
    
    def is_overdue(self):
        if self.due_date and not self.is_completed:
            return timezone.now() > self.due_date
        return False

# New model for collaboration invitations
class Invitation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]
    
    todo_list = models.ForeignKey(ToDoList, on_delete=models.CASCADE, related_name='invitations')
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    invited_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_invitations')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    class Meta:
        unique_together = ('todo_list', 'invited_user')
