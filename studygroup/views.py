from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, JsonResponse
from django.db import IntegrityError
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django import forms
from django.core.paginator import Paginator

from datetime import datetime
import json

from .models import User, Group

# I guess this form automatically resolves the timezone issue.
class MyForm(forms.Form):
    name            = forms.CharField(min_length=2, max_length=32, required=True, widget=forms.TextInput)
    description     = forms.CharField(max_length=256, required=False, widget=forms.Textarea)
    max_size        = forms.IntegerField(min_value=1, max_value=20, required=True)
    start           = forms.DateTimeField(required=True, input_formats=['%Y-%m-%dT%H:%M'])
    end             = forms.DateTimeField(required=True, input_formats=['%Y-%m-%dT%H:%M'])

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['profile_pic']
# Create your views here.

def index(request):
    return render(request, 'studygroup/index.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse('index'))
        else:
            return render(request, 'studygroup/login.html', {
                'message': 'Incorrect email and/or password'
            })
    else:
        return render(request, 'studygroup/login.html')
    
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('index'))

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirmation = request.POST['confirmation']

        # Check confirmation password, should do it at front-end
        if password != confirmation:
            return render(request, 'studygroup/register.html', {
                'message': 'Password and confirmation must match.'
            })
        
        # Check username
        # Attempt to create new user
        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()
        except:
            return render(request, "studygroup/register.html", {
                "message": "Username and/or e-mail already taken."
            })
        
        login(request, user)
        return HttpResponseRedirect(reverse('index'))
    else:
        return render(request, 'studygroup/register.html')

def groups(request):
    if request.method == "POST":
        txt = request.POST['txt']
        groups = Group.objects.filter(name__icontains=txt).order_by("-timestamp")
    else:
        groups = Group.objects.all().order_by("-timestamp")
    
    paginator = Paginator(groups, 12)
    page_number = request.GET.get('page')
    if page_number:
        page_obj = paginator.get_page(page_number)
    else:
        page_obj = paginator.get_page(1)
    numbers = range(1, paginator.num_pages + 1)

    return render(request, "studygroup/groups.html", {
        "page_obj": page_obj,
        "numbers": numbers
    })

@login_required
def mygroup(request):
    current_user = request.user
    owned_groups = Group.objects.filter(creator=current_user).order_by("-timestamp")
    # groups excluding owned ones
    groups = Group.objects.filter(participants__in=[current_user]).exclude(creator=current_user).order_by("-timestamp")
    
    paginator = Paginator(groups, 12)
    page_number = request.GET.get('page')
    if page_number:
        page_obj = paginator.get_page(page_number)
    else:
        page_obj = paginator.get_page(1)
    numbers = range(1, paginator.num_pages + 1)
    return render(request, "studygroup/mygroup.html", {
        "owned_groups": owned_groups,
        "page_obj": page_obj,
        "numbers": numbers
    })
    
@login_required
def create(request):
    if request.method == 'POST':
        form = MyForm(request.POST)
        current_user = request.user
        if form.is_valid():
            name = form.cleaned_data['name']
            description = form.cleaned_data['description']
            max_size = form.cleaned_data['max_size']
            start = form.cleaned_data['start']
            end = form.cleaned_data['end']
        else:
            return render(request, 'studygroup/create.html', {
                'message': 'Form invalid.',
                'form': form,
            })
        
        if start >= end:
            return render(request, 'studygroup/create.html', {
                'message': 'End time cannot precedes start time.',
                'form': form,
            })
        
        now = datetime.now(timezone.utc)
        if now >= start:
            return render(request, 'studygroup/create.html', {
                'message': 'Start time must be after current time.',
                'form': form,
            })

        if Group.objects.filter(creator=current_user).count() >= 3:
            return render(request, 'studygroup/create.html', {
                'message': 'Limit for creating groups reached (3).',
                'form': form,
            })
        
        group = Group(
            name=name,
            description=description,
            creator=current_user,
            max_size=max_size,
            start=start,
            end=end,
        )

        group.save()
        group.participants.add(current_user)
        return HttpResponseRedirect(reverse('mygroup'))
    return render(request, 'studygroup/create.html')


