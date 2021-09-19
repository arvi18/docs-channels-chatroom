from django.contrib.auth import get_user_model
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json
from .models import Message

User = get_user_model()

class ChatConsumer(WebsocketConsumer):

    def fetch_messages(self, data):
        messages = Message.last_10_messages() # <QuerySet [<Message: admin>]> from db
        content = {  #dict of list of dict
            'command': 'messages',
            'messages': self.messages_to_json(messages) #pass those and get result list having messages in dict
        }
        print('content:', content)
        self.send_message(content)

    def new_message(self, data):  #data=content
        author = data['from']
        author_user = User.objects.filter(username=author)[0]
        message = Message.objects.create(
            author=author_user,
            content=data['message'])
        content = {
            'command': 'new_message',
            'message': self.message_to_json(message)
        }
        return self.send_chat_message(content)

    def messages_to_json(self, messages): #return list of messages
        result = []
        for message in messages:
            result.append(self.message_to_json(message))  #append dict of all 3 fields for each message  
        return result

    def message_to_json(self, message): #convert db objects to json
        return {
            'id': message.id,
            'author': message.author.username,
            'content': message.content,
            'timestamp': str(message.timestamp)
        }

    commands = {
        'fetch_messages': fetch_messages,
        'new_message': new_message
    }

    def connect(self):
        
        self.room_name = self.scope['url_route']['kwargs']['room_name']# Handshake # get <roomname> from scope of socket req       
        self.room_group_name = 'chat_%s' % self.room_name # naming room name as <chat_ <roomname> >
        async_to_sync(self.channel_layer.group_add)(    # adding <roomname> and <chat_<roomname> >
            self.room_group_name,
            self.channel_name
        )
        
        self.accept() # upgrading to sockets

    def disconnect(self, close_code): # dissolving group
            async_to_sync(self.channel_layer.group_discard)(
                self.room_group_name,
                self.channel_name
            )

    def receive(self, text_data): #json  #{"command":"new_message","message":"the message is to _","from":"admin"}
        print('text_data:', text_data)
        data = json.loads(text_data)  #dict   #{'command': 'new_message', 'message': 'the message is to _', 'from': 'admin'}
        # calling fetch_messages or new_message accepting data
        self.commands[data['command']](self, data)  #### avoidable stylish code ####

    def send_chat_message(self, message):
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    def send_message(self, message):  #send content to socket in json
        self.send(text_data=json.dumps(message))  #dict to json

    def chat_message(self, event):
        message = event['message']
        self.send(text_data=json.dumps(message))