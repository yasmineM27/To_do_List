from django import forms
from .models import ToDoList, Task, Tag

class ToDoListForm(forms.ModelForm):
    class Meta:
        model = ToDoList
        fields = ['title', 'description']

class TaskForm(forms.ModelForm):
    due_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M']
    )
    
    class Meta:
        model = Task
        fields = ['title', 'description', 'due_date', 'priority', 'tags']
        widgets = {
            'tags': forms.CheckboxSelectMultiple(),
        }
    
    def __init__(self, user, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        self.fields['tags'].queryset = Tag.objects.filter(user=user)

class TagForm(forms.ModelForm):
    COLOR_CHOICES = [
        ('blue', 'Blue'),
        ('red', 'Red'),
        ('green', 'Green'),
        ('yellow', 'Yellow'),
        ('purple', 'Purple'),
        ('pink', 'Pink'),
        ('orange', 'Orange'),
        ('gray', 'Gray'),
    ]
    
    color = forms.ChoiceField(choices=COLOR_CHOICES)
    
    class Meta:
        model = Tag
        fields = ['name', 'color']