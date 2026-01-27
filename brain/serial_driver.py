import serial
import threading
import queue
import time
import sys


class SerialDriver:
    def __init__(self, config):
        """
        Initializes the Serial connection and starts the background read thread.
        :param config: Dictionary containing 'port' and 'baud_rate'.
        """
        self.port = config["serial"]["port"]
        self.baud = config["serial"]["baud_rate"]
        self.timeout = config["serial"]["timeout"]

        self.event_queue = queue.Queue()
        self.running = False
        self.ser = None
        self.thread = None

        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=self.timeout)
            # DTR toggle often resets Arduino, ensuring a fresh start
            self.ser.dtr = False
            time.sleep(0.1)
            self.ser.dtr = True
            time.sleep(2.0)  # Wait for Arduino bootloader
            self.ser.reset_input_buffer()
            print(f"[SERIAL] Connected to {self.port}")
        except serial.SerialException as e:
            print(f"[SERIAL] Critical Error: Could not open port {self.port}")
            print(e)
            sys.exit(1)

        # Start background reader
        self.running = True
        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()

    def _read_loop(self):
        """
        Background thread: Continually reads lines from serial.
        Parses 'TYPE:VALUE' or 'TYPE:ARG1:ARG2' into tuples.
        """
        while self.running:
            try:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode("utf-8", errors="ignore").strip()
                    if not line:
                        continue

                    # Protocol: TYPE:DATA or TYPE:ID:DATA
                    parts = line.split(":")

                    if len(parts) >= 2:
                        event_type = parts[0]
                        # Join the rest in case data contains colons (unlikely but safe)
                        event_data = ":".join(parts[1:])
                        self.event_queue.put((event_type, event_data))
                        # print(f"[DEBUG RX] {line}") # Uncomment for raw debug

            except serial.SerialException:
                print("[SERIAL] Connection lost!")
                self.running = False
                break
            except Exception as e:
                print(f"[SERIAL] Read Error: {e}")
                time.sleep(0.1)

    def send(self, cmd_type, action, value):
        """
        Sends a command to Arduino.
        Example: send("MOV", "FWD", "1000") -> "MOV:FWD:1000\n"
        """
        if not self.ser or not self.ser.is_open:
            return

        msg = f"{cmd_type}:{action}:{value}\n"
        try:
            self.ser.write(msg.encode("utf-8"))
            # print(f"[DEBUG TX] {msg.strip()}") # Uncomment for raw debug
        except serial.SerialException:
            print("[SERIAL] Write Failed")

    def get_event(self):
        """
        Non-blocking pop from event queue.
        Returns (type, data) or None.
        """
        try:
            return self.event_queue.get_nowait()
        except queue.Empty:
            return None

    def close(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        if self.ser:
            self.ser.close()
        print("[SERIAL] Closed.")
