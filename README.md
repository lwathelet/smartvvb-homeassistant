# SmartVVB for Home Assistant

*English · [Français](README.fr.md) · [Nederlands](README.nl.md)*

[![Validate](https://github.com/lwathelet/smartvvb-homeassistant/actions/workflows/validate.yml/badge.svg)](https://github.com/lwathelet/smartvvb-homeassistant/actions/workflows/validate.yml)

Monitor and control your [SmartVVB](https://smartvvb.no) water heater from Home Assistant.

This is the Home Assistant counterpart to the SmartVVB Homey app: same backend, same features.

## Features

**Water heater** (one per device):
- Current water temperature and the setpoint set on the heater's potentiometer (read-only)
- Operation mode and away mode

**Sensors:**
- Water temperature, power draw, energy used today, cost today (NOK)
- Available hot water and water used today, in liters
- WiFi signal strength (disabled by default, enable in entity settings)

"Energy today" can be added to the Home Assistant **Energy dashboard**.

**Binary sensors:**
- Heating: on while the heater draws power
- Water safety: Safe / Unsafe (legionella indicator)

**Controls:**
- Mode select: Off, Away, Economy, Standard, Comfort, Auto, Always on
- Force on / force off buttons (temporary 2-hour override, see note below)
- Max energy per hour (disabled by default, enable in entity settings)

**Action `smartvvb.set_max_energy_schedule`:** sets a separate power limit (W) for each of the 24 hours of the day, with 0 to block an hour. Useful with electricity price integrations to avoid expensive hours:

```yaml
action: smartvvb.set_max_energy_schedule
data:
  device_id: <your SmartVVB device>
  hours: [2000, 2000, 2000, 2000, 2000, 2000, 0, 0, 0, 2000, 2000, 2000,
          2000, 2000, 2000, 2000, 0, 0, 0, 0, 2000, 2000, 2000, 2000]
```

**Diagnostics:** device page → ⋮ → Download diagnostics (credentials are removed).

**Updates:** polled every minute from the SmartVVB cloud (the backend stores one sample per minute). No webhook or external access to Home Assistant is needed.

## Important: Force on/off is a 2-hour override, not a switch

The backend's `/ForceDevice` endpoint is documented as "force device for 2 hours". It is a temporary override on top of whatever mode is currently active, not a persistent on/off state. That's why this integration exposes it as two **buttons**, not a `switch` entity: a switch implies a stable, readable on/off state, which this isn't.

## Installation

### HACS (recommended)

[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=lwathelet&repository=smartvvb-homeassistant&category=integration)

Or manually in HACS:
1. HACS → ⋮ → Custom repositories → add `https://github.com/lwathelet/smartvvb-homeassistant`, type "Integration".
2. Search for "SmartVVB", download it, and restart Home Assistant.

### Manual
Copy `custom_components/smartvvb` into your Home Assistant `custom_components` folder and restart.

## Setup
Settings → Devices & services → Add integration → SmartVVB → enter your SmartVVB username and password.

Only the resulting access token is stored (the backend's token doesn't expire); your password is never saved.

## Multiple devices
If your account has more than one SmartVVB device, every device gets its own set of entities automatically after setup. There is no need to add the integration more than once.

## Support
Report problems in [GitHub issues](https://github.com/lwathelet/smartvvb-homeassistant/issues). Attaching the diagnostics file helps.
