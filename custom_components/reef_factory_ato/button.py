"""Button platform for Reef Factory Smart Level Keeper."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ReeffactoryCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Level Keeper buttons."""

    coordinator: ReeffactoryCoordinator = hass.data[
        DOMAIN
    ][entry.entry_id]

    async_add_entities(
        [
            LevelKeeperStartCalibrationButton(
                coordinator
            ),
            LevelKeeperSaveCalibrationButton(
                coordinator
            ),
            LevelKeeperManualRefillButton(
                coordinator
            ),
        ]
    )


class LevelKeeperBaseButton(ButtonEntity):
    """Base Level Keeper button."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ReeffactoryCoordinator,
    ) -> None:
        self._coordinator = coordinator
        self._attr_device_info = coordinator.device_info

    @property
    def available(self) -> bool:
        return True


class LevelKeeperStartCalibrationButton(
    LevelKeeperBaseButton
):
    """Start calibration pump run."""

    _attr_name = "Start Calibration"
    _attr_icon = "mdi:timer-play-outline"

    def __init__(
        self,
        coordinator: ReeffactoryCoordinator,
    ) -> None:
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.unique_id_prefix}"
            "_start_calibration"
        )

    async def async_press(self) -> None:
        seconds = int(
            self._coordinator.lk_data.get(
                "calibration_runtime",
                7,
            )
        )

        await self._coordinator.async_set_calibration_time(
            seconds
        )

        await self._coordinator.async_start_calibration()


class LevelKeeperSaveCalibrationButton(
    LevelKeeperBaseButton
):
    """Save calibration volume and interval."""

    _attr_name = "Save Calibration"
    _attr_icon = "mdi:content-save"

    def __init__(
        self,
        coordinator: ReeffactoryCoordinator,
    ) -> None:
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.unique_id_prefix}"
            "_save_calibration"
        )

    async def async_press(self) -> None:
        await self._coordinator.async_save_calibration()
        
class LevelKeeperManualRefillButton(
    LevelKeeperBaseButton
):
    """Start manual refill."""

    _attr_name = "Start Manual Refill"
    _attr_icon = "mdi:water-plus"

    def __init__(
        self,
        coordinator: ReeffactoryCoordinator,
    ) -> None:

        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.unique_id_prefix}"
            "_manual_refill"
        )

    async def async_press(self) -> None:

        volume_ml = int(
            self._coordinator.lk_data.get(
                "manual_refill_volume_ml",
                250,
            )
        )

        await self._coordinator.async_manual_refill(
            volume_ml
        )