"""Minimal OpenCV webcam capture wrapper."""

from __future__ import annotations

from typing import Any

import cv2


class CameraCapture:
    """Own one physical webcam and expose its unmodified frames."""

    def __init__(
        self,
        camera_index: int = 0,
        backend: int = cv2.CAP_MSMF,
        width: int = 1280,
        height: int = 720,
        fps: int = 30,
    ) -> None:
        self.camera_index = camera_index
        self.backend = backend
        self.width = width
        self.height = height
        self.fps = fps
        self._capture: cv2.VideoCapture | None = None

    def open(self) -> None:
        """Open the camera and request the configured capture settings."""
        if self.is_opened():
            return

        self._capture = cv2.VideoCapture(self.camera_index, self.backend)
        if not self._capture.isOpened():
            self.release()
            raise RuntimeError(
                f"Could not open camera index {self.camera_index} with CAP_MSMF."
            )

        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self._capture.set(cv2.CAP_PROP_FPS, self.fps)

    def read(self) -> tuple[bool, Any]:
        """Return the next unmodified webcam frame as (success, frame)."""
        if not self.is_opened():
            raise RuntimeError("Camera is not open. Call open() before read().")
        return self._capture.read()  # type: ignore[union-attr]

    def release(self) -> None:
        """Release the webcam device if it is currently allocated."""
        if self._capture is not None:
            self._capture.release()
            self._capture = None

    def is_opened(self) -> bool:
        """Return whether OpenCV currently has the webcam open."""
        return self._capture is not None and self._capture.isOpened()

    def print_actual_settings(self) -> None:
        """Print actual OpenCV capture values and warn about any fallback."""
        if not self.is_opened():
            raise RuntimeError("Camera is not open. Cannot read camera settings.")

        actual_width = int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH))  # type: ignore[union-attr]
        actual_height = int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT))  # type: ignore[union-attr]
        actual_fps = self._capture.get(cv2.CAP_PROP_FPS)  # type: ignore[union-attr]

        print(f"Camera index: {self.camera_index}")
        print("Camera backend: CAP_MSMF (Media Foundation)")
        print(f"Requested resolution: {self.width}x{self.height}")
        print(f"Requested FPS: {self.fps}")
        print(f"Actual resolution: {actual_width}x{actual_height}")
        print(f"Actual FPS: {actual_fps:g}")

        if (actual_width, actual_height) != (self.width, self.height):
            print("WARNING: Actual resolution differs from the requested resolution.")
        if abs(actual_fps - self.fps) > 0.01:
            print("WARNING: Actual FPS differs from the requested FPS.")
