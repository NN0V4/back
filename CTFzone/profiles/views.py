import uuid
import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import UniversityLoginForm, UniversitySignUpForm

# Traditional Signup View (Django Templates)
def signup_view(request):
    form = UniversitySignUpForm(request.POST or None)
    
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']

        if User.objects.filter(username=email).exists():
            messages.error(request, "This email is already registered.")
        else:
            user = User.objects.create_user(username=email, email=email, password=password)
            user.is_active = True
            user.save()

            token = str(uuid.uuid4())
            user.profile.verification_token = token
            user.profile.verification_sent_at = timezone.now()
            user.profile.save()

            confirmation_link = request.build_absolute_uri(reverse('confirm_email', args=[token, email]))
            email_content = render_to_string('profiles/email.html', {'confirmation_link': confirmation_link})

            send_mail(
                subject='Email Confirmation',
                message='',
                from_email='ctfzone99@gmail.com',
                recipient_list=[email],
                html_message=email_content
            )
            messages.success(request, 'Verification email sent! Please check your inbox.')
            return redirect('signup')

    return render(request, 'profiles/signup.html', {'form': form})


# API-based Signup for React Frontend
@csrf_exempt
def signup_api(request):
    if request.method == "POST":
        try:
            # Parse JSON data
            data = json.loads(request.body)
            email = data.get("email")
            password = data.get("password")

            # Validate input
            if not email or not password:
                return JsonResponse({"error": "Email and password are required."}, status=400)

            # Check if user already exists
            if User.objects.filter(username=email).exists():
                return JsonResponse({"error": "This email is already registered."}, status=400)

            # Create user
            user = User.objects.create_user(username=email, email=email, password=password)
            user.is_active = True  # Set the user as active
            user.save()

            return JsonResponse({"message": "Signup successful!"}, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid HTTP method. Use POST."}, status=405)


# Confirm Email View
def confirm_email(request, token, email):
    try:
        user = User.objects.get(email=email)
        if user.profile.verification_token == token:
            user.is_active = True
            user.save()
            user.profile.verification_token = None
            user.profile.save()
            messages.success(request, 'Your email has been confirmed.')
            return redirect('signup')
        else:
            messages.error(request, 'Invalid confirmation link.')
    except User.DoesNotExist:
        messages.error(request, 'Invalid confirmation link.')
    return redirect('signup')


# Login View
def login_view(request):
    form = UniversityLoginForm(request.POST or None)
    
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        
        try:
            user = User.objects.get(email=email)
            user_auth = authenticate(request, username=user.username, password=password)
            
            if user_auth is not None:
                login(request, user_auth)
                return redirect('home')
            else:
                messages.error(request, "Invalid email or password.")
        
        except User.DoesNotExist:
            messages.error(request, "No account with this email exists.")
    
    return render(request, 'profiles/login.html', {'form': form})


# Logout View
def logout_view(request):
    logout(request)
    return redirect('home')
