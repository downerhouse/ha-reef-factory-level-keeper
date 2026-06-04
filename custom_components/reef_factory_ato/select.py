from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SIGNAL_DATA_UPDATED
from .coordinator import ReeffactoryCoordinator


MODE_OPTIONS = [
    "Off",
    "60 Minutes",
    "30 Minutes",
    "10 Minutes",
    "Continuous",
    "Hysteresis",
]

MODE_MAP = {
    "Off": 0,
    "60 Minutes": 1,
    "30 Minutes": 2,
    "10 Minutes": 3,
    "Continuous": 4,
    "Hysteresis": 5,
}

CALIBRATION_INTERVAL_OPTIONS = {
    "1 Week": 0,
    "2 Weeks": 1,
    "1 Month": 2,
    "3 Months": 3,
}


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
            LevelKeeperModeSelect(
                coordinator
            ),
            LevelKeeperCalibrationIntervalSelect(
                coordinator
            ),
        ]
    )


class LevelKeeperBaseSelect(SelectEntity):
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


class LevelKeeperModeSelect(
    LevelKeeperBaseSelect
):
    _attr_name = "ATO Mode"

    def __init__(
        self,
        coordinator: ReeffactoryCoordinator,
    ) -> None:
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.unique_id_prefix}"
            "_ato_mode"
        )

        self._attr_options = MODE_OPTIONS

    @property
    def current_option(self):
        return self._coordinator.lk_data.get(
            "mode"
        )

    async def async_select_option(
        self,
        option: str,
    ) -> None:
        await self._coordinator.async_set_mode(
            MODE_MAP[option]
        )


class LevelKeeperCalibrationIntervalSelect(
    LevelKeeperBaseSelect
):
    _attr_name = "Calibration Interval"

    def __init__(
        self,
        coordinator: ReeffactoryCoordinator,
    ) -> None:
        super().__init__(coordinator)

        self._attr_unique_id = (
            f"{coordinator.unique_id_prefix}"
            "_calibration_interval"
        )

        self._attr_options = list(
            CALIBRATION_INTERVAL_OPTIONS.keys()
        )

        self._coordinator.lk_data.setdefault(
            "calibration_interval",
            "1 Week",
        )

    @property
    def current_option(self):
        return self._coordinator.lk_data.get(
            "calibration_interval",
            "1 Week",
        )

    async def async_select_option(
        self,
        option: str,
    ) -> None:
        self._coordinator.lk_data[
            "calibration_interval"
        ] = option

        self.async_write_ha_state()