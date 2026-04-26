import time
import os
import warnings

# -------------------------
# System Warning Filters & Environment Configuration
# -------------------------

# Suppress expected RuntimeWarning from Jetson.GPIO during resource cleanup.
# This occurs because hardware pinmux is utilized instead of standard GPIO.setup().
warnings.filterwarnings("ignore", category=RuntimeWarning, module="Jetson.GPIO")

# Suppress C++ backend warnings and debug logs from OpenCV and GStreamer.
# NOTE: These environment variables must be declared strictly before importing cv2.
os.environ["OPENCV_LOG_LEVEL"] = "FATAL"
os.environ["OPENCV_VIDEOIO_DEBUG"] = "0"

import cv2
import pygame
import Jetson.GPIO as GPIO
import signal
import subprocess
import sys
from ultralytics import YOLO
from collections import deque

# -------------------------
# Configuration
# -------------------------
start_alert = "path/to/start_alert.mp3"

MODEL_PATH = "path/to/best.engine"

CONF_THRESHOLD = 0.50
BUFFER_SIZE = 10
RESULT_DELAY = 2.0

CONF_SHUTDOWN_CARD = 0.70
BUFFER_SIZE_SHUTDOWN_CARD = 40
SHUTDOWN_DELAY = 10.0
SHUTDOWN_CLASS = "shutdown_card"

# --- Motion Detection Config ---
MOTION_THRESHOLD = 1500  # Minimum pixel change to trigger wake-up
YOLO_WAKE_DURATION = 2.5 # Duration to keep YOLO awake after motion stops

# -------------------------
# Sound Mapping
# -------------------------
SOUND_MAP = {
    "Recycle Waste": "path/to/recycle.mp3",
    "General Waste": "path/to/general.mp3",
    "Organic Waste": "path/to/organic.mp3",
    "Hazardous Waste": "path/to/hazardous.mp3",
}
SHUTDOWN_SOUND = "path/to/shutdown_alert.mp3"

# -------------------------
# Servo Mapping (Duty Cycles)
# -------------------------
SERVO_MAPPING = {
    "Recycle Waste": (5.0, 7.5),
    "General Waste": (10.5, 1.78),
    "Organic Waste": (10.3, 7.5),
    "Hazardous Waste": (5.0, 1.78),
}

START_POS = (7.5, 4.12)  # (rotate_duty, tilt_duty)

# -------------------------
# Global Flags
# -------------------------
EXITING = False

# -------------------------
# Model Initialization
# -------------------------
model = YOLO(MODEL_PATH, task="detect")

# -------------------------
# GStreamer Pipeline Configuration
# -------------------------
gst_pipeline = (
    "nvarguscamerasrc sensor-id=0 maxperf=true "               # Enable hardware acceleration
    "tnr-mode=2 tnr-strength=1 "
    "ee-mode=2 ee-strength=1.0 "
    "exposurecompensation=-1.0 "
    "ispdigitalgainrange=\"1 1\" "
    "awb-mode=1 "
    "aeantibanding=1 ! "
    "video/x-raw(memory:NVMM), width=1280, height=720 ! "      # Omit framerate to allow auto-negotiation for max FPS
    "nvvidconv flip-method=0 ! "
    "video/x-raw, format=BGRx ! "
    "videoconvert ! "
    "video/x-raw, format=BGR ! "
    "appsink max-buffers=1 drop=true"
)

cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
assert cap.isOpened(), "[ERROR] CSI camera could not be opened."

# -------------------------
# Audio Initialization
# -------------------------
pygame.mixer.init()
channel = pygame.mixer.Channel(0)
SOUNDS = {k: pygame.mixer.Sound(v) for k, v in SOUND_MAP.items()}
SHUTDOWN_SOUND_OBJ = pygame.mixer.Sound(SHUTDOWN_SOUND)
START_ALERT_OBJ = pygame.mixer.Sound(start_alert)

# -------------------------
# Waste Classification Groups
# -------------------------
RECYCLE = {"plastic_bottle", "can", "paper"}
GENERAL = {"plastic_bag", "instant_noodle", "mask"}
ORGANIC = {"banana", "apple", "orange"}
HAZARDOUS = {"battery"}

def get_waste_type(cls):
    """Maps specific object classes to general waste categories."""
    if cls in RECYCLE:
        return "Recycle Waste"
    if cls in GENERAL:
        return "General Waste"
    if cls in ORGANIC:
        return "Organic Waste"
    if cls in HAZARDOUS:
        return "Hazardous Waste"
    return None

# =========================================================
# Servo Motor Control Module
# =========================================================
SERVO_ROTATE_PIN = 32
SERVO_TILT_PIN = 33

servo_rotate = None
servo_tilt = None

