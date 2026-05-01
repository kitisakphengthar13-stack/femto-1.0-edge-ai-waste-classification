import numpy as np

from femto.motion_detector import MotionDetector


def make_detector(pixel_threshold=1):
    return MotionDetector(
        {
            "pixel_threshold": pixel_threshold,
            "frame_diff_threshold": 25,
            "blur_kernel_size": 1,
        }
    )


def test_first_frame_returns_gray_reference_without_motion():
    detector = make_detector()
    frame = np.zeros((2, 2, 3), dtype=np.uint8)

    result = detector.process_frame(frame, prev_gray=None)

    assert result.first_frame is True
    assert result.motion_pixels == 0
    assert result.gray.shape == (2, 2)


def test_frame_difference_counts_changed_pixels():
    detector = make_detector()
    previous = detector.process_frame(np.zeros((2, 2, 3), dtype=np.uint8), None)
    changed_frame = np.full((2, 2, 3), 255, dtype=np.uint8)

    result = detector.process_frame(changed_frame, previous.gray)

    assert result.first_frame is False
    assert result.motion_pixels == 4


def test_even_blur_kernel_is_adjusted_to_odd_value():
    detector = MotionDetector(
        {
            "pixel_threshold": 1,
            "frame_diff_threshold": 25,
            "blur_kernel_size": 2,
        }
    )
    frame = np.zeros((3, 3, 3), dtype=np.uint8)

    result = detector.process_frame(frame, prev_gray=None)

    assert result.first_frame is True
    assert result.gray.shape == (3, 3)


def test_should_wake_yolo_matches_existing_motion_or_servo_rule():
    detector = make_detector(pixel_threshold=10)

    assert detector.should_wake_yolo(motion_pixels=11, servo_active=False) is True
    assert detector.should_wake_yolo(motion_pixels=10, servo_active=False) is False
    assert detector.should_wake_yolo(motion_pixels=0, servo_active=True) is True
