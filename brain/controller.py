import time
import sys
from input_parser import InputParser

# --- State Constants ---
STATE_IDLE = "IDLE"  # Waiting at Home
STATE_LOADING = "LOADING"  # User putting items in
STATE_INPUT = "INPUT"  # User typing destination
STATE_MOVING = "MOVING"  # Driving to destination
STATE_DELIVERY = "DELIVERY"  # At destination, waiting for receiver
STATE_RETURNING = "RETURNING"  # Driving back to Home


class RobotController:
    """
    The 'Brain' of the operation.
    Responsibility: Manages the State Machine, coordinates components,
    and handles high-level business logic (Auth, Database Lookups).
    """

    def __init__(self, serial, hal, navigator, rooms_db, config):
        self.serial = serial
        self.hal = hal
        self.nav = navigator
        self.rooms = rooms_db
        self.config = config

        self.parser = InputParser()
        self.state = STATE_IDLE

        # Mission Context Variables
        self.active_box_id = None
        self.target_room_code = None

        # Initial Hardware Setup
        self.hal.set_servo(1, "LOCK")
        self.hal.set_servo(2, "LOCK")
        self.hal.lcd_write("SYSTEM READY", "Scan ID to Load")
        print("[CTRL] System Initialized. State: IDLE")

    def run(self):
        """
        The Main Loop.
        """
        try:
            while True:
                # 1. Fetch Event
                event = self.serial.get_event()

                # 2. Process Event (if any)
                if event:
                    etype, edata = event
                    self.handle_event(etype, edata)

                # 3. Prevent CPU Spin
                time.sleep(0.05)

        except KeyboardInterrupt:
            print("[CTRL] Shutdown requested.")
            self.hal.stop()
            self.serial.close()

    def handle_event(self, etype, edata):
        """
        Dispatches events to the correct handler based on current state.
        :param etype: String (e.g., "RFD", "KEY", "LMT")
        :param edata: String payload
        """
        if etype == "RFD":
            self._handle_rfid(edata)

        elif etype == "KEY":
            if self.state == STATE_INPUT:
                self._handle_input_key(edata)

        elif etype == "LMT":
            # LMT format: "ID:STATE" (e.g., "1:1")
            parts = edata.split(":")
            if len(parts) == 2:
                box_id = int(parts[0])
                is_pressed = parts[1] == "1"
                self._handle_limit_switch(box_id, is_pressed)

    # =========================================================
    # STATE-SPECIFIC HANDLERS
    # =========================================================

    def _handle_rfid(self, uid):
        print(f"[CTRL] RFID Scanned: {uid} in state {self.state}")

        # 1. Logic for IDLE (Sender Auth)
        if self.state == STATE_IDLE:
            user = self._find_user_by_rfid(uid)
            if user:
                self.hal.lcd_write("Hello User", "Open Box 1 & 2")
                self.hal.set_servo(1, "OPEN")
                self.hal.set_servo(2, "OPEN")
                self.state = STATE_LOADING
                print("[CTRL] Transition -> LOADING")
            else:
                self.hal.lcd_write("ACCESS DENIED", "Unknown ID")
                time.sleep(2)
                self.hal.lcd_write("SYSTEM READY", "Scan ID to Load")

        # 2. Logic for DELIVERY (Receiver Auth)
        elif self.state == STATE_DELIVERY:
            target_room = self.rooms.get(self.target_room_code)
            if target_room and target_room["rfid_uid"] == uid:
                self.hal.lcd_write("ACCESS GRANTED", f"Taking Box {self.active_box_id}")
                self.hal.set_servo(self.active_box_id, "OPEN")
                # We stay in DELIVERY state until they close the box
            else:
                self.hal.lcd_write("WRONG BADGE", "Try Again")

    def _handle_input_key(self, key):
        """
        Feeds the keypad press into the parser and checks for completion.
        """
        self.parser.push_key(key)

        # Update LCD
        self.hal.lcd_write("Dest Input:", self.parser.get_display_text())

        # Check result
        result = self.parser.get_parsed_result()
        if result:
            self._finalize_input(result)

    def _finalize_input(self, result):
        """
        Validates the parsed input against the database and starts the mission.
        """
        box_id = result["box_id"]
        room_code = result["room_code"]

        if room_code in self.rooms:
            self.active_box_id = box_id
            self.target_room_code = room_code

            self.hal.lcd_write("Confirmed:", f"Room {room_code}")
            time.sleep(2)
            self._start_mission_move(room_code)
        else:
            self.hal.lcd_write("INVALID ROOM", "Try Again")
            time.sleep(2)
            self.parser.clear()
            self.hal.lcd_write("Dest Input:", "")

    def _handle_limit_switch(self, box_id, is_closed):
        """
        Handles box closing events.
        """
        if is_closed:
            print(f"[CTRL] Box {box_id} Closed. Locking.")
            self.hal.set_servo(box_id, "LOCK")

            # Transition Logic
            if self.state == STATE_LOADING:
                # If loading, closing a box moves us to Input
                self.state = STATE_INPUT
                self.parser.clear()
                self.hal.lcd_write("Enter Dest:", "[Box]D[Room]DD")
                print("[CTRL] Transition -> INPUT")

            elif self.state == STATE_DELIVERY:
                # If delivered, closing the box means they took the item
                if box_id == self.active_box_id:
                    self.hal.lcd_write("Delivery Done", "Returning Home")
                    time.sleep(2)
                    self._return_home()

    # =========================================================
    # MOVEMENT & WORKFLOW HELPERS
    # =========================================================

    def _start_mission_move(self, room_code):
        self.state = STATE_MOVING
        coords = self.rooms[room_code]["coords"]

        self.hal.lcd_write("En Route...", f"To {room_code}")

        # Execute Blocking Move
        success = self.nav.goto(coords)

        if success:
            self.state = STATE_DELIVERY
            self.hal.lcd_write("ARRIVED", "Scan Badge")
            print("[CTRL] Transition -> DELIVERY")
        else:
            self.hal.lcd_write("PATH BLOCKED", "Returning...")
            time.sleep(2)
            self._return_home()

    def _return_home(self):
        self.state = STATE_RETURNING
        home_coords = self.config["map_settings"]["home_node"]

        # Execute Blocking Move
        self.nav.goto(home_coords)

        # Reset to IDLE
        self.state = STATE_IDLE
        self.active_box_id = None
        self.target_room_code = None
        self.hal.lcd_write("SYSTEM READY", "Scan ID to Load")
        print("[CTRL] Transition -> IDLE")

    def _find_user_by_rfid(self, uid):
        """
        Helper to lookup user in database.
        """
        for code, data in self.rooms.items():
            if data.get("rfid_uid") == uid:
                return data
        return None
