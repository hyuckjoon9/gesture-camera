"""Map MediaPipe canned gesture labels to the small MVP gesture set."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class Gesture(str, Enum):
    NONE = "NONE"
    UNKNOWN = "UNKNOWN"
    THUMBS_UP = "THUMBS_UP"
    VICTORY = "VICTORY"


@dataclass(frozen=True)
class HandGesture:
    handedness: str
    gesture: Gesture
    gesture_score: float
    handedness_score: float


class GestureRecognizer:
    """Classify each MediaPipe-detected hand independently."""

    _CANNED_GESTURES = {
        "None": Gesture.NONE,
        "Thumb_Up": Gesture.THUMBS_UP,
        "Victory": Gesture.VICTORY,
    }

    def recognize(self, detection_result: Any) -> list[HandGesture]:
        """Return one raw gesture result for every detected hand in this frame."""
        hands: list[HandGesture] = []

        for index, landmarks in enumerate(detection_result.hand_landmarks):
            if not landmarks:
                continue

            handedness_category = self._first_category(detection_result.handedness, index)
            gesture_category = self._first_category(detection_result.gestures, index)
            handedness = getattr(handedness_category, "category_name", "Unknown")
            gesture_name = getattr(gesture_category, "category_name", None)
            gesture = self._CANNED_GESTURES.get(gesture_name, Gesture.UNKNOWN)

            hands.append(
                HandGesture(
                    handedness=handedness,
                    gesture=gesture,
                    gesture_score=float(getattr(gesture_category, "score", 0.0)),
                    handedness_score=float(getattr(handedness_category, "score", 0.0)),
                )
            )

        return hands

    @staticmethod
    def _first_category(categories: list[list[Any]], index: int) -> Any | None:
        if index < len(categories) and categories[index]:
            return categories[index][0]
        return None