class Servo:
    """Safe PWM wrapper for Jetson.GPIO handling explicit start, stop, and duty cycle updates."""
    def __init__(self, pin, freq=50):
        self.pin = pin
        self.freq = freq
        self.pwm = None
        self._started = False
        try:
            self.pwm = GPIO.PWM(pin, freq)
        except Exception as e:
            print(f"[WARN] PWM creation failed on pin {pin}: {e}")
            self.pwm = None

    def start(self, duty=0.0):
        if self.pwm is None:
            return False
        if self._started:
            try:
                self.pwm.ChangeDutyCycle(float(duty))
                return True
            except Exception:
                return False
        try:
            self.pwm.start(float(duty))
            self._started = True
            return True
        except Exception as e:
            print(f"[WARN] PWM start failed on pin {self.pin}: {e}")
            self._started = False
            return False

    def set_duty(self, duty):
        if self.pwm is None or not self._started:
            return False
        try:
            self.pwm.ChangeDutyCycle(float(duty))
            return True
        except Exception:
            return False

    def stop(self):
        if self.pwm is None or not self._started:
            return
        try:
            self.pwm.ChangeDutyCycle(0)
            self.pwm.stop()
        except Exception:
            pass
        self._started = False

# =========================================================
# Finite State Machine (FSM) for Servo Operations
# =========================================================
servo = {"active": False, "step": 0, "start": 0, "duty": None}

def start_servo(waste):
    """Initiates the servo movement cycle based on waste classification."""
    if waste not in SERVO_MAPPING or servo["active"]:
        return
    servo.update(active=True, step=0, start=time.perf_counter(), duty=SERVO_MAPPING[waste])

def update_servo():
    """Updates servo positions asynchronously based on elapsed time."""
    global servo_rotate, servo_tilt
    if not servo["active"] or servo["duty"] is None or servo_rotate is None or servo_tilt is None:
        return
    t = time.perf_counter() - servo["start"]
    rotate_duty, tilt_duty = servo["duty"]

    if servo["step"] == 0 and t >= 0:
        servo_rotate.set_duty(rotate_duty)
        servo["step"] += 1
    elif servo["step"] == 1 and t >= 0.3:
        servo_tilt.set_duty(tilt_duty)
        servo["step"] += 1
    elif servo["step"] == 2 and t >= 1.3:
        servo_tilt.set_duty(START_POS[1])
        servo["step"] += 1
    elif servo["step"] == 3 and t >= 1.7:
        servo_rotate.set_duty(START_POS[0])
        servo["step"] += 1
    elif servo["step"] == 4 and t >= 2.0:  
        # Release rotate servo PWM to mitigate hardware jitter
        servo_rotate.set_duty(0)
        # Complete the cycle and reset active state
        servo["active"] = False

# -------------------------
# Inference & Logic Buffers
# -------------------------
shutdown_buffer = deque(maxlen=BUFFER_SIZE_SHUTDOWN_CARD)
cooldown_until = 0.0
current_class = None
consecutive_count = 0

# -------------------------
# Resource Management & Graceful Exit
# -------------------------
def safe_stop_servos_and_hw():
    """Returns servos to starting positions and cleanly stops PWM signals."""
    global servo_rotate, servo_tilt
    try:
        if servo_tilt is not None:
            servo_tilt.set_duty(START_POS[1])
            time.sleep(0.08)
        if servo_rotate is not None:
            servo_rotate.set_duty(START_POS[0])
            time.sleep(0.08)
    except Exception:
        pass
    
    try:
        if servo_tilt is not None: servo_tilt.stop()
        if servo_rotate is not None: servo_rotate.stop()
    except Exception:
        pass

def cleanup_resources(cap_obj=None):
    """Releases hardware resources including camera, GPIO, and audio systems."""
    try:
        if cap_obj is not None and cap_obj.isOpened():
            cap_obj.release()
        elif 'cap' in globals() and cap is not None and cap.isOpened():
            cap.release()
    except Exception: pass
    
    try: safe_stop_servos_and_hw()
    except Exception: pass
    
    try: GPIO.cleanup()
    except Exception: pass
    
    try: pygame.mixer.quit()
    except Exception: pass
    
    print("[INFO] Resources cleaned successfully.")

def perform_system_shutdown(cap_obj=None, poweroff=True):
    """Executes a system-level shutdown or reboot command after cleanup."""
    global EXITING
    if EXITING: return
    EXITING = True
    
    cleanup_resources(cap_obj)
    time.sleep(0.5)  # Buffer delay for OS level IO clearance
    
    try:
        if poweroff: 
            subprocess.run(["poweroff"], check=True)
        else: 
            subprocess.run(["reboot"], check=True)
    except subprocess.CalledProcessError:
        print("[WARN] Standard poweroff failed, escalating with sudo...")
        try:
            if poweroff: subprocess.run(["sudo", "poweroff"], check=False)
            else: subprocess.run(["sudo", "reboot"], check=False)
        except Exception as e:
            print(f"[ERROR] Failed to issue sudo shutdown: {e}")
    
    sys.exit(0)

def graceful_exit_no_poweroff(exit_code=0):
    global EXITING
    if EXITING: return
    EXITING = True
    cleanup_resources()
    sys.exit(exit_code)

# -------------------------
# Signal Handlers
# -------------------------
def _signal_handler(signum, frame):
    print(f"\n[SYSTEM] Signal {signum} received. Initiating graceful shutdown.")
    graceful_exit_no_poweroff(0)

