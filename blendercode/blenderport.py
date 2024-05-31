import serial
import json
import threading
import time
import logging

class UARTCommunicator:
    def __init__(self, port, baudrate=115200, logging_level=None):
        self.serial_connection = None
        self.port = port
        self.baudrate = baudrate
        self.data_table = {}
        self.stop_signal = threading.Event()
        self.logger = logging.getLogger("UARTComm")
        if logging_level:
            self.logger.setLevel(logging_level)
        self.connect()

    def connect(self):
        while True:
            try:
                self.serial_connection = serial.Serial(self.port, self.baudrate)
                if self.serial_connection.is_open:
                    break
            except serial.SerialException:
                time.sleep(1)
                continue
        self.logger.info("Connected.")

    def stop(self):
        self.stop_signal.set()
        if self.serial_connection:
            self.serial_connection.close()
        self.logger.info("Stopped.")

    def start(self):
        self.logger.debug("Starting...")
        self.receive_packet()

    def start_threaded(self):
        self.logger.debug("Starting thread...")
        self.thread = threading.Thread(target=self.receive_packet)
        self.thread.start()

    def get(self, key):
        return self.data_table.get(key)

    def receive_packet(self):
        while True:
            if self.stop_signal.is_set():
                return

            char = b""
            buffer = b""
            while char != b"\n":
                if self.stop_signal.is_set():
                    return
                buffer += char
                try:
                    char = self.serial_connection.read()
                except (AttributeError, TypeError, serial.serialutil.SerialException) as e:
                    print(e)
                    self.connect()
                    continue

            data = buffer.decode()
            try:
                data = json.loads(data)
            except json.decoder.JSONDecodeError:
                self.logger.warning("Packet format error.")
                continue

            key = data.get("key")
            if not key:
                self.logger.warning("Packet format error.")
                continue

            self.data_table[key] = data.get("value")

if __name__ == "__main__":
    try:
        uart_right_arm = UARTCommunicator("COM7", logging_level=logging.DEBUG)
        uart_left_arm = UARTCommunicator("COM9", logging_level=logging.DEBUG)
        
        uart_right_arm.start_threaded()
        uart_left_arm.start_threaded()

        while True:
            joint_right_upper = uart_right_arm.get("/joint/0")
            joint_right_lower = uart_right_arm.get("/joint/1")
            joint_left_upper = uart_left_arm.get("/joint/2")
            joint_left_lower = uart_left_arm.get("/joint/3")
            
            print(f'joint_right_upper: {joint_right_upper}, joint_right_lower: {joint_right_lower}, joint_left_upper: {joint_left_upper}, joint_left_lower: {joint_left_lower}')
            
            time.sleep(0.01)
    except KeyboardInterrupt:
        uart_right_arm.stop()
        uart_left_arm.stop()
