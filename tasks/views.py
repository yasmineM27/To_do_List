from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
import uuid
import json
from datetime import datetime, timedelta
from .models import ToDoList, Task, Tag, Invitation
from .forms import ToDoListForm, TaskForm, TagForm, ShareListForm, InvitationResponseForm

@login_required
def dashboard(request):
    # Get statistics
    total_tasks = Task.objects.filter(
        Q(todo_list__user=request.user) | Q(todo_list__shared_with=request.user)
    ).distinct().count()
    
    completed_tasks = Task.objects.filter(
        Q(todo_list__user=request.user) | Q(todo_list__shared_with=request.user),
        is_completed=True
    ).distinct().count()
    
    incomplete_tasks = total_tasks - completed_tasks
    
    overdue_tasks = Task.objects.filter(
        Q(todo_list__user=request.user) | Q(todo_list__shared_with=request.user),
        is_completed=False,
        due_date__lt=timezone.now()
    ).distinct().count()
    
    # Get recent activity
    recent_tasks = Task.objects.filter(
        Q(todo_list__user=request.user) | Q(todo_list__shared_with=request.user)
    ).distinct().order_by('-created_at')[:5]
    
    upcoming_tasks = Task.objects.filter(
        Q(todo_list__user=request.user) | Q(todo_list__shared_with=request.user),
        is_completed=False,
        due_date__gte=timezone.now()
    ).distinct().order_by('due_date')[:5]
    
    # Get lists
    owned_lists = ToDoList.objects.filter(user=request.user).order_by('-created_at')
    shared_lists = ToDoList.objects.filter(shared_with=request.user).order_by('-created_at')
    
    # Get pending invitations
    pending_invitations = Invitation.objects.filter(
        invited_user=request.user,
        status='pending'
    ).select_related('todo_list', 'invited_by')
    
    context = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
        'incomplete_tasks': incomplete_tasks,
        'overdue_tasks': overdue_tasks,
        'recent_tasks': recent_tasks,
        'upcoming_tasks': upcoming_tasks,
        'owned_lists': owned_lists,
        'shared_lists': shared_lists,
        'pending_invitations': pending_invitations,
    }
    
    return render(request, 'tasks/dashboard.html', context)

# ToDoList views
@login_required
def list_todo_lists(request):
    owned_lists = ToDoList.objects.filter(user=request.user).order_by('-created_at')
    shared_lists = ToDoList.objects.filter(shared_with=request.user).order_by('-created_at')
    return render(request, 'tasks/todo_list/list.html', {
        'owned_lists': owned_lists,
        'shared_lists': shared_lists
    })

@login_required
def create_todo_list(request):
    if request.method == 'POST':
        form = ToDoListForm(request.POST)
        if form.is_valid():
            todo_list = form.save(commit=False)
            todo_list.user = request.user
            todo_list.save()
            messages.success(request, 'Todo list created successfully.')
            return redirect('tasks:todo_list_detail', pk=todo_list.pk)
    else:
        form = ToDoListForm()
    
    return render(request, 'tasks/todo_list/form.html', {'form': form, 'title': 'Create Todo List'})

@login_required
def todo_list_detail(request, pk):
    todo_list = get_object_or_404(
        ToDoList.objects.prefetch_related('tasks__tags'),
        Q(pk=pk, user=request.user) | Q(pk=pk, shared_with=request.user)
    )
    
    # Check if the user has permission to view this list
    if todo_list.user != request.user and not todo_list.shared_with.filter(id=request.user.id).exists():
        messages.error(request, "You don't have permission to view this list.")
        return redirect('tasks:dashboard')
    
    tasks = todo_list.tasks.all().order_by('position', '-created_at')
    
    # Group tasks by status for kanban view
    tasks_by_status = {
        'todo': tasks.filter(status='todo', is_completed=False),
        'in_progress': tasks.filter(status='in_progress', is_completed=False),
        'done': tasks.filter(is_completed=True)
    }
    
    # Get collaborators
    collaborators = todo_list.shared_with.all()
    
    return render(request, 'tasks/todo_list/detail.html', {
        'todo_list': todo_list,
        'tasks': tasks,
        'tasks_by_status': tasks_by_status,
        'collaborators': collaborators,
        'is_owner': todo_list.user == request.user
    })

