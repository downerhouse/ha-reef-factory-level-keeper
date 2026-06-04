"""Binary sensor platform for Reef Factory Smart Level Keeper."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
)
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
    """Set up Smart Level Keeper binary sensors."""

    coordinator: ReeffactoryCoordinator = hass.data[
        DOMAIN
    ][entry.entry_id]

    async_add_entities(
        [
            LevelKeeperPumpRunning(
                coordinator
            ),
        ]
    )


class LevelKeeperPumpRunning(
    BinarySensorEntity
):
    """ATO pump running."""

    _attr_has_entity_name = True
    _attr_name = "Pump Running"
    _attr_icon = "mdi:pump"

    def __init__(
        self,
        coordinator: ReeffactoryCoordinator,
    ) -> None:

        self._coordinator = coordinator

        self._attr_unique_id = (
            f"{coordinator.unique_id_prefix}"
            "_pump_running"
        )

        self._attr_device_info = (
            coordinator.device_info
        )

    @property
    def available(self) -> bool:

        return self._coordinator.available

    async def async_added_to_hass(
        self,
    ) -> None:

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_DATA_UPDATED,
                self._handle_update,
            )
        )

    @callback
    def _handle_update(self) -> None:

        self._attr_is_on = (
            self._coordinator.lk_data.get(
                "pump_running",
                False,
            )
        )

        self.async_write_ha_state()