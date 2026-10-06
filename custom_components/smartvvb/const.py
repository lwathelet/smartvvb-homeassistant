"""Constants for the SmartVVB integration."""
from __future__ import annotations

DOMAIN = "smartvvb"

API_BASE_URL = "https://frontend.smartvvb.no/api"

# Polling is the only update source. The backend stores one sample per minute
# (samples_minute), so polling faster would gain nothing.
POLL_INTERVAL_SECONDS = 60

# setpoint/volume (GetUserDevices) only change when the potentiometer is turned
# or the device is edited, so they are refreshed far less often than the poll.
DEVICE_LIST_REFRESH_SECONDS = 1800

# Homey picker values <-> SmartVVB backend mode strings, per smartvvb.no/mode.php.
MODE_API_VALUES = {
    "off": "Off",
    "away": "Away",
    "economy": "Eco",
    "standard": "Standard",
    "comfort": "Comfort",
    "auto": "Auto",
    "always_on": "Always",
}
MODE_HA_VALUES = {v: k for k, v in MODE_API_VALUES.items()}

# /ForceDevice is documented as "force device for 2 hours" — a temporary
# override, not a persistent on/off switch. Exposed as buttons, not a switch.
FORCE_ON = "ON"
FORCE_OFF = "OFF"
