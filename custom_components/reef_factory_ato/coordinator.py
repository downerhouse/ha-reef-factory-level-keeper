"""WebSocket connection manager for Reef Factory Smart Level Keeper."""

from __future__ import annotations

import asyncio
import logging
import time

import aiohttp

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import (
    DOMAIN,
    PING_INTERVAL,
    PONG_TIMEOUT,
    SIGNAL_CONNECTION_STATE,
    SIGNAL_DATA_UPDATED,
    WS_PATH,
    WS_SUBPROTOCOL,
)

from .protocol import (
    build_message,
    parse_config_response,
    parse_message,
)

_LOGGER = logging.getLogger(__name__)


class ReeffactoryCoordinator:
    """Manages the persistent WebSocket connection to a Reef Factory device."""

    def __init__(self, hass: HomeAssistant, host: str, name: str) -> None:
        self.hass = hass
        self.host = host
        self.name = name

        self.serial_number: str | None = None
        self.firmware_version: str = "0.0.0"

        self.lk_data: dict = {}

        self.available: bool = False

        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._session: aiohttp.ClientSession | None = None

        self._listen_task: asyncio.Task | None = None
        self._ping_task: asyncio.Task | None = None

        self._stop_event = asyncio.Event()
        self._pong_received = asyncio.Event()

        self._retry_count = 0

    @property
    def unique_id_prefix(self) -> str:
        """Return a stable unique ID prefix for entities."""
        return self.serial_number

    @property
    def device_info(self) -> dict:
        """Return device info for the HA device registry."""

        identifier = self.serial_number or self.host

        return {
            "identifiers": {
                (DOMAIN, identifier)
            },
            "name": "Reef Factory Smart Level Keeper",
            "manufacturer": "Reef Factory",
            "model": "Smart Level Keeper",
            "sw_version": self.firmware_version,
        }

    async def async_start(self) -> None:
        """Start the WebSocket connection."""
        self._stop_event.clear()
        await self._connect()

    async def async_stop(self) -> None:
        """Disconnect and clean up all resources."""

        self._stop_event.set()

        for task in (self._listen_task, self._ping_task):
            if task and not task.done():
                task.cancel()

        if self._ws and not self._ws.closed and self.serial_number:
            try:
                leave_payload = self.serial_number.encode("ascii") + b"\x00"

                msg = build_message(
                    self.serial_number,
                    "pmConnect",
                    "leave",
                    payload=leave_payload,
                )

                await self._ws.send_bytes(msg)

            except Exception:
                pass

        if self._ws and not self._ws.closed:
            await self._ws.close()

        if self._session and not self._session.closed:
            await self._session.close()

    async def _close_connection(self) -> None:
        """Close existing WebSocket and session if open."""

        if self._ping_task and not self._ping_task.done():
            self._ping_task.cancel()

        if self._ws and not self._ws.closed:
            await self._ws.close()

        if self._session and not self._session.closed:
            await self._session.close()

        self._ws = None
        self._session = None

    async def _connect(self) -> None:
        """Establish a WebSocket connection to the device."""

        if self._stop_event.is_set():
            return

        await self._close_connection()

        url = f"ws://{self.host}/{WS_PATH}"

        try:
            self._session = aiohttp.ClientSession()

            self._ws = await self._session.ws_connect(
                url,
                protocols=[WS_SUBPROTOCOL],
                timeout=10,
            )

            self._retry_count = 0

            msg = build_message(
                "0000000000000000",
                "get",
                "config",
            )

            await self._ws.send_bytes(msg)

            self._listen_task = asyncio.create_task(
                self._listen()
            )

            self._ping_task = asyncio.create_task(
                self._ping_loop()
            )

        except (
            aiohttp.ClientError,
            OSError,
            asyncio.TimeoutError,
        ) as err:

            _LOGGER.warning(
                "Connection to %s failed: %s",
                self.host,
                err,
            )

            if self._session and not self._session.closed:
                await self._session.close()

            await self._schedule_reconnect()

    async def _listen(self) -> None:
        """Read incoming WebSocket messages until disconnection."""

        try:
            async for ws_msg in self._ws:

                if ws_msg.type == aiohttp.WSMsgType.BINARY:
                    self._handle_message(ws_msg.data)

                elif ws_msg.type in (
                    aiohttp.WSMsgType.ERROR,
                    aiohttp.WSMsgType.CLOSE,
                    aiohttp.WSMsgType.CLOSING,
                    aiohttp.WSMsgType.CLOSED,
                ):
                    break

        except asyncio.CancelledError:
            return

        except Exception:
            _LOGGER.exception(
                "WebSocket listener error for %s",
                self.host,
            )

        finally:
            if not self._stop_event.is_set():
                self._set_unavailable()
                await self._cleanup_and_reconnect()

    def _set_unavailable(self) -> None:
        """Mark the device as unavailable and notify entities."""

        if self.available:
            self.available = False

            async_dispatcher_send(
                self.hass,
                SIGNAL_CONNECTION_STATE,
                False,
            )

    async def _cleanup_and_reconnect(self) -> None:
        """Close current session and schedule reconnect."""

        await self._close_connection()
        await self._schedule_reconnect()

    async def _schedule_reconnect(self) -> None:
        """Reconnect with progressive back-off."""

        if self._stop_event.is_set():
            return

        self._retry_count += 1

        if self._retry_count <= 3:
            delay = 5
        elif self._retry_count <= 10:
            delay = 15
        else:
            delay = 30

        await asyncio.sleep(delay)

        if not self._stop_event.is_set():
            self.hass.async_create_task(
                self._connect()
            )

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    async def async_set_led(self, enabled: bool) -> None:
        """Set Level Keeper LED."""

        if not self._ws or self._ws.closed or not self.serial_number:
            return

        payload = bytearray([
            1 if enabled else 0,
            0,
        ])

        msg = build_message(
            self.serial_number,
            "lkSet",
            "light",
            identifier=str(int(time.time() * 1000)),
            payload=payload,
        )

        _LOGGER.debug(
            "TX LED enabled=%s payload=%s",
            enabled,
            payload.hex(),
        )

        await self._ws.send_bytes(msg)

    async def async_set_max_runtime(self, seconds: int) -> None:
        """Set max refill runtime in seconds. Zero disables it."""

        if not self._ws or self._ws.closed or not self.serial_number:
            return

        if seconds <= 0:
            payload = b"\xff\xff\xff\xff"
        else:
            payload = seconds.to_bytes(4, "big")

        msg = build_message(
            self.serial_number,
            "lkSet",
            "maxRefillTime",
            identifier=str(int(time.time() * 1000)),
            payload=payload,
        )

        _LOGGER.debug(
            "SET MAX REFILL RUNTIME seconds=%s payload=%s len=%s",
            seconds,
            payload.hex(),
            len(payload),
        )

        await self._ws.send_bytes(msg)

    async def async_set_calibration_time(self, seconds: int) -> None:
        """Set calibration pump runtime."""

        if not self._ws or self._ws.closed or not self.serial_number:
            return

        payload = seconds.to_bytes(1, "big") + b"\x00"

        msg = build_message(
            self.serial_number,
            "lkCalibration",
            "time",
            identifier=str(int(time.time() * 1000)),
            payload=payload,
        )

        _LOGGER.debug(
            "TX CAL TIME seconds=%s payload=%s",
            seconds,
            payload.hex(),
        )

        await self._ws.send_bytes(msg)

    async def async_start_calibration(self) -> None:
        """Start calibration pump run."""

        if not self._ws or self._ws.closed or not self.serial_number:
            return

        payload = b"\x00"

        msg = build_message(
            self.serial_number,
            "lkCalibration",
            "start",
            identifier=str(int(time.time() * 1000)),
            payload=payload,
        )

        _LOGGER.debug(
            "TX CAL START payload=%s",
            payload.hex(),
        )

        await self._ws.send_bytes(msg)

    async def async_set_calibration_volume(self, volume_ml: int) -> None:
        """Set measured calibration volume."""

        if not self._ws or self._ws.closed or not self.serial_number:
            return

        payload = int(volume_ml).to_bytes(4, "big") + b"\x00"

        msg = build_message(
            self.serial_number,
            "lkCalibration",
            "value",
            identifier=str(int(time.time() * 1000)),
            payload=payload,
        )

        _LOGGER.debug(
            "TX CAL VALUE volume_ml=%s payload=%s",
            volume_ml,
            payload.hex(),
        )

        await self._ws.send_bytes(msg)

    async def async_set_calibration_notification(self, option: int) -> None:
        """Set next calibration interval."""

        if not self._ws or self._ws.closed or not self.serial_number:
            return

        payload = int(option).to_bytes(1, "big") + b"\x00"

        msg = build_message(
            self.serial_number,
            "lkCalibration",
            "notification",
            identifier=str(int(time.time() * 1000)),
            payload=payload,
        )

        _LOGGER.debug(
            "TX CAL NOTIFICATION option=%s payload=%s",
            option,
            payload.hex(),
        )

        await self._ws.send_bytes(msg)

    async def async_save_calibration(self) -> None:
        """Save calibration volume and next calibration interval."""

        volume = int(
            self.lk_data.get(
                "calibration_volume_ml",
                0,
            )
        )

        interval_map = {
            "1 Week": 0,
            "2 Weeks": 1,
            "1 Month": 2,
            "3 Months": 3,
        }

        interval = interval_map.get(
            self.lk_data.get(
                "calibration_interval",
                "1 Week",
            ),
            0,
        )

        await self.async_set_calibration_volume(
            volume
        )

        await self.async_set_calibration_notification(
            interval
        )

    async def async_manual_refill(
        self,
        volume_ml: int,
    ) -> None:
        """Start a manual refill for the requested volume."""

        if not self._ws or self._ws.closed or not self.serial_number:
            return

        payload = int(volume_ml).to_bytes(4, "big") + b"\x00"

        msg = build_message(
            self.serial_number,
            "lkManualRefill",
            "start",
            identifier=str(int(time.time() * 1000)),
            payload=payload,
        )

        _LOGGER.debug(
            "TX MANUAL REFILL volume_ml=%s payload=%s",
            volume_ml,
            payload.hex(),
        )

        await self._ws.send_bytes(msg)
        
    
    async def async_set_mode(self, mode: int) -> None:
        """Set Level Keeper mode."""

        if not self._ws or self._ws.closed or not self.serial_number:
            return

        payload = bytearray([
            mode,
            0,
        ])

        msg = build_message(
            self.serial_number,
            "lkSet",
            "settings",
            identifier=str(int(time.time() * 1000)),
            payload=payload,
        )

        _LOGGER.debug(
            "TX MODE mode=%s payload=%s",
            mode,
            payload.hex(),
        )

        await self._ws.send_bytes(msg)

    
    # ------------------------------------------------------------------
    # Message handling
    # ------------------------------------------------------------------

    @callback
    def _handle_message(self, data: bytes) -> None:
        """Parse and dispatch an incoming binary message."""

        msg = parse_message(data)

        _LOGGER.debug(
            "RX command=%s sub=%s ident=%s payload=%s",
            msg.command,
            msg.subcommand,
            msg.identifier,
            msg.payload.hex(),
        )

        if (
            msg.command == "refresh"
            and msg.subcommand == "config"
        ):
            self._handle_config(msg.payload)

        elif (
            msg.command == "lkRefresh"
            and msg.subcommand == "status"
        ):
            self._handle_lk_status(msg.payload)

        elif (
            msg.command == "lkRefresh"
            and msg.subcommand == "settings"
        ):
            self._handle_lk_settings(msg.payload)

        elif (
            msg.command == "lkRefresh"
            and msg.subcommand == "calibration"
        ):
            self._handle_lk_calibration(msg.payload)
            
        elif (
            msg.command == "lkRefresh"
            and msg.subcommand == "manualRefill"
        ):
            self._handle_lk_manual_refill(msg.payload)

        elif (
            msg.command == "lkRefresh"
            and msg.subcommand == "alert"
        ):
            _LOGGER.warning(
                "LEVEL KEEPER ALERT %s",
                msg.payload.hex(),
            )

        elif msg.command == "pong":
            self._pong_received.set()

    def _handle_lk_status(self, payload: bytes) -> None:
        """Handle Level Keeper status packet."""

        _LOGGER.debug(
            "LEVEL KEEPER STATUS %s",
            payload.hex(),
        )

        status_code = payload[0]

        status_map = {
            6: "Low Water",
            0: "Normal",
            5: "High Water",
            1: "Refilling",
        }

        self.lk_data["status_raw"] = payload.hex()
        self.lk_data["status_code"] = status_code

        self.lk_data["water_level_status"] = status_map.get(
            status_code,
            f"Unknown ({status_code})",
        )

        if status_code == 6:
            self.lk_data["float_state"] = "Both Low"
        elif status_code == 5:
            self.lk_data["float_state"] = "Both High"
        else:
            self.lk_data["float_state"] = "One High / One Low"

        if len(payload) >= 9:
            self.lk_data["pump_running"] = payload[0] == 1

            self.lk_data["today_volume_ml"] = int.from_bytes(
                payload[4:8],
                "little",
            )

            self.lk_data["refill_runtime"] = payload[8]

            _LOGGER.debug(
                "PUMP=%s TODAY=%s RUNTIME=%s",
                self.lk_data["pump_running"],
                self.lk_data["today_volume_ml"],
                self.lk_data["refill_runtime"],
            )

        async_dispatcher_send(
            self.hass,
            SIGNAL_DATA_UPDATED,
        )

    def _handle_lk_settings(self, payload: bytes) -> None:
        """Handle Level Keeper settings packet."""

        for i in range(20, 33):
            if i < len(payload):
                _LOGGER.debug(
                    "OFFSET %s = %02x",
                    i,
                    payload[i],
                )
                
        mode_map = {
            0: "Off",
            1: "60 Minutes",
            2: "30 Minutes",
            3: "10 Minutes",
            4: "Continuous",
            5: "Hysteresis",
        }

        self.lk_data["mode_raw"] = payload[0]
        self.lk_data["mode"] = mode_map.get(
            payload[0],
            f"Unknown ({payload[0]})",
        )

        self.lk_data["led_enabled"] = bool(payload[33])

        self.lk_data["calibration_volume_ml"] = int.from_bytes(
            payload[4:6],
            "big",
        )

        day = payload[6]
        month = payload[7]
        year = int.from_bytes(payload[8:10], "big")

        self.lk_data["next_calibration_date"] = (
            f"{day:02d}/{month:02d}/{year}"
        )

        raw_max_refill_runtime = int.from_bytes(
            payload[25:29],
            "big",
        )

        if raw_max_refill_runtime == 0xFFFFFFFF:
            max_refill_runtime = 0
        else:
            max_refill_runtime = raw_max_refill_runtime

        self.lk_data["max_refill_runtime"] = max_refill_runtime

        _LOGGER.debug(
            "CALIBRATION volume=%sml next=%s",
            self.lk_data["calibration_volume_ml"],
            self.lk_data["next_calibration_date"],
        )

        _LOGGER.debug(
            "MAX RUNTIME=%s raw=%s",
            max_refill_runtime,
            payload[25:29].hex(),
        )

        async_dispatcher_send(
            self.hass,
            SIGNAL_DATA_UPDATED,
        )

    def _handle_lk_calibration(self, payload: bytes) -> None:
        """Handle calibration countdown packet."""

        self.lk_data["calibration_countdown"] = int.from_bytes(
            payload,
            "big",
        )

        _LOGGER.debug(
            "CALIBRATION COUNTDOWN=%s",
            self.lk_data["calibration_countdown"],
        )

        async_dispatcher_send(
            self.hass,
            SIGNAL_DATA_UPDATED,
        )

    def _handle_lk_manual_refill(self, payload: bytes) -> None:
        """Handle manual refill update packet."""

        if len(payload) >= 8:
            self.lk_data["manual_refill_requested_ml"] = int.from_bytes(
                payload[0:4],
                "big",
            )

            self.lk_data["manual_refill_remaining_ml"] = int.from_bytes(
                payload[4:8],
                "big",
            )

        _LOGGER.debug(
            "MANUAL REFILL requested=%s remaining=%s raw=%s",
            self.lk_data.get("manual_refill_requested_ml"),
            self.lk_data.get("manual_refill_remaining_ml"),
            payload.hex(),
        )

        async_dispatcher_send(
            self.hass,
            SIGNAL_DATA_UPDATED,
        )

    def _handle_config(self, payload: bytes) -> None:
        """Process config response."""

        config = parse_config_response(payload)

        self.serial_number = config["serial_number"]
        self.firmware_version = config["firmware_version"]

        self.available = True

        async_dispatcher_send(
            self.hass,
            SIGNAL_CONNECTION_STATE,
            True,
        )

        self.hass.async_create_task(
            self._subscribe()
        )

    async def _subscribe(self) -> None:
        """Send Level Keeper join request."""

        if not self._ws or self._ws.closed or not self.serial_number:
            return

        join_payload = (
            self.serial_number.encode("ascii")
            + b"\x00"
        )

        msg = build_message(
            self.serial_number,
            "lkConnect",
            "join",
            payload=join_payload,
        )

        _LOGGER.debug(
            "Sending Level Keeper join request"
        )

        await self._ws.send_bytes(msg)

        user_msg = build_message(
            self.serial_number,
            "get",
            "user",
        )

        _LOGGER.debug("TX GET USER")

        await self._ws.send_bytes(user_msg)

    async def _ping_loop(self) -> None:
        """Send periodic pings and verify pong responses."""

        try:
            while not self._stop_event.is_set():

                await asyncio.sleep(PING_INTERVAL)

                if not self._ws or self._ws.closed:
                    break

                self._pong_received.clear()

                serial = (
                    self.serial_number
                    or "0000000000000000"
                )

                msg = build_message(
                    serial,
                    "ping",
                    "ping",
                )

                try:
                    await self._ws.send_bytes(msg)

                except Exception:

                    if self._ws and not self._ws.closed:
                        await self._ws.close()

                    break

                try:
                    await asyncio.wait_for(
                        self._pong_received.wait(),
                        timeout=PONG_TIMEOUT,
                    )

                except asyncio.TimeoutError:

                    _LOGGER.warning(
                        "Pong timeout from %s",
                        self.host,
                    )

                    if self._ws and not self._ws.closed:
                        await self._ws.close()

                    break

        except asyncio.CancelledError:
            return