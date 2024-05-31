import sys  # Ensure the sys module is imported
import json
import logging
import threading
import time
from azure.eventhub import EventHubConsumerClient

CONNECTION_STR = "key"
EVENTHUB_NAME = "name"

# Set up logging
logger = logging.getLogger("EventHubReceiver")
logger.setLevel(logging.WARNING)  # Set the logging level to WARNING to reduce output

# Create a StreamHandler for the logger
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setStream(sys.stdout)
    ch.setLevel(logging.INFO)  # Change this to INFO to see info-level logs
    ch.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s]: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(ch)

# Global dictionary to store the data
data_table = {}

class EventHubReceiver:
    def __init__(self, connection_str, eventhub_name):
        self.connection_str = connection_str
        self.eventhub_name = eventhub_name
        self.consumer_client = EventHubConsumerClient.from_connection_string(
            conn_str=self.connection_str,
            consumer_group="$Default",
            eventhub_name=self.eventhub_name,
        )
        self.stop_sig = threading.Event()
        self.stop_sig.clear()

    def on_event(self, partition_context, event):
        data = event.body_as_str()
        
        # Preprocess the data to handle escaped quotes
        data = data.replace('\\"', '"')

        # Split the data into separate lines
        lines = data.strip().split('\n')
        for line in lines:
            try:
                item = json.loads(line)
                key = item.get("key")
                value = item.get("value")
                if not key:
                    logger.warning("packet format error.")
                    continue

                global data_table
                data_table[key] = value
                logger.info(f"Updated data_table: {data_table}")
            except json.decoder.JSONDecodeError:
                logger.warning(f"packet format error: {line}")

    def start(self):
        with self.consumer_client:
            self.consumer_client.receive(
                on_event=self.on_event,
                starting_position="@latest",  # "@latest" is from the latest position.
            )

    def stop(self):
        self.stop_sig.set()
        logger.info("Stopped.")

    def startThreaded(self):
        self.t = threading.Thread(target=self.start)
        self.t.start()

    def get(self, key):
        global data_table
        return data_table.get(key)

if __name__ == "__main__":
    try:
        eventhub_receiver = EventHubReceiver(CONNECTION_STR, EVENTHUB_NAME)
        eventhub_receiver.startThreaded()
        while True:
            print(eventhub_receiver.get("/joint/0"))  # Replace with the actual key you are using
            print(eventhub_receiver.get("/joint/1"))  # Replace with the actual key you are using
            time.sleep(1)
    except KeyboardInterrupt:
        eventhub_receiver.stop()
        logger.info("Received KeyboardInterrupt, stopped.")
