"""Entry point for fixed CAP_MSMF capture with MediaPipe hand gestures."""

from pathlib import Path
import time

import cv2

from camera.camera_capture import CameraCapture
from camera.virtual_camera import VirtualCamera
from obs.effect_manager import EffectManager
from obs.obs_controller import ObsController
from recognition.gesture_recognizer import GestureRecognizer, HandGesture
from recognition.hand_detector import HandDetector

WINDOW_NAME = "Gesture Camera - Preview"
CAMERA_INDEX = 0
CAMERA_BACKEND = cv2.CAP_MSMF
REQUESTED_WIDTH = 1280
REQUESTED_HEIGHT = 720
REQUESTED_FPS = 30
GESTURE_MODEL_PATH = Path(__file__).parent / "models" / "gesture_recognizer.task"

OBS_HOST = "localhost"
OBS_PORT = 4455
OBS_PASSWORD = ""
OBS_SCENE_NAME = "GestureCamera"
EFFECT_DURATION_SECONDS = 2.0
GESTURE_EFFECT_MAP = {
    "THUMBS_UP": [
        "effect_thumbs_up_1",
        "effect_thumbs_up_2",
        "effect_thumbs_up_3",
        "effect_thumbs_up_4",
        "effect_thumbs_up_5",
        "effect_thumbs_up_6",
        "effect_thumbs_up_7",
    ],
    "VICTORY": ["effect_victory"],
}
EFFECT_SOURCE_NAMES = tuple(
    source_name
    for source_names in GESTURE_EFFECT_MAP.values()
    for source_name in source_names
)


def draw_status(
    preview_frame: object, hands: list[HandGesture], processing_fps: float
) -> None:
    """Draw current per-hand gesture classifications on the preview copy."""
    lines = ["Gesture Camera - Preview"]
    if not hands:
        lines.append("No hands detected")
    else:
        lines.extend(
            f"{hand.handedness}: {hand.gesture.value} "
            f"(gesture {hand.gesture_score:.2f}, hand {hand.handedness_score:.2f})"
            for hand in hands
        )
    lines.append(f"MediaPipe FPS: {processing_fps:.1f}")

    for index, line in enumerate(lines):
        y = 30 + index * 30
        cv2.putText(
            preview_frame, line, (12, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4
        )
        cv2.putText(
            preview_frame,
            line,
            (12, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            1,
        )


def main() -> None:
    camera = CameraCapture(
        camera_index=CAMERA_INDEX,
        backend=CAMERA_BACKEND,
        width=REQUESTED_WIDTH,
        height=REQUESTED_HEIGHT,
        fps=REQUESTED_FPS,
    )
    detector = HandDetector(model_path=GESTURE_MODEL_PATH, max_num_hands=2)
    gesture_recognizer = GestureRecognizer()
    virtual_camera = VirtualCamera(
        width=REQUESTED_WIDTH,
        height=REQUESTED_HEIGHT,
        fps=REQUESTED_FPS,
    )
    obs_controller = ObsController(OBS_HOST, OBS_PORT, OBS_PASSWORD)
    effect_manager = EffectManager(
        obs_controller, OBS_SCENE_NAME, EFFECT_DURATION_SECONDS
    )
    previous_effect_gestures: set[str] = set()

    try:
        camera.open()
        camera.print_actual_settings()
        detector.open()
        virtual_camera.open()
        obs_controller.connect()
        obs_controller.validate_scene(OBS_SCENE_NAME, EFFECT_SOURCE_NAMES)
        for effect_name in EFFECT_SOURCE_NAMES:
            obs_controller.set_source_visible(OBS_SCENE_NAME, effect_name, False)

        # AUTOSIZE displays raw frames at their native dimensions. Because the
        # window cannot be manually stretched, no preview resize is required.
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_AUTOSIZE)
        print("Preview started. Press 'q' or close the preview window to exit.")

        while True:
            now = time.monotonic()
            effect_manager.update(now)
            success, frame = camera.read()
            if not success:
                raise RuntimeError("Failed to read a frame from the webcam.")

            start_time = time.perf_counter()
            detection_result = detector.detect(frame)
            hands = gesture_recognizer.recognize(detection_result)
            processing_fps = 1 / max(time.perf_counter() - start_time, 1e-6)

            current_effect_gestures = {
                hand.gesture.value
                for hand in hands
                if hand.gesture.value in GESTURE_EFFECT_MAP
            }
            new_effect_gestures = current_effect_gestures - previous_effect_gestures
            for hand in hands:
                gesture_name = hand.gesture.value
                if gesture_name in new_effect_gestures:
                    effect_manager.trigger(GESTURE_EFFECT_MAP[gesture_name], now)
                    new_effect_gestures.remove(gesture_name)
            previous_effect_gestures = current_effect_gestures

            # Send the raw BGR capture frame. The Preview copy below is never sent.
            virtual_camera.send(frame)

            # Keep the capture frame raw. Draw only on the Preview copy.
            preview_frame = frame.copy()
            detector.draw_landmarks(preview_frame, detection_result)
            draw_status(preview_frame, hands, processing_fps)
            cv2.imshow(WINDOW_NAME, preview_frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                break
    finally:
        try:
            effect_manager.clear()
        finally:
            try:
                obs_controller.disconnect()
            finally:
                try:
                    virtual_camera.close()
                finally:
                    try:
                        detector.close()
                    finally:
                        camera.release()
                        cv2.destroyAllWindows()
        print("Camera released. Preview windows closed.")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as error:
        print(f"Camera error: {error}")
