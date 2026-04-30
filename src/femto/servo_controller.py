import time

import Jetson.GPIO as GPIO


class Servo:
    """
    Safe PWM wrapper for Jetson.GPIO.

    Handles:
    - PWM creation
    - PWM start
    - duty cycle update
    - safe stop
    """

    def __init__(self, pin: int, freq: int = 50):
        self.pin = pin
        self.freq = freq
        self.pwm = None
        self._started = False

        try:
            self.pwm = GPIO.PWM(pin, freq)
        except Exception as exc:
            print(f"[WARN] PWM creation failed on pin {pin}: {exc}")
            self.pwm = None

    def start(self, duty: float = 0.0) -> bool:
        if self.pwm is None:
            return False

        if self._started:
            return self.set_duty(duty)

        try:
            self.pwm.start(float(duty))
            self._started = True
            return True
        except Exception as exc:
            print(f"[WARN] PWM start failed on pin {self.pin}: {exc}")
            self._started = False
            return False

    def set_duty(self, duty: float) -> bool:
        if self.pwm is None or not self._started:
            return False

        try:
            self.pwm.ChangeDutyCycle(float(duty))
            return True
        except Exception:
            return False

    def stop(self) -> None:
        if self.pwm is None or not self._started:
            return

        try:
            self.pwm.ChangeDutyCycle(0)
            self.pwm.stop()
        except Exception:
            pass

        self._started = False


class ServoController:
    """
    Non-blocking servo finite-state machine for FEMTO 1.0.

    Flow:
    1. Rotate to target bin position
    2. Tilt to release waste
    3. Return tilt to home
    4. Return rotation to home
    5. Release rotate PWM to reduce jitter
    """

    def __init__(self, servo_config: dict):
        self.config = servo_config

        self.rotate_pin = servo_config["rotate_pin"]
        self.tilt_pin = servo_config["tilt_pin"]
        self.frequency = servo_config.get("pwm_frequency", 50)

        self.start_position = servo_config["start_position"]
        self.category_positions = servo_config["category_positions"]
        self.timing = servo_config["timing"]

        self.rotate_servo: Servo | None = None
        self.tilt_servo: Servo | None = None

        self.active = False
        self.step = 0
        self.start_time = 0.0
        self.target_position: dict | None = None

    def initialize(self) -> None:
        GPIO.setmode(GPIO.BOARD)

        self.rotate_servo = Servo(self.rotate_pin, self.frequency)
        self.tilt_servo = Servo(self.tilt_pin, self.frequency)

        rotate_home = self.start_position["rotate_duty"]
        tilt_home = self.start_position["tilt_duty"]

        try:
            if self.rotate_servo.start(rotate_home):
                time.sleep(0.05)

            if self.tilt_servo.start(tilt_home):
                time.sleep(0.05)

            time.sleep(self.timing.get("startup_delay_seconds", 0.5))

            if self.timing.get("release_rotate_pwm", True):
                self.rotate_servo.set_duty(0)

        except Exception as exc:
            print(f"[WARN] Servo initialization failed: {exc}")

    def start_sorting(self, waste_type: str) -> None:
        if self.active:
            return

        if waste_type not in self.category_positions:
            print(f"[WARN] No servo mapping for waste type: {waste_type}")
            return

        self.active = True
        self.step = 0
        self.start_time = time.perf_counter()
        self.target_position = self.category_positions[waste_type]

    def update(self) -> None:
        if not self.active or self.target_position is None:
            return

        if self.rotate_servo is None or self.tilt_servo is None:
            return

        elapsed = time.perf_counter() - self.start_time

        rotate_duty = self.target_position["rotate_duty"]
        tilt_duty = self.target_position["tilt_duty"]

        home_rotate = self.start_position["rotate_duty"]
        home_tilt = self.start_position["tilt_duty"]

        rotate_step_seconds = self.timing.get("rotate_step_seconds", 0.3)
        tilt_return_seconds = self.timing.get("tilt_return_seconds", 1.3)
        rotate_return_seconds = self.timing.get("rotate_return_seconds", 1.7)
        cycle_done_seconds = self.timing.get("cycle_done_seconds", 2.0)

        if self.step == 0:
            self.rotate_servo.set_duty(rotate_duty)
            self.step += 1

        elif self.step == 1 and elapsed >= rotate_step_seconds:
            self.tilt_servo.set_duty(tilt_duty)
            self.step += 1

        elif self.step == 2 and elapsed >= tilt_return_seconds:
            self.tilt_servo.set_duty(home_tilt)
            self.step += 1

        elif self.step == 3 and elapsed >= rotate_return_seconds:
            self.rotate_servo.set_duty(home_rotate)
            self.step += 1

        elif self.step == 4 and elapsed >= cycle_done_seconds:
            if self.timing.get("release_rotate_pwm", True):
                self.rotate_servo.set_duty(0)

            self.active = False
            self.target_position = None

    def stop_safe(self) -> None:
        try:
            if self.tilt_servo is not None:
                self.tilt_servo.set_duty(self.start_position["tilt_duty"])
                time.sleep(0.08)

            if self.rotate_servo is not None:
                self.rotate_servo.set_duty(self.start_position["rotate_duty"])
                time.sleep(0.08)

        except Exception:
            pass

        try:
            if self.tilt_servo is not None:
                self.tilt_servo.stop()

            if self.rotate_servo is not None:
                self.rotate_servo.stop()

        except Exception:
            pass