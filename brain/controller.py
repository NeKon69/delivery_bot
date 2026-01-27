import time
from input_parser import InputParser

STATE_IDLE = "IDLE"
STATE_LOADING = "LOADING"
STATE_INPUT = "INPUT"
STATE_MOVING = "MOVING"
STATE_DELIVERY = "DELIVERY"
STATE_RETURNING = "RETURNING"


class RobotController:
    def __init__(self, serial, hal, navigator, rooms_db, config):
        self.serial = serial
        self.hal = hal
        self.nav = navigator
        self.rooms = rooms_db
        self.config = config
        self.parser = InputParser()
        self.state = STATE_IDLE
        self.active_box_id = None
        self.target_room_code = None

        self.hal.set_servo(1, "LOCK")
        self.hal.set_servo(2, "LOCK")
        self.hal.lcd_write("SYSTEM READY", "Scan ID to Load")

    def run(self):
        try:
            while True:
                event = self.serial.get_event()
                if event:
                    etype, edata = event
                    self.handle_event(etype, edata)
                time.sleep(0.05)
        except KeyboardInterrupt:
            self.hal.stop()
            self.serial.close()

    def handle_event(self, etype, edata):
        if etype == "RFD":
            self._handle_rfid(edata)
        elif etype == "KEY" and self.state == STATE_INPUT:
            self._handle_input_key(edata)
        elif etype == "LMT":
            parts = edata.split(":")
            if len(parts) == 2:
                self._handle_limit_switch(int(parts[0]), parts[1] == "1")

    def _handle_rfid(self, uid):
        if self.state == STATE_IDLE:
            user = self._find_user_by_rfid(uid)
            if user:
                is_admin = user.get("role") == "admin"
                # Запоминаем, какой ящик мы открыли, чтобы потом ждать его закрытия
                self.active_box_id = 1

                if is_admin:
                    print(f"[LOG] Admin {uid} opening all boxes")
                    self.hal.lcd_write("Hello ADMIN", "Open Box 1 & 2")
                    self.hal.set_servo(1, "OPEN")
                    self.hal.set_servo(2, "OPEN")
                else:
                    print(f"[LOG] User {uid} opening Box 1")
                    self.hal.lcd_write("Hello User", "Open Box 1")
                    self.hal.set_servo(1, "OPEN")

                self.state = STATE_LOADING
            else:
                self.hal.lcd_write("Access Denied", "Unknown ID")
                time.sleep(2)
                self.hal.lcd_write("SYSTEM READY", "Scan ID to Load")

        elif self.state == STATE_DELIVERY:
            target_room = self.rooms.get(self.target_room_code)
            user = self._find_user_by_rfid(uid)
            is_admin = user and user.get("role") == "admin"

            if is_admin or (target_room and target_room["rfid_uid"] == uid):
                print(
                    f"[LOG] Access granted for delivery at room {self.target_room_code}"
                )
                self.hal.lcd_write("ACCESS GRANTED", "Pls Remove Item")
                self.hal.set_servo(self.active_box_id, "OPEN")
            else:
                self.hal.lcd_write("Access Denied", "Try Again")

    def _handle_input_key(self, key):
        self.parser.push_key(key)
        self.hal.lcd_write("Dest Input:", self.parser.get_display_text())

        if self.parser.is_complete:
            result = self.parser.get_parsed_result()
            if result:
                self._finalize_input(result)
            else:
                self.hal.lcd_write("Invalid Syntax", "Try Again")
                time.sleep(2)
                self.parser.clear()

    def _finalize_input(self, result):
        if result["room_code"] in self.rooms:
            self.active_box_id = result["box_id"]
            self.target_room_code = result["room_code"]
            self.hal.lcd_write("Confirmed:", f"Room {self.target_room_code}")
            time.sleep(2)
            self._start_mission_move(self.target_room_code)
        else:
            self.hal.lcd_write("Invalid Room", "Try Again")  # Синхронизировано
            time.sleep(2)
            self.parser.clear()
            self.hal.lcd_write("Dest Input:", "")

    def _handle_limit_switch(self, box_id, is_closed):
        if is_closed:
            print(f"[LOG] Limit Switch: Box {box_id} CLOSED")
            self.hal.set_servo(box_id, "LOCK")

            if self.state == STATE_LOADING:
                self.state = STATE_INPUT
                self.parser.clear()
                self.hal.lcd_write("Enter Dest:", "[Box]D[Room]DD")

            elif self.state == STATE_DELIVERY:
                # Если active_box_id не задан (глюк или тест), берем box_id из события
                if self.active_box_id is None or box_id == self.active_box_id:
                    print(f"[LOG] Delivery finished for box {box_id}. Returning home.")
                    self.hal.lcd_write("Delivery Done", "Returning Home")
                    time.sleep(2)
                    self._return_home()
                else:
                    print(
                        f"[LOG] Warning: Box {box_id} closed, but active box is {self.active_box_id}"
                    )

    def _start_mission_move(self, room_code):
        self.state = STATE_MOVING
        coords = self.rooms[room_code]["coords"]
        print(f"[LOG] Starting mission to {room_code} at {coords}")

        self.hal.lcd_write("En Route...", f"To {room_code}")

        if self.nav.goto(coords):
            print(f"[LOG] Arrival at {room_code} successful")
            self.state = STATE_DELIVERY
            self.hal.lcd_write("Arrived", "Scan Badge")
        else:
            print(f"[LOG] Mission to {room_code} FAILED. Path blocked.")
            self.hal.lcd_write("PATH BLOCKED", "Returning...")
            time.sleep(2)
            self._return_home()

    def _return_home(self):
        self.state = STATE_RETURNING
        home_coords = self.config["map_settings"]["home_node"]

        print(f"[LOG] Navigating to Home: {home_coords}")
        if self.nav.goto(home_coords):
            print("[LOG] Home reached.")
            self.state = STATE_IDLE
            self.active_box_id = None
            self.hal.lcd_write("SYSTEM READY", "Scan ID to Load")
        else:
            print("[LOG] ERROR: Path to home is blocked!")
            self.hal.lcd_write("Home Error", "Path Blocked")

    def _find_user_by_rfid(self, uid):
        for data in self.rooms.values():
            if data.get("rfid_uid") == uid:
                return data
        return None
