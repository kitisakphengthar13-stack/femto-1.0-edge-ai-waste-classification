from femto.shutdown_detection import ShutdownCardDetector


def make_detector(buffer_size=3):
    return ShutdownCardDetector(
        class_name="shutdown_card",
        confidence_threshold=0.7,
        buffer_size=buffer_size,
    )


def test_shutdown_card_confirms_after_consecutive_matches():
    detector = make_detector(buffer_size=3)

    assert detector.update(["shutdown_card"], [0.7]) is False
    assert detector.update(["shutdown_card"], [0.8]) is False
    assert detector.update(["shutdown_card"], [0.9]) is True


def test_low_confidence_detection_clears_buffer():
    detector = make_detector(buffer_size=2)

    assert detector.update(["shutdown_card"], [0.9]) is False
    assert detector.update(["shutdown_card"], [0.69]) is False
    assert detector.update(["shutdown_card"], [0.9]) is False


def test_non_shutdown_or_multiple_classes_clear_buffer():
    detector = make_detector(buffer_size=2)

    assert detector.update(["shutdown_card"], [0.9]) is False
    assert detector.update(["can"], [0.9]) is False
    assert detector.update(["shutdown_card"], [0.9]) is False
    assert detector.update(["shutdown_card", "can"], [0.9, 0.8]) is False
    assert detector.update(["shutdown_card"], [0.9]) is False


def test_reset_clears_confirmation_buffer():
    detector = make_detector(buffer_size=2)

    detector.update(["shutdown_card"], [0.9])
    detector.reset()

    assert detector.update(["shutdown_card"], [0.9]) is False
