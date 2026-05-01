from collections import deque


class ShutdownCardDetector:
    """Consecutive shutdown-card confirmation buffer."""

    def __init__(self, class_name: str, confidence_threshold: float, buffer_size: int):
        self.class_name = class_name
        self.confidence_threshold = confidence_threshold
        self.buffer = deque(maxlen=buffer_size)

    def update(self, classes_in_frame: list[str], confs_in_frame: list[float]) -> bool:
        is_shutdown_detected = (
            len(classes_in_frame) == 1
            and classes_in_frame[0] == self.class_name
            and confs_in_frame[0] >= self.confidence_threshold
        )

        if is_shutdown_detected:
            self.buffer.append(True)
        else:
            self.buffer.clear()

        return len(self.buffer) == self.buffer.maxlen

    def reset(self) -> None:
        self.buffer.clear()
