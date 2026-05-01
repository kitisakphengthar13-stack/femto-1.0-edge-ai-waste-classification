from dataclasses import dataclass

import cv2


@dataclass(frozen=True)
class MotionResult:
    first_frame: bool
    gray: object
    motion_pixels: int


class MotionDetector:
    """Frame-difference motion detector used to decide when YOLO should wake."""

    def __init__(self, motion_config: dict):
        self.pixel_threshold = motion_config["pixel_threshold"]
        self.frame_diff_threshold = motion_config.get("frame_diff_threshold", 25)
        self.blur_kernel_size = motion_config.get("blur_kernel_size", 21)

    def process_frame(self, frame, prev_gray) -> MotionResult:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        blur_kernel_size = self.blur_kernel_size

        if blur_kernel_size % 2 == 0:
            blur_kernel_size += 1

        gray = cv2.GaussianBlur(gray, (blur_kernel_size, blur_kernel_size), 0)

        if prev_gray is None:
            return MotionResult(
                first_frame=True,
                gray=gray,
                motion_pixels=0,
            )

        diff = cv2.absdiff(prev_gray, gray)

        _, thresh = cv2.threshold(
            diff,
            self.frame_diff_threshold,
            255,
            cv2.THRESH_BINARY,
        )

        motion_pixels = cv2.countNonZero(thresh)

        return MotionResult(
            first_frame=False,
            gray=gray,
            motion_pixels=motion_pixels,
        )

    def should_wake_yolo(self, motion_pixels: int, servo_active: bool) -> bool:
        return motion_pixels > self.pixel_threshold or servo_active
