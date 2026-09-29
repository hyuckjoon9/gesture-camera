"""Non-blocking lifecycle for one active group of OBS effect sources."""

from __future__ import annotations

from collections.abc import Iterable

from .obs_controller import ObsController


class EffectManager:
    """Show one source group briefly, replacing the active group when needed."""

    def __init__(
        self, controller: ObsController, scene_name: str, duration_seconds: float = 2.0
    ) -> None:
        self.controller = controller
        self.scene_name = scene_name
        self.duration_seconds = duration_seconds
        self.active_effects: tuple[str, ...] = ()
        self.expires_at: float | None = None

    def trigger(self, effect_names: Iterable[str], current_time: float) -> None:
        """Activate sources together, first clearing a different active group."""
        effect_names = tuple(effect_names)
        if not effect_names:
            return
        if self.active_effects == effect_names:
            return

        self.clear()
        for effect_name in effect_names:
            self.controller.set_source_visible(self.scene_name, effect_name, True)
        self.active_effects = effect_names
        self.expires_at = current_time + self.duration_seconds
        print(f"OBS effects ON: {', '.join(effect_names)} ({self.duration_seconds:g}s)")

    def update(self, current_time: float) -> None:
        """Turn off the active effect when its deadline is reached; never blocks."""
        if self.expires_at is not None and current_time >= self.expires_at:
            self.clear()

    def clear(self) -> None:
        """Immediately hide every source in the active group, if present."""
        if self.active_effects:
            effect_names = self.active_effects
            self.active_effects = ()
            self.expires_at = None
            for effect_name in effect_names:
                self.controller.set_source_visible(self.scene_name, effect_name, False)
            print(f"OBS effects OFF: {', '.join(effect_names)}")