@login_required
def chat(request):
    current_user = request.user
    groups = Group.objects.filter(participants__in=[current_user]).order_by("-timestamp")
    return render(request, 'studygroup/chat.html', {
        "groups": groups,
    })

@login_required
def chatroom(request, gid):
    current_user = request.user
    groups = Group.objects.filter(participants__in=[current_user]).order_by("-timestamp")
    try:
        group = Group.objects.get(id=gid)
    except:
        return render(request, 'studygroup/chat.html', {
            "message": "Group chat not found.",
            "groups": groups
        })
    
    return render(request, 'studygroup/chat.html', {
        "groups": groups,
        "gid": gid        
    })

@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return render(request, 'studygroup/profile.html', {
                'message': 'Upload successfully!'
            })
    return render(request, 'studygroup/profile.html')

# API Calls

@login_required
def join(request, gid):
    current_user = request.user
    try:
        group = Group.objects.get(id=gid)
    except:
        return JsonResponse({
            "error": "Group ID invalid."
        }, status=404)
    
    if group.creator == current_user:
        return JsonResponse({
            "error": "Creator cannot join group."
        }, status=404)
    
    if current_user in group.participants.all():
        return JsonResponse({
            "error": "User already joined group."
        }, status=404)
    
    if group.current_size == group.max_size:
        return JsonResponse({
            "error": "Group is full."
        }, status=404)
    
    group.current_size += 1
    group.save()
    group.participants.add(current_user)
    
    return JsonResponse({
        "message": "Successfully joined group!"
    }, status=200)


@login_required
def leave(request, gid):
    current_user = request.user
    try:
        group = Group.objects.get(id=gid)
    except:
        return JsonResponse({
            "error": "Group ID invalid."
        }, status=404)
    
    if group.creator == current_user:
        return JsonResponse({
            "error": "Creator cannot leave group. Delete instead."
        }, status=404)
    
    if current_user not in group.participants.all():
        return JsonResponse({
            "error": "User already left group."
        }, status=404)

    group.current_size -= 1
    group.save()
    group.participants.remove(current_user)

    return JsonResponse({
        "message": "Successfully left group!"
    }, status=200)

@login_required
def edit(request, gid):
    if request.method == "POST":
        current_user = request.user

        data = json.loads(request.body)
        name = data['name']
        description = data['description']
        max_size = data['max_size']

        start_datetime = datetime.strptime(data['start'], "%Y-%m-%dT%H:%M")
        start = timezone.make_aware(start_datetime, timezone.get_default_timezone())
        end_datetime = datetime.strptime(data['end'], "%Y-%m-%dT%H:%M")
        end = timezone.make_aware(end_datetime, timezone.get_default_timezone())

        try:
            group = Group.objects.get(id=gid)
        except:
            return JsonResponse({
                "error": "Group ID invalid."
            }, status=404)
        
        if current_user != group.creator:
            return JsonResponse({
                "error": "Only creator can edit group."
            }, status=404)

        if start >= end:
            return JsonResponse({
                'error': 'End time cannot precede start time.'
            }, status=404)
        
        now = datetime.now(timezone.utc)
        if now >= start:
            return JsonResponse({
                'error': 'Start time must be after current time.'
            }, status=404)
        
        if int(max_size) < group.current_size:
            return JsonResponse({
                'error': 'Max size must be greater than current size.'
            }, status=404)

        group.name = name
        group.description = description
        group.max_size = max_size
        group.start = start
        group.end = end
        group.save()

        output = group.serialize()
        output['message'] = 'Edit Successfully!'
        return JsonResponse(output, status=200)
    return JsonResponse({
        "error": "Request error."
    }, status=404)