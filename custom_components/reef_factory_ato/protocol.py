"""Binary protocol encoder/decoder for Reef Factory Smart Level Keeper.

Wire format:
    [serialNumber\\0][command\\0][subcommand\\0][identifier\\0][payload_bytes]

All string fields are ASCII, null-terminated.
Payload is raw binary.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging

_LOGGER = logging.getLogger(__name__)


@dataclass
class ReeffactoryMessage:
    """Parsed Reef Factory websocket message."""

    serial_number: str
    command: str
    subcommand: str
    identifier: str
    payload: bytes


def parse_message(data: bytes) -> ReeffactoryMessage:
    """Parse a binary WebSocket frame."""

    pos = 0
    fields: list[str] = []

    for _ in range(4):
        chars: list[str] = []

        while pos < len(data):
            byte = data[pos]
            pos += 1

            if byte == 0:
                break

            chars.append(chr(byte))

        fields.append("".join(chars))

    payload = data[pos:]

    _LOGGER.debug(
        "RF MSG serial=%s cmd=%s sub=%s ident=%s payload=%s",
        fields[0],
        fields[1],
        fields[2],
        fields[3],
        payload.hex(),
    )

    return ReeffactoryMessage(
        serial_number=fields[0],
        command=fields[1],
        subcommand=fields[2],
        identifier=fields[3],
        payload=payload,
    )


def parse_config_response(payload: bytes) -> dict[str, str]:
    """Extract serial number and firmware version from refresh/config payload."""

    pos = 0
    serial_chars: list[str] = []

    while pos < len(payload):
        byte = payload[pos]
        pos += 1

        if byte == 0:
            break

        serial_chars.append(chr(byte))

    serial = "".join(serial_chars)

    pos += 1  # language byte
    pos += 1  # onboarding byte

    firmware_chars: list[str] = []

    for _ in range(5):
        if pos < len(payload):
            firmware_chars.append(chr(payload[pos]))
            pos += 1

    firmware = "".join(firmware_chars)

    return {
        "serial_number": serial,
        "firmware_version": firmware,
    }


def build_message(
    serial_number: str,
    command: str,
    subcommand: str = "",
    identifier: str = "",
    payload: bytes | None = None,
) -> bytes:
    """Construct an outgoing binary WebSocket frame."""

    parts = bytearray()

    for field in (
        serial_number,
        command,
        subcommand,
        identifier,
    ):
        parts.extend(field.encode("ascii"))
        parts.append(0)

    if payload:
        parts.extend(payload)

    return bytes(parts)