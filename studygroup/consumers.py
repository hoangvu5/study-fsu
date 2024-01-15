# class where WebSocket connections are handled

from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
from asgiref.sync import async_to_sync
import json
from .models import Message, User, Group

class ChatConsumer(WebsocketConsumer):

    # Serialize multiple messages
    def messages_serialize(self, messages):
        result = []
        for message in messages:
            result.append(message.serialize())
        return result

    # Fetch recent messages (10) and return
    def fetch_messages(self, data):
        group_id = int(data['gid'])
        messages = Message.recent_messages(group_id)
        content = {
            "command": "messages",
            "messages": self.messages_serialize(messages)
        }
        self.send(text_data=json.dumps(content))
        
    # Create new Message object and return
    def new_message(self, data):
        # Retrieve data about group and sender from request
        sender_id = int(data['uid'])
        group_id = int(data['gid'])
        sender = User.objects.get(id=sender_id)
        group = Group.objects.get(id=group_id)

        # Create Message object
        message = Message.objects.create(
            sender=sender,
            group=group,
            value=data['message']
        )

        content = {
            "command": "new_message",
            "message": message.serialize()
        }
        return self.send_chat_message(content)
        
    commands = {
        'fetch_messages': fetch_messages,
        'new_message': new_message,
    }

    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['gid']
        self.room_group_name = self.room_name
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def receive(self, text_data):
        data = json.loads(text_data)
        self.commands[data['commands']](self, data)
    
    # For many users
    def send_chat_message(self, message):
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    # For one user for a specific event
    def chat_message(self, event):
        message = event['message']
        self.send(text_data=json.dumps(message))

    """
    async def connect(self):
        # self.room_group_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'test'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        print(message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    async def chat_message(self, event):
        message = event['message']

        await self.send(text_data=json.dumps({
            'type': 'chat',
            'message': message
        }))
    """

""" Synchronous ChatConsumer: call regular synchronous I/O functions such as
those that access Django models without writing special code

If it went asynchonous, can still use utils such as
- asgiref.sync.sync_to_async
- channels.db.database_sync_to_async
to call sync code from an async consumer
"""