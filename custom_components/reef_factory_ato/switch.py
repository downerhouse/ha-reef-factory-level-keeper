"""Switch platform for Reef Factory Smart Level Keeper."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
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
    """Set up Smart Level Keeper switches."""

    coordinator: ReeffactoryCoordinator = hass.data[
        DOMAIN
    ][entry.entry_id]

    async_add_entities(
        [
            LevelKeeperLedSwitch(
                coordinator
            ),
        ]
    )


class LevelKeeperLedSwitch(SwitchEntity):
    """Level Keeper LED switch."""

    _attr_has_entity_name = True
    _attr_name = "ATO LED"
    _attr_icon = "mdi:led-on"

    def __init__(
        self,
        coordinator: ReeffactoryCoordinator,
    ) -> None:
        self._coordinator = coordinator

        self._attr_unique_id = (
            f"{coordinator.unique_id_prefix}"
            "_ato_led"
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
                "led_enabled",
                False,
            )
        )

        self.async_write_ha_state()

    async def async_turn_on(
        self,
        **kwargs,
    ) -> None:
        await self._coordinator.async_set_led(
            True
        )

    async def async_turn_off(
        self,
        **kwargs,
    ) -> None:
        await self._coordinator.async_set_led(
            False
        )