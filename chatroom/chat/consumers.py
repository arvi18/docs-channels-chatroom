# chat/consumers.py
import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        # Obtains the 'room_name' parameter from the URL route in chat/routing.py that opened the WebSocket connection to the consumer.
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        # Constructs a Channels group name directly from the user-specified room name, without any quoting or escaping.
        self.room_group_name = 'chat_%s' % self.room_name

        # Join room group
        # ChatConsumer is a synchronous WebsocketConsumer but it is calling an asynchronous channel layer method. (All channel layer methods are asynchronous.) so async_to_sync(…) wrapper is required.
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        # Accepts the WebSocket connection.
        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            # event has a special 'type' key corresponding to the name of the method that should be invoked on consumers that receive the event.
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    # Receive message from room group
    def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': message
        }))