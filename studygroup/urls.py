
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login', views.login_view, name='login'),
    path('logout', views.logout_view, name='logout'),
    path('register', views.register, name='register'),
    path('groups', views.groups, name='groups'),
    path('mygroup', views.mygroup, name='mygroup'),
    path('create', views.create, name='create'),
    path('profile', views.profile, name='profile'),

    # Chat function
    path('chat', views.chat, name='chat'),
    path('chat/<int:gid>', views.chatroom, name='chatroom'),

    # API calls
    path('join/<int:gid>', views.join, name='join'),
    path('leave/<int:gid>', views.leave, name='leave'),
    path('edit/<int:gid>', views.edit, name='edit'),
]