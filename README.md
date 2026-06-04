# Reef Factory Smart Level Keeper for Home Assistant

A fully local Home Assistant integration for the Reef Factory Smart Level Keeper (ATO).

This integration was developed by reverse engineering the device's local WebSocket protocol and does not require cloud access.

> ⚠️ This integration has currently been tested against Reef Factory Smart Level Keeper firmware version **1.0.0**.

---

## Features

### Monitoring

* Water level status
* Float switch state
* Pump running status
* Today's top-up volume
* Refill runtime
* Calibration volume
* Next calibration date
* Firmware version

### Control

* LED enable / disable
* ATO mode selection
* Maximum refill runtime configuration
* Manual refill operation

### Calibration

The complete calibration workflow can be performed from Home Assistant:

1. Select calibration runtime
2. Start calibration
3. Measure delivered water volume
4. Enter calibration volume
5. Select calibration interval
6. Save calibration

---

## Installation

### Manual Installation

Copy:

```text
custom_components/reef_factory_ato
```

into your Home Assistant configuration directory:

```text
config/custom_components/
```

Restart Home Assistant.

Navigate to:

```text
Settings → Devices & Services → Add Integration
```

Search for:

```text
Reef Factory Smart Level Keeper
```

Enter the IP address of the device.

---

## Entities

### Sensors

* Water Level
* Float State
* Pump Running
* Refill Runtime
* Today's Top-Up Volume
* Calibration Volume
* Next Calibration Date
* Firmware Version

### Controls

* ATO LED
* ATO Mode
* Max Refill Runtime
* Calibration Runtime
* Calibration Volume
* Calibration Interval
* Manual Refill Volume

### Actions

* Start Calibration
* Save Calibration
* Start Manual Refill

---

## Supported Hardware

Currently tested with:

* Reef Factory Smart Level Keeper

Firmware tested:

* 1.0.0

Additional firmware versions may work but have not yet been validated.

---

## Design Goals

The objective of this project is to provide a fully local Home Assistant integration that replicates the core functionality of the official Reef Factory application while avoiding reliance on external cloud services.

Benefits include:

* Local operation
* Faster response times
* Reduced cloud dependency
* Native Home Assistant automations and dashboards
* Greater visibility into device status and operation

---

## Credits

This integration was originally inspired by and partially based on the excellent work by Dominik Hartl:

https://github.com/dominikhartl/ha-reeffactory-ph

While the original project focused on the Reef Factory pH Meter, it provided a valuable foundation for understanding the Reef Factory local communication protocol and Home Assistant integration structure.

The Smart Level Keeper integration has since been extensively redesigned, expanded, and adapted to support the Reef Factory Smart Level Keeper (ATO), including:

* Native Smart Level Keeper protocol support
* Water level monitoring
* Float switch state monitoring
* Pump runtime and top-up volume tracking
* Calibration workflow
* Manual refill control
* Maximum runtime configuration
* LED and operating mode control
* Firmware version reporting

Special thanks to Dominik Hartl for publishing the original Reef Factory Home Assistant integration and providing the inspiration for this project.

---

## Disclaimer

This project is unofficial and is not affiliated with, endorsed by, or supported by Reef Factory.

Use at your own risk.

---

## License

This project is licensed under the MIT License.
