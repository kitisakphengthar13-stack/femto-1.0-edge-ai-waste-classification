from femto.decision_buffer import WasteDecisionBuffer


def make_buffer(buffer_size=2, allow_multiple_objects=False):
    return WasteDecisionBuffer(
        buffer_size=buffer_size,
        allow_multiple_objects=allow_multiple_objects,
        waste_classes={
            "can": "Recycle Waste",
            "battery": "Hazardous Waste",
        },
        special_classes={
            "shutdown_card": "shutdown",
        },
    )


def test_consecutive_same_class_triggers_sorting_decision():
    decision_buffer = make_buffer(buffer_size=2)

    first = decision_buffer.update(["can"])
    second = decision_buffer.update(["can"])

    assert first.should_sort is False
    assert second.should_sort is True
    assert second.final_class == "can"
    assert second.waste_type == "Recycle Waste"


def test_class_change_restarts_consecutive_count():
    decision_buffer = make_buffer(buffer_size=2)

    decision_buffer.update(["can"])
    changed = decision_buffer.update(["battery"])
    final = decision_buffer.update(["battery"])

    assert changed.should_sort is False
    assert final.should_sort is True
    assert final.final_class == "battery"
    assert final.waste_type == "Hazardous Waste"


def test_no_detection_preserves_current_consecutive_count():
    decision_buffer = make_buffer(buffer_size=2)

    decision_buffer.update(["can"])
    empty = decision_buffer.update([])
    final = decision_buffer.update(["can"])

    assert empty.should_sort is False
    assert final.should_sort is True
    assert final.waste_type == "Recycle Waste"


def test_multiple_objects_reset_when_not_allowed():
    decision_buffer = make_buffer(buffer_size=2)

    decision_buffer.update(["can"])
    multiple = decision_buffer.update(["can", "battery"])
    after_reset = decision_buffer.update(["can"])

    assert multiple.should_sort is False
    assert after_reset.should_sort is False


def test_multiple_objects_use_first_class_when_allowed():
    decision_buffer = make_buffer(buffer_size=2, allow_multiple_objects=True)

    decision_buffer.update(["can", "battery"])
    final = decision_buffer.update(["can", "battery"])

    assert final.should_sort is True
    assert final.final_class == "can"
    assert final.waste_type == "Recycle Waste"


def test_special_class_does_not_reset_existing_count():
    decision_buffer = make_buffer(buffer_size=2)

    decision_buffer.update(["can"])
    special = decision_buffer.update(["shutdown_card"])
    final = decision_buffer.update(["can"])

    assert special.should_sort is False
    assert final.should_sort is True


def test_unmapped_class_resets_after_threshold_without_sorting():
    decision_buffer = make_buffer(buffer_size=2)

    decision_buffer.update(["unknown"])
    result = decision_buffer.update(["unknown"])
    after_reset = decision_buffer.update(["unknown"])

    assert result.should_sort is False
    assert result.final_class == "unknown"
    assert result.waste_type is None
    assert after_reset.should_sort is False
