from dataclasses import dataclass


@dataclass(frozen=True)
class DecisionResult:
    final_class: str | None = None
    waste_type: str | None = None
    should_sort: bool = False


class WasteDecisionBuffer:
    """Consecutive-class decision buffer for waste sorting decisions."""

    def __init__(
        self,
        buffer_size: int,
        allow_multiple_objects: bool,
        waste_classes: dict[str, str],
        special_classes: dict[str, str] | None = None,
    ):
        self.buffer_size = buffer_size
        self.allow_multiple_objects = allow_multiple_objects
        self.waste_classes = waste_classes
        self.special_classes = special_classes or {}

        self.current_class = None
        self.consecutive_count = 0

    def update(self, classes_in_frame: list[str]) -> DecisionResult:
        if len(classes_in_frame) == 0:
            return DecisionResult()

        if len(classes_in_frame) > 1 and not self.allow_multiple_objects:
            self.reset()
            return DecisionResult()

        frame_class = classes_in_frame[0]

        if frame_class in self.special_classes:
            return DecisionResult()

        if self.current_class is None:
            self.current_class = frame_class
            self.consecutive_count = 1

        elif frame_class == self.current_class:
            self.consecutive_count += 1

        else:
            self.current_class = frame_class
            self.consecutive_count = 1

        if self.consecutive_count < self.buffer_size:
            return DecisionResult()

        final_class = self.current_class
        waste_type = self.waste_classes.get(final_class)
        self.reset()

        if waste_type:
            return DecisionResult(
                final_class=final_class,
                waste_type=waste_type,
                should_sort=True,
            )

        return DecisionResult(final_class=final_class)

    def reset(self) -> None:
        self.current_class = None
        self.consecutive_count = 0
