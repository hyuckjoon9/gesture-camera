"""Unity Capture output using pyvirtualcam only."""

from __future__ import annotations

from typing import Any


class VirtualCamera:
    """Send raw BGR OpenCV frames to the Unity Capture virtual camera."""

    def __init__(
        self,
        width: int = 1280,
        height: int = 720,
        fps: int = 30,
        device: str | None = None,
    ) -> None:
        self.width = width
        self.height = height
        self.fps = fps
        self.device = device
        self._camera: Any | None = None

    def open(self) -> None:
        """Open Unity Capture without falling back to any other backend."""
        if self.is_opened():
            return

        try:
            import pyvirtualcam
        except ModuleNotFoundError as error:
            raise RuntimeError(
                "pyvirtualcam is not installed. Run: py -m pip install -r requirements.txt"
            ) from error

        try:
            self._camera = pyvirtualcam.Camera(
                width=self.width,
                height=self.height,
                fps=self.fps,
                fmt=pyvirtualcam.PixelFormat.BGR,
                device=self.device,
                backend="unitycapture",
            )
        except Exception as error:
            raise RuntimeError(
                "Unity Capture virtual camera could not be opened. "
                "Install/register Unity Capture, ensure it is not in use by another "
                f"process, and retry. Details: {error}"
            ) from error

        print("Virtual Camera:")
        print(f"Backend: {self._camera.backend}")
        print(f"Device: {self._camera.device}")
        print(f"Resolution: {self._camera.width}x{self._camera.height}")
        print(f"FPS: {self._camera.fps:g}")
        print(f"Input pixel format: {self._camera.fmt.name}")

    def send(self, frame: Any) -> None:
        """Send one unmodified BGR frame and pace output to the target FPS."""
        if not self.is_opened():
            raise RuntimeError("Virtual camera is not open. Call open() before send().")

        shape = getattr(frame, "shape", None)
        expected_shape = (self.height, self.width, 3)
        if shape != expected_shape:
            raise ValueError(
                f"Virtual camera requires a BGR frame of shape {expected_shape}, "
                f"but received {shape}. Frames are not resized automatically."
            )

        try:
            self._camera.send(frame)
            # Adaptive pacing avoids adding delay when processing is already slow.
            self._camera.sleep_until_next_frame()
            if self._camera.frames_sent % self.fps == 0:
                print(f"Virtual Camera send FPS: {self._camera.current_fps:.1f}")
        except Exception as error:
            raise RuntimeError(f"Failed to send a frame to Unity Capture: {error}") from error

    def close(self) -> None:
        """Release the Unity Capture output device."""
        if self._camera is not None:
            try:
                self._camera.close()
            except Exception as error:
                raise RuntimeError(f"Failed to close Unity Capture virtual camera: {error}") from error
            finally:
                self._camera = None

    def is_opened(self) -> bool:
        """Return whether the Unity Capture output device is ready."""
        return self._camera is not None
