"""Sensor platform for Reef Factory Smart Level Keeper."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import (
    HomeAssistant,
    callback,
)
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
)
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
)

from .const import DOMAIN, SIGNAL_DATA_UPDATED
from .coordinator import ReeffactoryCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Level Keeper entities."""

    coordinator: ReeffactoryCoordinator = hass.data[
        DOMAIN
    ][entry.entry_id]

    async_add_entities(
        [
            LevelKeeperWaterLevelSensor(
                coordinator
            ),
            LevelKeeperTodayVolumeSensor(
                coordinator
            ),
            LevelKeeperRefillRuntimeSensor(
                coordinator
            ),
            LevelKeeperFloatStateSensor(
                coordinator
            ),
            LevelKeeperMaxRuntimeSensor(
                coordinator
            ),
            LevelKeeperCalibrationVolumeSensor(
                coordinator
            ),
            LevelKeeperNextCalibrationDateSensor(
                coordinator
            ),
            LevelKeeperCalibrationCountdownSensor(
                coordinator
            ),
        ]
    )


class LevelKeeperBaseEntity:
    """Base Level Keeper sensor entity."""

    def __init__(
        self,
        coordinator: ReeffactoryCoordinator,
    ) -> None:

        self._coordinator = coordinator

        self._attr_device_info = (
            coordinator.device_info
        )

    @property
    def available(self) -> bool:
        """Return True if device is connected."""

        return self._coordinator.available

    async def async_added_to_hass(
        self,
    ) -> None:
        """Subscribe to updates."""

        await super().async_added_to_hass()

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_DATA_UPDATED,
                self._handle_update,
            )
        )

    @callback
    def _handle_update(self) -> None:
        """Handle updates."""

        self.async_write_ha_state()


class LevelKeeperWaterLevelSensor(
    LevelKeeperBaseEntity,
    SensorEntity,
):
    """ATO water level status."""

    _attr_has_entity_name = True
    _attr_name = "Water Level"
    _attr_icon = "mdi:waves-arrow-up"

    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.unique_id_prefix}"
            "_water_level"
        )

    @property
    def native_value(self):

        return self._coordinator.lk_data.get(
            "water_level_status",
            "Unknown",
        )
        
    @property
    def extra_state_attributes(self):

        return {
            "status_code": self._coordinator.lk_data.get(
                "status_code"
            )
        }
        
class LevelKeeperTodayVolumeSensor(
    LevelKeeperBaseEntity,
    SensorEntity,
):
    """ATO today's delivered volume."""

    _attr_has_entity_name = True
    _attr_name = "Today's Volume"

    _attr_native_unit_of_measurement = "ml"

    _attr_icon = "mdi:water"

    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.unique_id_prefix}"
            "_today_volume"
        )

    @property
    def native_value(self):

        return self._coordinator.lk_data.get(
            "today_volume_ml"
        )
        
class LevelKeeperRefillRuntimeSensor(
    LevelKeeperBaseEntity,
    SensorEntity,
):
    """ATO refill runtime."""

    _attr_has_entity_name = True
    _attr_name = "Refill Runtime"

    _attr_native_unit_of_measurement = "s"

    _attr_icon = "mdi:timer-outline"

    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.unique_id_prefix}"
            "_refill_runtime"
        )

    @property
    def native_value(self):

        return self._coordinator.lk_data.get(
            "refill_runtime"
        )

class LevelKeeperFloatStateSensor(
    LevelKeeperBaseEntity,
    SensorEntity,
):
    """ATO float state."""

    _attr_has_entity_name = True
    _attr_name = "Float State"

    _attr_icon = "mdi:waves-arrow-up"

    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.unique_id_prefix}"
            "_float_state"
        )

    @property
    def native_value(self):

        return self._coordinator.lk_data.get(
            "float_state"
        )

class LevelKeeperMaxRuntimeSensor(
    LevelKeeperBaseEntity,
    SensorEntity,
):
    """ATO maximum refill runtime."""

    _attr_has_entity_name = True

    _attr_name = "Max Refill Runtime"

    _attr_native_unit_of_measurement = "s"

    _attr_icon = (
        "mdi:timer-alert-outline"
    )

    def __init__(self, coordinator):

        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.unique_id_prefix}"
            "_max_refill_runtime"
        )

    @property
    def native_value(self):

        return self._coordinator.lk_data.get(
            "max_refill_runtime"
        )
        
class LevelKeeperCalibrationVolumeSensor(
    LevelKeeperBaseEntity,
    SensorEntity,
):
    """ATO calibration volume."""

    _attr_has_entity_name = True
    _attr_name = "Calibration Volume"
    _attr_native_unit_of_measurement = "ml"
    _attr_icon = "mdi:beaker-outline"

    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.unique_id_prefix}"
            "_calibration_volume"
        )

    @property
    def native_value(self):
        return self._coordinator.lk_data.get(
            "calibration_volume_ml"
        )


class LevelKeeperNextCalibrationDateSensor(
    LevelKeeperBaseEntity,
    SensorEntity,
):
    """ATO next calibration date."""

    _attr_has_entity_name = True
    _attr_name = "Next Calibration Date"
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.unique_id_prefix}"
            "_next_calibration_date"
        )

    @property
    def native_value(self):
        return self._coordinator.lk_data.get(
            "next_calibration_date"
        )
        
class LevelKeeperCalibrationCountdownSensor(
    LevelKeeperBaseEntity,
    SensorEntity,
):
    """ATO calibration countdown."""

    _attr_has_entity_name = True
    _attr_name = "Calibration Countdown"

    _attr_native_unit_of_measurement = "s"

    _attr_icon = "mdi:timer-sand"

    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.unique_id_prefix}"
            "_calibration_countdown"
        )

    @property
    def native_value(self):

        return self._coordinator.lk_data.get(
            "calibration_countdown"
        )