from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# Create your models here.
class User(AbstractUser):
    profile_pic     = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    def __str__(self):
        return f"{self.username}"
    
class Group(models.Model):
    name            = models.CharField(max_length=32)
    description     = models.TextField(max_length=128, blank=True)
    creator         = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_groups")
    participants    = models.ManyToManyField(User, related_name="joined_groups")
    current_size    = models.IntegerField(default=1)
    max_size        = models.IntegerField(default=1)
    timestamp       = models.DateTimeField(auto_now_add=True)
    edited          = models.BooleanField(default=False)
    start           = models.DateTimeField()
    end             = models.DateTimeField()

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "creator": self.creator.username,
            "participants": [participant.username for participant in self.participants.all()],
            "current_size": self.current_size,
            "max_size": self.max_size,
            "timestamp": self.timestamp.strftime("%H:%M, %m/%d/%Y"),
            "edited": self.edited,
            "start": self.start.strftime("%H:%M, %m/%d/%Y"),
            "end": self.end.strftime("%H:%M, %m/%d/%Y"),
        }
    

class Message(models.Model):
    value       = models.TextField(max_length=1024)
    timestamp   = models.DateTimeField(auto_now_add=True)
    sender      = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    group       = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="group_messages")

    def __str__(self):
        return self.sender.username
    
    def serialize(self):
        # Get sender's profile picture's URL
        if self.sender.profile_pic != None:
            profile_pic_url = self.sender.profile_pic.url
        else:
            profile_pic_url = None
        
        # Change into UTC-5 timezone manually
        local_time = timezone.localtime(self.timestamp, timezone=timezone.get_fixed_timezone(-300))

        return {
            "sender": self.sender.username,
            "profile_pic_url": profile_pic_url,
            "value": self.value,
            "timestamp": local_time.strftime("%H:%M, %m/%d/%Y"),
            "group": self.group.name,
        }

    @classmethod
    def recent_messages(self, gid):
        return Message.objects.filter(group__id=gid).order_by("timestamp").all()[:20]
