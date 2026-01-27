import math


class RobotHAL:
    """
    Hardware Abstraction Layer (HAL).
    Responsibility: Translates high-level intent (Drive 1 Block) into
    low-level protocol commands with voltage compensation.
    """

    def __init__(self, serial_driver, config):
        """
        :param serial_driver: Instance of SerialDriver (or Mock)
        :param config: Dictionary containing 'calibration' key.
        """
        self.serial = serial_driver
        self.cal = config.get("calibration", {})

        # Cache calibration values with defaults if missing
        self.time_block = self.cal.get("time_move_1_grid_ms", 1000)
        self.time_turn = self.cal.get("time_turn_90_ms", 800)
        self.scalar = self.cal.get("voltage_scalar", 1.0)

    def _apply_scalar(self, base_duration_ms):
        """
        Adjusts timing based on battery voltage scalar.
        Returns: int
        """
        return int(base_duration_ms * self.scalar)

    def drive_forward(self):
        """
        Sends command to move forward one grid unit.
        Returns: int (The duration in ms the move will take)
        """
        duration = self._apply_scalar(self.time_block)
        if self.serial:
            self.serial.send("MOV", "FWD", duration)
        return duration

    def turn(self, direction):
        """
        Turns 90 degrees.
        :param direction: 'LEFT' or 'RIGHT'
        Returns: int (The duration in ms)
        """
        duration = self._apply_scalar(self.time_turn)
        cmd = "LFT" if direction == "LEFT" else "RGT"

        if self.serial:
            self.serial.send("MOV", cmd, duration)
        return duration

    def stop(self):
        """Emergency Stop"""
        if self.serial:
            self.serial.send("MOV", "STP", "0")

    def set_servo(self, box_id, state):
        """
        :param box_id: 1 or 2
        :param state: 'OPEN' or 'LOCK'
        """
        if self.serial:
            self.serial.send("SRV", str(box_id), state)

    def lcd_write(self, line1, line2=""):
        """
        Updates LCD screen. Truncates to 16 chars to ensure protocol safety.
        """
        # Truncate and sanitize
        l1 = str(line1)[:16]
        l2 = str(line2)[:16]

        if self.serial:
            self.serial.send("LCD", "CLS", "0")
            self.serial.send("LCD", "0", l1)
            if l2:
                self.serial.send("LCD", "1", l2)

    def update_voltage_scalar(self, new_scalar):
        """
        Runtime calibration update (e.g. if we add a voltage sensor later).
        """
        self.scalar = new_scalar
        # Update internal config cache just in case
        self.cal["voltage_scalar"] = new_scalar