def _unhandled_exception_hook(exc_type, exc_value, tb):
    print(f"[ERROR] Unhandled exception: {exc_value}")
    graceful_exit_no_poweroff(1)

signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)
try: signal.signal(signal.SIGQUIT, _signal_handler)
except Exception: pass
sys.excepthook = _unhandled_exception_hook

# =========================================================
# Main Application Loop
# =========================================================
def main():
    global servo_rotate, servo_tilt
    global cooldown_until, current_class, consecutive_count
    
    print("[INFO] Initializing FEMTO 1.0...")

    # 1. Initialize GPIO mode
    GPIO.setmode(GPIO.BOARD)

    # 2. Instantiate Servo controllers
    servo_rotate = Servo(SERVO_ROTATE_PIN)
    servo_tilt = Servo(SERVO_TILT_PIN)

    # 3. Position servos to default starting coordinates
    try:
        if servo_rotate.start(START_POS[0]):
            time.sleep(0.05) # Anti-surge startup delay
        if servo_tilt.start(START_POS[1]):
            time.sleep(0.05)
            
        # Allow mechanical movement completion before releasing rotate servo
        time.sleep(0.5)
        servo_rotate.set_duty(0)
    except Exception:
        pass

    # =========================================================
    # System Audio Ready Notification
    # =========================================================
    print("[INFO] FEMTO 1.0 is ready.")
    try:
        channel.play(START_ALERT_OBJ)
        while channel.get_busy():
            time.sleep(0.1) 
    except Exception as e:
        print(f"[WARN] Failed to play startup alert: {e}")

    # --- Variables for Motion Detection ---
    prev_gray = None
    yolo_awake_until = 0.0
    is_yolo_awake = False

    # =========================================================
    # Primary Inference Loop
    # =========================================================
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[WARN] Camera frame dropped.")
                time.sleep(0.05)
                continue

            now = time.perf_counter()

            # --- 1. Motion Detection Processing ---
            # Convert frame to grayscale and apply blur to reduce noise
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

            # Initialize prev_gray on the first loop
            if prev_gray is None:
                prev_gray = gray
                continue

            # Compute absolute difference between current and previous frame
            diff = cv2.absdiff(prev_gray, gray)
            _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
            motion_pixels = cv2.countNonZero(thresh)
            prev_gray = gray  # Update reference frame

            # Trigger Wake-up condition
            if motion_pixels > MOTION_THRESHOLD or servo["active"]:
                yolo_awake_until = now + YOLO_WAKE_DURATION
                if not is_yolo_awake:
                    is_yolo_awake = True

            # Trigger Sleep condition
            if now > yolo_awake_until and is_yolo_awake:
                is_yolo_awake = False
                # Clear inference buffers to prevent phantom detections
                current_class = None
                consecutive_count = 0
                shutdown_buffer.clear()

            # --- 2. YOLO Inference (Executes only when awake) ---
            if is_yolo_awake:
                results = model(frame, conf=CONF_THRESHOLD, verbose=False,)

                classes_in_frame = []
                confs_in_frame = []
                for box in results[0].boxes:
                    cls = model.names[int(box.cls[0])]
                    conf = float(box.conf[0])
                    classes_in_frame.append(cls)
                    confs_in_frame.append(conf)

                # Shutdown card evaluation
                if len(classes_in_frame) == 1 and classes_in_frame[0] == SHUTDOWN_CLASS and confs_in_frame[0] >= CONF_SHUTDOWN_CARD:
                    shutdown_buffer.append(True)
                else:
                    shutdown_buffer.clear()

                if len(shutdown_buffer) == BUFFER_SIZE_SHUTDOWN_CARD:
                    channel.play(SHUTDOWN_SOUND_OBJ)
                    print("[SYSTEM] Consecutive shutdown cards detected. Executing poweroff.")
                    time.sleep(SHUTDOWN_DELAY)
                    perform_system_shutdown(cap, poweroff=True)
                    break

                # Object detection & confidence buffer evaluation
                if now >= cooldown_until:
                    if len(classes_in_frame) > 0:
                        if len(classes_in_frame) > 1:
                            current_class = None
                            consecutive_count = 0
                        else:
                            frame_class = classes_in_frame[0]
                            if current_class is None:
                                current_class = frame_class
                                consecutive_count = 1
                            elif frame_class == current_class:
                                consecutive_count += 1
                            else:
                                current_class = frame_class
                                consecutive_count = 1

                        if consecutive_count >= BUFFER_SIZE:
                            final_cls = current_class
                            waste = get_waste_type(final_cls)
                            
                            if waste:
                                start_servo(waste)
                                try: channel.play(SOUNDS[waste])
                                except Exception: pass
                                cooldown_until = now + RESULT_DELAY
                                
                            current_class = None
                            consecutive_count = 0

            # --- 3. Hardware Updates ---
            # Asynchronous servo update cycle
            update_servo()
            
            time.sleep(0.005)

    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user (KeyboardInterrupt).")
    finally:
        cleanup_resources(cap)

# =========================================================
# Application Entry Point
# =========================================================
if __name__ == "__main__":
    main()