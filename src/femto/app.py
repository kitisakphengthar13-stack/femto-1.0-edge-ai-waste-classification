import os
import signal
import subprocess
import sys
import time
import warnings

# Suppress expected RuntimeWarning from Jetson.GPIO during resource cleanup.
warnings.filterwarnings("ignore", category=RuntimeWarning, module="Jetson.GPIO")

# These must be set before importing cv2.
os.environ["OPENCV_LOG_LEVEL"] = "FATAL"
os.environ["OPENCV_VIDEOIO_DEBUG"] = "0"

import cv2
import pygame
import Jetson.GPIO as GPIO
from ultralytics import YOLO

from femto.class_mapper import ClassMapper
from femto.decision_buffer import WasteDecisionBuffer
from femto.motion_detector import MotionDetector
from femto.servo_controller import ServoController
from femto.shutdown_detection import ShutdownCardDetector


class FemtoApp:
    """
    Main runtime application for FEMTO 1.0.

    Responsibilities:
    - Initialize YOLO model
    - Open CSI camera
    - Initialize audio
    - Initialize servo controller
    - Run motion-triggered inference loop
    - Handle shutdown card
    - Control sorting action
    - Cleanup hardware resources safely
    """

    def __init__(self, system_config: dict, mapping_config: dict):
        self.config = system_config
        self.mapping_config = mapping_config

        self.model_config = system_config["model"]
        self.decision_config = system_config["decision"]
        self.shutdown_config = system_config["shutdown"]
        self.motion_config = system_config["motion"]
        self.camera_config = system_config["camera"]
        self.audio_config = system_config["audio"]
        self.servo_config = system_config["servo"]
        self.runtime_config = system_config["runtime"]

        self.class_mapper = ClassMapper(mapping_config)
        self.servo_controller = ServoController(self.servo_config)
        self.motion_detector = MotionDetector(self.motion_config)
        self.decision_buffer = WasteDecisionBuffer(
            buffer_size=self.decision_config["buffer_size"],
            allow_multiple_objects=self.decision_config.get("allow_multiple_objects", False),
            waste_classes=mapping_config["waste_classes"],
            special_classes=mapping_config.get("special_classes", {}),
        )
        self.shutdown_detector = ShutdownCardDetector(
            class_name=self.shutdown_config["class_name"],
            confidence_threshold=self.shutdown_config["confidence_threshold"],
            buffer_size=self.shutdown_config["buffer_size"],
        )

        self.model = None
        self.cap = None

        self.channel = None
        self.sounds = {}
        self.shutdown_sound = None
        self.startup_sound = None

        self.cooldown_until = 0.0

        self.exiting = False

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        print("[INFO] Initializing FEMTO 1.0...")

        self._register_signal_handlers()
        self._initialize_model()
        self._initialize_camera()
        self._initialize_audio()
        self.servo_controller.initialize()

        print("[INFO] FEMTO 1.0 is ready.")
        self._play_startup_alert()

    def _initialize_model(self) -> None:
        self.model = YOLO(
            self.model_config["path"],
            task=self.model_config.get("task", "detect"),
        )

    def _initialize_camera(self) -> None:
        gst_pipeline = self._build_gstreamer_pipeline()
        self.cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)

        if not self.cap.isOpened():
            raise RuntimeError("[ERROR] CSI camera could not be opened.")

    def _build_gstreamer_pipeline(self) -> str:
        sensor_id = self.camera_config.get("sensor_id", 0)
        width = self.camera_config.get("width", 1280)
        height = self.camera_config.get("height", 720)
        flip_method = self.camera_config.get("flip_method", 0)

        return (
            f"nvarguscamerasrc sensor-id={sensor_id} maxperf=true "
            "tnr-mode=2 tnr-strength=1 "
            "ee-mode=2 ee-strength=1.0 "
            "exposurecompensation=-1.0 "
            "ispdigitalgainrange=\"1 1\" "
            "awb-mode=1 "
            "aeantibanding=1 ! "
            f"video/x-raw(memory:NVMM), width={width}, height={height} ! "
            f"nvvidconv flip-method={flip_method} ! "
            "video/x-raw, format=BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=BGR ! "
            "appsink max-buffers=1 drop=true"
        )

    def _initialize_audio(self) -> None:
        pygame.mixer.init()
        self.channel = pygame.mixer.Channel(0)

        category_sounds = self.audio_config.get("category_sounds", {})

        self.sounds = {
            waste_type: pygame.mixer.Sound(sound_path)
            for waste_type, sound_path in category_sounds.items()
        }

        shutdown_sound_path = self.shutdown_config.get("sound_path")
        startup_sound_path = self.audio_config.get("startup_alert")

        if shutdown_sound_path:
            self.shutdown_sound = pygame.mixer.Sound(shutdown_sound_path)

        if startup_sound_path:
            self.startup_sound = pygame.mixer.Sound(startup_sound_path)

    def _play_startup_alert(self) -> None:
        if self.channel is None or self.startup_sound is None:
            return

        try:
            self.channel.play(self.startup_sound)
            while self.channel.get_busy():
                time.sleep(0.1)
        except Exception as exc:
            print(f"[WARN] Failed to play startup alert: {exc}")

    # ------------------------------------------------------------------
    # Runtime Loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        self.initialize()

        prev_gray = None
        yolo_awake_until = 0.0
        is_yolo_awake = False

        try:
            while True:
                ret, frame = self.cap.read()

                if not ret:
                    print("[WARN] Camera frame dropped.")
                    time.sleep(
                        self.runtime_config.get("camera_drop_sleep_seconds", 0.05)
                    )
                    continue

                now = time.perf_counter()

                motion_result = self._process_motion(frame, prev_gray)
                prev_gray = motion_result["gray"]

                if motion_result["first_frame"]:
                    continue

                motion_pixels = motion_result["motion_pixels"]

                if self.motion_detector.should_wake_yolo(motion_pixels, self.servo_controller.active):
                    yolo_awake_until = now + self.motion_config["yolo_awake_duration_seconds"]
                    is_yolo_awake = True

                if now > yolo_awake_until and is_yolo_awake:
                    is_yolo_awake = False
                    self._reset_inference_buffers()

                if is_yolo_awake:
                    self._run_inference_cycle(frame, now)

                self.servo_controller.update()

                time.sleep(self.runtime_config.get("loop_sleep_seconds", 0.005))

        except KeyboardInterrupt:
            print("\n[INFO] Interrupted by user (KeyboardInterrupt).")
        finally:
            self.cleanup_resources()

    def _process_motion(self, frame, prev_gray):
        motion_result = self.motion_detector.process_frame(frame, prev_gray)

        return {
            "first_frame": motion_result.first_frame,
            "gray": motion_result.gray,
            "motion_pixels": motion_result.motion_pixels,
        }

    def _run_inference_cycle(self, frame, now: float) -> None:
        results = self.model(
            frame,
            conf=self.model_config["confidence_threshold"],
            verbose=False,
        )

        classes_in_frame = []
        confs_in_frame = []

        for box in results[0].boxes:
            class_name = self.model.names[int(box.cls[0])]
            confidence = float(box.conf[0])

            classes_in_frame.append(class_name)
            confs_in_frame.append(confidence)

        self._handle_shutdown_card(classes_in_frame, confs_in_frame)

        if now >= self.cooldown_until:
            self._handle_waste_detection(classes_in_frame, now)

    def _handle_shutdown_card(self, classes_in_frame: list[str], confs_in_frame: list[float]) -> None:
        if self.shutdown_detector.update(classes_in_frame, confs_in_frame):
            self._play_shutdown_sound()
            print("[SYSTEM] Consecutive shutdown cards detected. Executing poweroff.")
            time.sleep(self.shutdown_config["delay_seconds"])
            self.perform_system_shutdown(poweroff=True)

    def _handle_waste_detection(self, classes_in_frame: list[str], now: float) -> None:
        decision_result = self.decision_buffer.update(classes_in_frame)

        if decision_result.should_sort and decision_result.waste_type:
            self.servo_controller.start_sorting(decision_result.waste_type)
            self._play_category_sound(decision_result.waste_type)
            self.cooldown_until = now + self.decision_config["result_delay_seconds"]

    # ------------------------------------------------------------------
    # Audio
    # ------------------------------------------------------------------

    def _play_category_sound(self, waste_type: str) -> None:
        if self.channel is None:
            return

        sound = self.sounds.get(waste_type)

        if sound is None:
            return

        try:
            self.channel.play(sound)
        except Exception:
            pass

    def _play_shutdown_sound(self) -> None:
        if self.channel is None or self.shutdown_sound is None:
            return

        try:
            self.channel.play(self.shutdown_sound)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Cleanup / Shutdown
    # ------------------------------------------------------------------

    def _reset_inference_buffers(self) -> None:
        self.decision_buffer.reset()
        self.shutdown_detector.reset()

    def cleanup_resources(self) -> None:
        try:
            if self.cap is not None and self.cap.isOpened():
                self.cap.release()
        except Exception:
            pass

        try:
            self.servo_controller.stop_safe()
        except Exception:
            pass

        try:
            GPIO.cleanup()
        except Exception:
            pass

        try:
            pygame.mixer.quit()
        except Exception:
            pass

        print("[INFO] Resources cleaned successfully.")

    def perform_system_shutdown(self, poweroff: bool = True) -> None:
        if self.exiting:
            return

        self.exiting = True
        self.cleanup_resources()

        time.sleep(0.5)

        try:
            if poweroff:
                subprocess.run(["poweroff"], check=True)
            else:
                subprocess.run(["reboot"], check=True)

        except subprocess.CalledProcessError:
            print("[WARN] Standard shutdown command failed, escalating with sudo...")

            try:
                if poweroff:
                    subprocess.run(["sudo", "poweroff"], check=False)
                else:
                    subprocess.run(["sudo", "reboot"], check=False)

            except Exception as exc:
                print(f"[ERROR] Failed to issue sudo shutdown/reboot: {exc}")

        sys.exit(0)

    def graceful_exit_no_poweroff(self, exit_code: int = 0) -> None:
        if self.exiting:
            return

        self.exiting = True
        self.cleanup_resources()
        sys.exit(exit_code)

    def _register_signal_handlers(self) -> None:
        def signal_handler(signum, frame):
            print(f"\n[SYSTEM] Signal {signum} received. Initiating graceful shutdown.")
            self.graceful_exit_no_poweroff(0)

        def unhandled_exception_hook(exc_type, exc_value, traceback):
            print(f"[ERROR] Unhandled exception: {exc_value}")
            self.graceful_exit_no_poweroff(1)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            signal.signal(signal.SIGQUIT, signal_handler)
        except Exception:
            pass

        sys.excepthook = unhandled_exception_hook
