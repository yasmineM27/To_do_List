from django import forms
from django.contrib.auth.models import User
from .models import ToDoList, Task, Tag, Invitation

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
        fields = ['title', 'description', 'due_date', 'priority', 'status', 'tags']
        widgets = {
            'tags': forms.CheckboxSelectMultiple(),
            'status': forms.Select(attrs={'class': 'form-select'}),
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

# New forms for collaboration features
class ShareListForm(forms.Form):
    email = forms.EmailField(label="User's Email")
    
    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            raise forms.ValidationError("No user with this email exists in the system.")
        return email

class InvitationResponseForm(forms.ModelForm):
    class Meta:
        model = Invitation
        fields = ['status']
        widgets = {
            'status': forms.RadioSelect(choices=[
                ('accepted', 'Accept'),
                ('declined', 'Decline'),
            ])
        }
