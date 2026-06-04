from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SIGNAL_DATA_UPDATED
from .coordinator import ReeffactoryCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ReeffactoryCoordinator = hass.data[
        DOMAIN
    ][entry.entry_id]

    async_add_entities(
        [
            LevelKeeperMaxRuntime(
                coordinator
            ),
            LevelKeeperCalibrationRuntime(
                coordinator
            ),
            LevelKeeperCalibrationVolume(
                coordinator
            ),
            LevelKeeperManualRefillVolume(
                coordinator
            ),
        ]
    )


class LevelKeeperBaseNumber(NumberEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ReeffactoryCoordinator,
    ) -> None:
        self._coordinator = coordinator
        self._attr_device_info = coordinator.device_info

    @property
    def available(self):
        return self._coordinator.available

    async def async_added_to_hass(self):
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_DATA_UPDATED,
                self._handle_update,
            )
        )

    @callback
    def _handle_update(self):
        self.async_write_ha_state()


class LevelKeeperMaxRuntime(
    LevelKeeperBaseNumber
):
    _attr_name = "Max Refill Runtime"
    _attr_native_min_value = 0
    _attr_native_max_value = 60.0
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = "min"
    _attr_icon = "mdi:timer-alert-outline"

    def __init__(
        self,
        coordinator: ReeffactoryCoordinator,
    ) -> None:
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.unique_id_prefix}"
            "_max_refill_runtime"
        )

    @property
    def native_value(self):
        seconds = self._coordinator.lk_data.get(
            "max_refill_runtime"
        )

        if seconds is None:
            return None

        return round(
            seconds / 60,
            1,
        )

    async def async_set_native_value(
        self,
        value: float,
    ) -> None:
        seconds = int(
            round(
                value * 60
            )
        )

        await self._coordinator.async_set_max_runtime(
            seconds
        )


class LevelKeeperCalibrationRuntime(
    LevelKeeperBaseNumber
):
    _attr_name = "Calibration Runtime"
    _attr_native_min_value = 1
    _attr_native_max_value = 60
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "s"
    _attr_icon = "mdi:timer-play-outline"

    def __init__(
        self,
        coordinator: ReeffactoryCoordinator,
    ) -> None:
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.unique_id_prefix}"
            "_calibration_runtime"
        )

        self._coordinator.lk_data.setdefault(
            "calibration_runtime",
            7,
        )

    @property
    def native_value(self):
        return self._coordinator.lk_data.get(
            "calibration_runtime",
            7,
        )

    async def async_set_native_value(
        self,
        value: float,
    ) -> None:
        self._coordinator.lk_data[
            "calibration_runtime"
        ] = int(value)

        self.async_write_ha_state()


class LevelKeeperCalibrationVolume(
    LevelKeeperBaseNumber
):
    _attr_name = "Calibration Volume"
    _attr_native_min_value = 1
    _attr_native_max_value = 9999
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "ml"
    _attr_icon = "mdi:beaker-outline"

    def __init__(
        self,
        coordinator: ReeffactoryCoordinator,
    ) -> None:
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.unique_id_prefix}"
            "_calibration_volume_number"
        )

    @property
    def native_value(self):
        return self._coordinator.lk_data.get(
            "calibration_volume_ml"
        )

    async def async_set_native_value(
        self,
        value: float,
    ) -> None:
        self._coordinator.lk_data[
            "calibration_volume_ml"
        ] = int(value)

        self.async_write_ha_state()
        
class LevelKeeperManualRefillVolume(
    LevelKeeperBaseNumber
):
    _attr_name = "Manual Refill Volume"
    _attr_native_min_value = 1
    _attr_native_max_value = 9999
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "ml"
    _attr_icon = "mdi:water-plus"

    def __init__(
        self,
        coordinator: ReeffactoryCoordinator,
    ) -> None:
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.unique_id_prefix}"
            "_manual_refill_volume"
        )

        self._coordinator.lk_data.setdefault(
            "manual_refill_volume_ml",
            250,
        )

    @property
    def native_value(self):
        return self._coordinator.lk_data.get(
            "manual_refill_volume_ml",
            250,
        )

    async def async_set_native_value(
        self,
        value: float,
    ) -> None:
        self._coordinator.lk_data[
            "manual_refill_volume_ml"
        ] = int(value)

        self.async_write_ha_state()