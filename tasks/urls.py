from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # ToDo Lists
    path('lists/', views.list_todo_lists, name='list_todo_lists'),
    path('lists/create/', views.create_todo_list, name='create_todo_list'),
    path('lists/<int:pk>/', views.todo_list_detail, name='todo_list_detail'),
    path('lists/<int:pk>/edit/', views.edit_todo_list, name='edit_todo_list'),
    path('lists/<int:pk>/delete/', views.delete_todo_list, name='delete_todo_list'),
    
    # Tasks
    path('lists/<int:list_pk>/tasks/create/', views.create_task, name='create_task'),
    path('tasks/<uuid:pk>/', views.task_detail, name='task_detail'),
    path('tasks/<uuid:pk>/edit/', views.edit_task, name='edit_task'),
    path('tasks/<uuid:pk>/delete/', views.delete_task, name='delete_task'),
    path('tasks/<uuid:pk>/toggle-complete/', views.toggle_task_complete, name='toggle_task_complete'),
    
    # Tags
    path('tags/', views.list_tags, name='list_tags'),
    path('tags/create/', views.create_tag, name='create_tag'),
    path('tags/<int:pk>/edit/', views.edit_tag, name='edit_tag'),
    path('tags/<int:pk>/delete/', views.delete_tag, name='delete_tag'),
    
    # Filters
    path('search/', views.search_tasks, name='search_tasks'),
    path('tasks/filter/tag/<int:tag_pk>/', views.filter_by_tag, name='filter_by_tag'),
    path('tasks/filter/overdue/', views.filter_overdue, name='filter_overdue'),
    path('tasks/filter/today/', views.filter_today, name='filter_today'),
    path('tasks/filter/week/', views.filter_week, name='filter_week'),
]