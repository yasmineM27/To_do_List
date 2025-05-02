from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages

class CustomLoginView(LoginView):
    template_name = 'core/login.html'
    redirect_authenticated_user = True

def home(request):
    if request.user.is_authenticated:
        return redirect('tasks:dashboard')
    return render(request, 'core/home.html')

def register(request):
    if request.user.is_authenticated:
        return redirect('tasks:dashboard')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created successfully. You can now log in.')
            return redirect('core:login')
        else:
            messages.error(request, 'There was a problem with your registration. Please correct the errors below.')
    else:
        form = UserCreationForm()
    
    return render(request, 'core/register.html', {'form': form})

@login_required
def profile(request):
    return render(request, 'core/profile.html')