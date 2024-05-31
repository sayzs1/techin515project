import os
from azure.eventhub import EventHubConsumerClient

CONNECTION_STR = "key"
EVENTHUB_NAME = "name"

consumer_client = EventHubConsumerClient.from_connection_string(
    conn_str=CONNECTION_STR,
    consumer_group="$Default",
    eventhub_name=EVENTHUB_NAME,
)


def on_event(partition_context, event):
    print("Received event from partition: {}.".format(partition_context.partition_id))
    print("Event properties: {}".format(event.properties))
    print("Event body: {}".format(event.body_as_str()))


try:
    with consumer_client:
        consumer_client.receive(
            on_event=on_event,
            starting_position="@latest",  
        )
except KeyboardInterrupt:
    print("Stopped receiving.")