"""Small OBS WebSocket v5 controller for scene item visibility."""

from __future__ import annotations

from typing import Any, Iterable


class ObsController:
    """Connect to OBS and change scene-item enabled states."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 4455,
        password: str = "",
    ) -> None:
        self.host = host
        self.port = port
        self.password = password
        self._client: Any | None = None
        self._scene_item_ids: dict[tuple[str, str], int] = {}

    def connect(self) -> None:
        """Connect to OBS WebSocket v5 and verify that it responds."""
        if self.is_connected():
            return

        try:
            import obsws_python as obs
        except ModuleNotFoundError as error:
            raise RuntimeError(
                "obsws-python is not installed. Run: py -m pip install -r requirements.txt"
            ) from error

        try:
            self._client = obs.ReqClient(
                host=self.host,
                port=self.port,
                password=self.password,
                timeout=3,
            )
            version = self._client.get_version()
            print(f"Connected to OBS {version.obs_version} at {self.host}:{self.port}")
        except Exception as error:
            self.disconnect()
            details = str(error).lower()
            if "auth" in details or "password" in details:
                reason = "Check the OBS WebSocket password."
            else:
                reason = (
                    "Confirm OBS is running, WebSocket Server is enabled, "
                    "and the host/port are correct."
                )
            raise RuntimeError(
                f"Could not connect to OBS WebSocket at {self.host}:{self.port}. "
                f"{reason} Details: {error}"
            ) from error

    def validate_scene(self, scene_name: str, source_names: Iterable[str]) -> None:
        """Verify one scene and required source scene-items before capture starts."""
        self._require_connection()
        try:
            scene_list = self._client.get_scene_list().scenes
            scene_names = {scene["sceneName"] for scene in scene_list}
        except Exception as error:
            raise RuntimeError(f"Could not read OBS scenes: {error}") from error

        if scene_name not in scene_names:
            raise RuntimeError(f"OBS scene not found: {scene_name}")

        for source_name in source_names:
            self._get_scene_item_id(scene_name, source_name)

    def set_source_visible(
        self, scene_name: str, source_name: str, visible: bool
    ) -> None:
        """Set a source's scene-item enabled state in the specified scene."""
        self._require_connection()
        scene_item_id = self._get_scene_item_id(scene_name, source_name)
        try:
            self._client.set_scene_item_enabled(scene_name, scene_item_id, visible)
        except Exception as error:
            state = "visible" if visible else "hidden"
            raise RuntimeError(
                f"Could not make OBS source '{source_name}' {state} in scene "
                f"'{scene_name}': {error}"
            ) from error

    def disconnect(self) -> None:
        """Close the OBS WebSocket connection."""
        if self._client is not None:
            try:
                self._client.disconnect()
            finally:
                self._client = None
                self._scene_item_ids.clear()

    def is_connected(self) -> bool:
        return self._client is not None

    def _get_scene_item_id(self, scene_name: str, source_name: str) -> int:
        key = (scene_name, source_name)
        if key in self._scene_item_ids:
            return self._scene_item_ids[key]

        try:
            response = self._client.get_scene_item_id(scene_name, source_name)
            scene_item_id = response.scene_item_id
        except Exception as error:
            raise RuntimeError(
                f"OBS source not found: {source_name} in scene {scene_name}. Details: {error}"
            ) from error

        self._scene_item_ids[key] = scene_item_id
        return scene_item_id

    def _require_connection(self) -> None:
        if not self.is_connected():
            raise RuntimeError("OBS is not connected. Call connect() first.")
