"""Constants for the Reef Factory Smart Level Keeper."""

DOMAIN = "reef_factory_ato"
PLATFORMS = [
    "sensor",
    "switch",
    "select",
    "button",
    "number",
    "binary_sensor",
]

WS_PATH = "controler"
WS_SUBPROTOCOL = "arduino"

PING_INTERVAL = 30  # seconds
PONG_TIMEOUT = 10  # seconds

SIGNAL_DATA_UPDATED = f"{DOMAIN}_data_updated"
SIGNAL_CONNECTION_STATE = f"{DOMAIN}_connection_state"
