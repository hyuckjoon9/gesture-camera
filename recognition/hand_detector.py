"""MediaPipe Gesture Recognizer wrapper that receives OpenCV frames."""

from __future__ import annotations

from pathlib import Path
import time
from typing import Any

import cv2
import mediapipe as mp


HAND_CONNECTIONS = (
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (0, 17), (17, 18), (18, 19), (19, 20),
)


class HandDetector:
    """Run MediaPipe on BGR frames supplied by the existing CameraCapture."""

    def __init__(
        self,
        model_path: Path,
        max_num_hands: int = 2,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ) -> None:
        self.model_path = model_path
        self.max_num_hands = max_num_hands
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self._recognizer: Any | None = None
        self._last_timestamp_ms = -1

    def open(self) -> None:
        """Initialize the MediaPipe Gesture Recognizer using its local model."""
        if self._recognizer is not None:
            return
        if not self.model_path.is_file():
            raise FileNotFoundError(
                "MediaPipe gesture model is missing: "
                f"{self.model_path}. Download gesture_recognizer.task as described in README.md."
            )

        try:
            base_options = mp.tasks.BaseOptions(model_asset_path=str(self.model_path))
            options = mp.tasks.vision.GestureRecognizerOptions(
                base_options=base_options,
                running_mode=mp.tasks.vision.RunningMode.VIDEO,
                num_hands=self.max_num_hands,
                min_hand_detection_confidence=self.min_detection_confidence,
                min_hand_presence_confidence=self.min_detection_confidence,
                min_tracking_confidence=self.min_tracking_confidence,
            )
            self._recognizer = mp.tasks.vision.GestureRecognizer.create_from_options(options)
        except Exception as error:
            raise RuntimeError(f"Failed to initialize MediaPipe Gesture Recognizer: {error}") from error

    def detect(self, bgr_frame: Any) -> Any:
        """Convert the supplied BGR frame to RGB and recognize its hands."""
        if self._recognizer is None:
            raise RuntimeError("MediaPipe is not initialized. Call open() before detect().")

        try:
            rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            timestamp_ms = max(time.monotonic_ns() // 1_000_000, self._last_timestamp_ms + 1)
            self._last_timestamp_ms = timestamp_ms
            return self._recognizer.recognize_for_video(image, timestamp_ms)
        except Exception as error:
            raise RuntimeError(f"MediaPipe failed to process the camera frame: {error}") from error

    def draw_landmarks(self, preview_frame: Any, detection_result: Any) -> None:
        """Draw 21 landmarks and their connections on a preview-only frame copy."""
        frame_height, frame_width = preview_frame.shape[:2]

        for landmarks in detection_result.hand_landmarks:
            points = [
                (int(landmark.x * frame_width), int(landmark.y * frame_height))
                for landmark in landmarks
            ]
            for start, end in HAND_CONNECTIONS:
                if start < len(points) and end < len(points):
                    cv2.line(preview_frame, points[start], points[end], (0, 255, 0), 2)
            for point in points:
                cv2.circle(preview_frame, point, 3, (0, 0, 255), -1)

    def close(self) -> None:
        """Release MediaPipe task resources."""
        if self._recognizer is not None:
            try:
                self._recognizer.close()
            except Exception as error:
                raise RuntimeError(f"Failed to close MediaPipe Gesture Recognizer: {error}") from error
            finally:
                self._recognizer = None
