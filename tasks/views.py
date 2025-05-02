from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
from .models import ToDoList, Task, Tag
from .forms import ToDoListForm, TaskForm, TagForm

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