@login_required
def kanban_board(request, pk):
    todo_list = get_object_or_404(
        ToDoList.objects.prefetch_related('tasks__tags'),
        Q(pk=pk, user=request.user) | Q(pk=pk, shared_with=request.user)
    )
    
    # Group tasks by status for kanban view
    tasks_by_status = todo_list.get_tasks_by_status()
    
    return render(request, 'tasks/todo_list/kanban.html', {
        'todo_list': todo_list,
        'tasks_by_status': tasks_by_status,
        'is_owner': todo_list.user == request.user
    })

@login_required
def update_task_status(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = json.loads(request.body)
        task_id = data.get('taskId')
        new_status = data.get('status')
        new_position = data.get('position', 0)
        
        try:
            task = Task.objects.get(id=task_id)
            
            # Check if user has permission
            if task.todo_list.user != request.user and not task.todo_list.shared_with.filter(id=request.user.id).exists():
                return JsonResponse({'error': 'Permission denied'}, status=403)
            
            # Update task status
            task.status = new_status
            if new_status == 'done':
                task.is_completed = True
                task.completed_at = timezone.now()
            else:
                task.is_completed = False
                task.completed_at = None
            
            task.position = new_position
            task.save()
            
            return JsonResponse({'success': True})
        except Task.DoesNotExist:
            return JsonResponse({'error': 'Task not found'}, status=404)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def edit_todo_list(request, pk):
    todo_list = get_object_or_404(ToDoList, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = ToDoListForm(request.POST, instance=todo_list)
        if form.is_valid():
            form.save()
            messages.success(request, 'Todo list updated successfully.')
            return redirect('tasks:todo_list_detail', pk=todo_list.pk)
    else:
        form = ToDoListForm(instance=todo_list)
    
    return render(request, 'tasks/todo_list/form.html', {'form': form, 'title': 'Edit Todo List'})

@login_required
def delete_todo_list(request, pk):
    todo_list = get_object_or_404(ToDoList, pk=pk, user=request.user)
    
    if request.method == 'POST':
        todo_list.delete()
        messages.success(request, 'Todo list deleted successfully.')
        return redirect('tasks:list_todo_lists')
    
    return render(request, 'tasks/todo_list/confirm_delete.html', {'todo_list': todo_list})

# Collaboration views
@login_required
def share_todo_list(request, pk):
    todo_list = get_object_or_404(ToDoList, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = ShareListForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user_to_share_with = User.objects.get(email=email)
            
            # Don't share with yourself
            if user_to_share_with == request.user:
                messages.error(request, "You can't share a list with yourself.")
                return redirect('tasks:share_todo_list', pk=todo_list.pk)
            
            # Check if already shared
            if todo_list.shared_with.filter(id=user_to_share_with.id).exists():
                messages.info(request, f"This list is already shared with {user_to_share_with.username}.")
                return redirect('tasks:todo_list_detail', pk=todo_list.pk)
            
            # Check if invitation already exists
            if Invitation.objects.filter(todo_list=todo_list, invited_user=user_to_share_with, status='pending').exists():
                messages.info(request, f"An invitation has already been sent to {user_to_share_with.username}.")
                return redirect('tasks:todo_list_detail', pk=todo_list.pk)
            
            # Create invitation
            invitation = Invitation.objects.create(
                todo_list=todo_list,
                invited_by=request.user,
                invited_user=user_to_share_with
            )
            
            # Mark list as shared
            todo_list.is_shared = True
            if not todo_list.share_code:
                todo_list.share_code = str(uuid.uuid4())[:8]
            todo_list.save()
            
            messages.success(request, f"Invitation sent to {user_to_share_with.username}.")
            return redirect('tasks:todo_list_detail', pk=todo_list.pk)
    else:
        form = ShareListForm()
    
    # Get current collaborators
    collaborators = todo_list.shared_with.all()
    
    return render(request, 'tasks/todo_list/share.html', {
        'form': form,
        'todo_list': todo_list,
        'collaborators': collaborators
    })

@login_required
def remove_collaborator(request, list_pk, user_pk):
    todo_list = get_object_or_404(ToDoList, pk=list_pk, user=request.user)
    user_to_remove = get_object_or_404(User, pk=user_pk)
    
    if request.method == 'POST':
        todo_list.shared_with.remove(user_to_remove)
        
        # If no more collaborators, update shared status
        if todo_list.shared_with.count() == 0:
            todo_list.is_shared = False
            todo_list.save()
        
        messages.success(request, f"{user_to_remove.username} has been removed from collaborators.")
        return redirect('tasks:share_todo_list', pk=todo_list.pk)
    
    return render(request, 'tasks/todo_list/confirm_remove_collaborator.html', {
        'todo_list': todo_list,
        'collaborator': user_to_remove
    })

@login_required
def invitations(request):
    pending_invitations = Invitation.objects.filter(
        invited_user=request.user,
        status='pending'
    ).select_related('todo_list', 'invited_by')
    
    return render(request, 'tasks/invitations.html', {
        'pending_invitations': pending_invitations
    })

@login_required
def respond_to_invitation(request, invitation_id):
    invitation = get_object_or_404(
        Invitation,
        id=invitation_id,
        invited_user=request.user,
        status='pending'
    )
    
    if request.method == 'POST':
        form = InvitationResponseForm(request.POST, instance=invitation)
        if form.is_valid():
            invitation = form.save()
            
            if invitation.status == 'accepted':
                # Add user to shared_with
                invitation.todo_list.shared_with.add(request.user)
                messages.success(request, f"You've joined {invitation.todo_list.title}.")
            else:
                messages.info(request, f"You've declined the invitation to {invitation.todo_list.title}.")
            
            return redirect('tasks:dashboard')
    else:
        form = InvitationResponseForm(instance=invitation)
    
    return render(request, 'tasks/respond_to_invitation.html', {
        'form': form,
        'invitation': invitation
    })

# Calendar integration
@login_required
def export_calendar(request, pk):
    todo_list = get_object_or_404(
        ToDoList,
        Q(pk=pk, user=request.user) | Q(pk=pk, shared_with=request.user)
    )
    
    ical_data = todo_list.generate_ical()
    
    response = HttpResponse(ical_data, content_type='text/calendar')
    response['Content-Disposition'] = f'attachment; filename="{todo_list.title}.ics"'
    
    return response

# Task views
@login_required
def create_task(request, list_pk):
    todo_list = get_object_or_404(
        ToDoList,
        Q(pk=list_pk, user=request.user) | Q(pk=list_pk, shared_with=request.user)
    )
    
    if request.method == 'POST':
        form = TaskForm(request.user, request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.todo_list = todo_list
            
            # Set position to be at the end of the list for its status
            last_position = Task.objects.filter(
                todo_list=todo_list,
                status=task.status
            ).aggregate(max_pos=models.Max('position'))['max_pos'] or 0
            task.position = last_position + 1
            
            task.save()
            
            # Handle many-to-many relationships
            form.save_m2m()
            
            messages.success(request, 'Task created successfully.')
            
            # Redirect based on where the task was created from
            if 'from_kanban' in request.POST:
                return redirect('tasks:kanban_board', pk=todo_list.pk)
            return redirect('tasks:todo_list_detail', pk=todo_list.pk)
    else:
        # Pre-fill status if provided in GET parameters
        initial = {}
        if 'status' in request.GET:
            initial['status'] = request.GET.get('status')
        
        form = TaskForm(request.user, initial=initial)
    
    return render(request, 'tasks/task/form.html', {
        'form': form,
        'title': 'Create Task',
        'todo_list': todo_list,
        'from_kanban': 'from_kanban' in request.GET
    })

# Other task views remain largely the same, just update for permissions with shared lists

@login_required
def dashboard(request):
    # Get statistics
    total_tasks = Task.objects.filter(todo_list__user=request.user).count()
    completed_tasks = Task.objects.filter(todo_list__user=request.user, is_completed=True).count()
    incomplete_tasks = total_tasks - completed_tasks
    overdue_tasks = Task.objects.filter(
        todo_list__user=request.user,
        is_completed=False,
        due_date__lt=timezone.now()
    ).count()
    
    # Get recent activity
    recent_tasks = Task.objects.filter(todo_list__user=request.user).order_by('-created_at')[:5]
    upcoming_tasks = Task.objects.filter(
        todo_list__user=request.user,
        is_completed=False,
        due_date__gte=timezone.now()
    ).order_by('due_date')[:5]
    
    # Get lists
    todo_lists = ToDoList.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
        'incomplete_tasks': incomplete_tasks,
        'overdue_tasks': overdue_tasks,
        'recent_tasks': recent_tasks,
        'upcoming_tasks': upcoming_tasks,
        'todo_lists': todo_lists,
    }
    
    return render(request, 'tasks/dashboard.html', context)

# ToDoList views
@login_required
def list_todo_lists(request):
    todo_lists = ToDoList.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'tasks/todo_list/list.html', {'todo_lists': todo_lists})

@login_required
def create_todo_list(request):
    if request.method == 'POST':
        form = ToDoListForm(request.POST)
        if form.is_valid():
            todo_list = form.save(commit=False)
            todo_list.user = request.user
            todo_list.save()
            messages.success(request, 'Todo list created successfully.')
            return redirect('tasks:todo_list_detail', pk=todo_list.pk)
    else:
        form = ToDoListForm()
    
    return render(request, 'tasks/todo_list/form.html', {'form': form, 'title': 'Create Todo List'})

@login_required
def todo_list_detail(request, pk):
    todo_list = get_object_or_404(ToDoList, pk=pk, user=request.user)
    tasks = todo_list.tasks.all().order_by('-created_at')
    return render(request, 'tasks/todo_list/detail.html', {'todo_list': todo_list, 'tasks': tasks})

@login_required
def edit_todo_list(request, pk):
    todo_list = get_object_or_404(ToDoList, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = ToDoListForm(request.POST, instance=todo_list)
        if form.is_valid():
            form.save()
            messages.success(request, 'Todo list updated successfully.')
            return redirect('tasks:todo_list_detail', pk=todo_list.pk)
    else:
        form = ToDoListForm(instance=todo_list)
    
    return render(request, 'tasks/todo_list/form.html', {'form': form, 'title': 'Edit Todo List'})

@login_required
def delete_todo_list(request, pk):
    todo_list = get_object_or_404(ToDoList, pk=pk, user=request.user)
    
    if request.method == 'POST':
        todo_list.delete()
        messages.success(request, 'Todo list deleted successfully.')
        return redirect('tasks:list_todo_lists')
    
    return render(request, 'tasks/todo_list/confirm_delete.html', {'todo_list': todo_list})

# Task views
@login_required
def create_task(request, list_pk):
    todo_list = get_object_or_404(ToDoList, pk=list_pk, user=request.user)
    
    if request.method == 'POST':
        form = TaskForm(request.user, request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.todo_list = todo_list
            task.save()
            
            # Handle many-to-many relationships
            form.save_m2m()
            
            messages.success(request, 'Task created successfully.')
            return redirect('tasks:todo_list_detail', pk=todo_list.pk)
    else:
        form = TaskForm(request.user)
    
    return render(request, 'tasks/task/form.html', {'form': form, 'title': 'Create Task', 'todo_list': todo_list})

@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk, todo_list__user=request.user)
    return render(request, 'tasks/task/detail.html', {'task': task})

@login_required
def edit_task(request, pk):
    task = get_object_or_404(Task, pk=pk, todo_list__user=request.user)
    
    if request.method == 'POST':
        form = TaskForm(request.user, request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task updated successfully.')
            return redirect('tasks:task_detail', pk=task.pk)
    else:
        form = TaskForm(request.user, instance=task)
    
    return render(request, 'tasks/task/form.html', {'form': form, 'title': 'Edit Task', 'task': task})

@login_required
def delete_task(request, pk):
    task = get_object_or_404(Task, pk=pk, todo_list__user=request.user)
    todo_list = task.todo_list
    
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted successfully.')
        return redirect('tasks:todo_list_detail', pk=todo_list.pk)
    
    return render(request, 'tasks/task/confirm_delete.html', {'task': task})

@login_required
def toggle_task_complete(request, pk):
    task = get_object_or_404(Task, pk=pk, todo_list__user=request.user)
    
    if task.is_completed:
        task.mark_incomplete()
        messages.success(request, 'Task marked as incomplete.')
    else:
        task.mark_completed()
        messages.success(request, 'Task marked as complete.')
    
    # Redirect back to referring page
    return redirect(request.META.get('HTTP_REFERER', 'tasks:dashboard'))

# Tag views
@login_required
def list_tags(request):
    tags = Tag.objects.filter(user=request.user).order_by('name')
    return render(request, 'tasks/tag/list.html', {'tags': tags})

@login_required
def create_tag(request):
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            tag = form.save(commit=False)
            tag.user = request.user
            tag.save()
            messages.success(request, 'Tag created successfully.')
            return redirect('tasks:list_tags')
    else:
        form = TagForm()
    
    return render(request, 'tasks/tag/form.html', {'form': form, 'title': 'Create Tag'})

@login_required
def edit_tag(request, pk):
    tag = get_object_or_404(Tag, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = TagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tag updated successfully.')
            return redirect('tasks:list_tags')
    else:
        form = TagForm(instance=tag)
    
    return render(request, 'tasks/tag/form.html', {'form': form, 'title': 'Edit Tag'})

@login_required
def delete_tag(request, pk):
    tag = get_object_or_404(Tag, pk=pk, user=request.user)
    
    if request.method == 'POST':
        tag.delete()
        messages.success(request, 'Tag deleted successfully.')
        return redirect('tasks:list_tags')
    
    return render(request, 'tasks/tag/confirm_delete.html', {'tag': tag})

# Filter and search views
@login_required
def search_tasks(request):
    query = request.GET.get('q', '')
    
    if query:
        tasks = Task.objects.filter(
            Q(todo_list__user=request.user) &
            (Q(title__icontains=query) | Q(description__icontains=query))
        ).order_by('-created_at')
    else:
        tasks = Task.objects.none()
    
    return render(request, 'tasks/task/search_results.html', {'tasks': tasks, 'query': query})

@login_required
def filter_by_tag(request, tag_pk):
    tag = get_object_or_404(Tag, pk=tag_pk, user=request.user)
    tasks = Task.objects.filter(tags=tag, todo_list__user=request.user).order_by('-created_at')
    return render(request, 'tasks/task/filtered_tasks.html', {'tasks': tasks, 'filter_type': f'Tag: {tag.name}'})

@login_required
def filter_overdue(request):
    tasks = Task.objects.filter(
        todo_list__user=request.user,
        is_completed=False,
        due_date__lt=timezone.now()
    ).order_by('due_date')
    return render(request, 'tasks/task/filtered_tasks.html', {'tasks': tasks, 'filter_type': 'Overdue Tasks'})

@login_required
def filter_today(request):
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)
    
    tasks = Task.objects.filter(
        todo_list__user=request.user,
        due_date__gte=timezone.make_aware(datetime.combine(today, datetime.min.time())),
        due_date__lt=timezone.make_aware(datetime.combine(tomorrow, datetime.min.time()))
    ).order_by('due_date')
    
    return render(request, 'tasks/task/filtered_tasks.html', {'tasks': tasks, 'filter_type': 'Today\'s Tasks'})

@login_required
def filter_week(request):
    today = timezone.now().date()
    end_of_week = today + timedelta(days=7)
    
    tasks = Task.objects.filter(
        todo_list__user=request.user,
        due_date__gte=timezone.make_aware(datetime.combine(today, datetime.min.time())),
        due_date__lt=timezone.make_aware(datetime.combine(end_of_week, datetime.min.time()))
    ).order_by('due_date')
    
    return render(request, 'tasks/task/filtered_tasks.html', {'tasks': tasks, 'filter_type': 'This Week\'s Tasks'})