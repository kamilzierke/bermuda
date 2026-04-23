# Bermuda Fork for DFRobot Fermion / IN100 BLE Beacons

This fork is a focused variant of Bermuda for tracking custom DFRobot / InPlay BLE sensor beacons in Home Assistant.

The goal is simple:

- keep Bermuda's normal BLE device discovery and room-presence behavior
- keep the same Bermuda device entry
- add native decoding of a custom `0x0505` manufacturer payload used by DFRobot / InPlay IN100-based beacons
- expose extra telemetry as Home Assistant sensors without adding a new integration

## Supported hardware context

This fork targets DFRobot beacons built around the InPlay `IN100` family.

Relevant official DFRobot products:

- [Fermion: IN100 BLE Sensor Beacon (TEL0168)](https://wiki.dfrobot.com/tel0168/)
- [Fermion product page](https://www.dfrobot.com/product-2765.html)
- [Gravity: IN100 BLE Sensor Data Broadcasting Module (TEL0149)](https://wiki.dfrobot.com/tel0149/)

According to DFRobot's documentation, these beacons:

- use low-power Bluetooth 5.3
- have a built-in 11-bit ADC
- can broadcast data from digital, analog, and in the Fermion variant also I2C sensors
- support `iBeacon`, `Eddystone`, and `Custom` advertising formats
- are configured through the NanoBeacon graphical tool rather than a normal firmware workflow
- use manufacturer-specific data in custom mode, and DFRobot's own example shows manufacturer number `0505`

DFRobot's official getting-started example also shows:

- custom advertising configured through `Manufacturer Specific Data`
- big-endian encoding for appended values
- example payload interpretation where `0505` is the manufacturer number
- the module is effectively a one-time burn workflow, with `Run in RAM` recommended for testing before final burn

## What this fork adds

This fork extends Bermuda so that a normal Bermuda-tracked BLE device can expose extra telemetry from the latest `0x0505` manufacturer payload.

Added sensors on the existing Bermuda device:

- `VCC`
- `Temperature`
- `ADC Voltage`

Added internal telemetry fields in `bermuda.dump_devices`:

- `in100_vcc`
- `in100_temp_c`
- `in100_adc_voltage`
- `in100_raw_payload_hex`
- `in100_last_payload_len`
- `in100_detected`

What stays unchanged:

- no new Home Assistant integration
- no extra dependency
- no separate HA device entry
- no change to Bermuda's overall discovery / config flow
- no intentional change to existing iBeacon or Private BLE handling

## Payload profile used by this fork

This fork decodes a custom payload profile carried under manufacturer ID `0x0505`.

Important:

- this is a custom beacon profile used in this fork, not a claim that every DFRobot IN100 beacon ships with this exact layout by default
- DFRobot's official docs confirm the `0505` manufacturer number and custom manufacturer-data workflow
- this fork adds decoding for one specific burned/custom payload layout

Decoded bytes:

- byte `0`: VCC raw, unsigned 8-bit
- bytes `1..2`: temperature raw, signed 16-bit, big-endian
- bytes `3..4`: ADC raw, unsigned 16-bit, big-endian

Conversions:

- `VCC = byte0 / 32.0`
- `Temperature = signed_be16(bytes1_2) / 100.0`
- `ADC Voltage = uint16_be(bytes3_4) / 1000.0`

Parser behavior:

- only the latest manufacturer-data entry is used
- only the first 5 bytes are decoded
- trailing bytes are ignored on purpose
- short or malformed payloads do not raise exceptions

The decision to ignore trailing bytes is deliberate. Some custom-burned beacons can carry duplicated or malformed tail data while the first 5 bytes remain valid.

## Why ADC Voltage is useful here

DFRobot positions these boards as BLE sensor beacons with ADC-based sensor acquisition. In this fork, the `ADC Voltage` field is used as battery-voltage style telemetry because that is how the custom beacon profile was burned.

In practice this gives a very useful per-device view in Home Assistant:

- room / nearest scanner from Bermuda
- distance from Bermuda
- chip supply voltage
- temperature
- beacon ADC / battery voltage

## Typical use with Home Assistant

1. Configure and burn the DFRobot / InPlay beacon with a custom `0x0505` manufacturer payload profile.
2. Let Bermuda discover the beacon normally as a BLE device.
3. Add that device to Bermuda tracking as usual.
4. Use the same Bermuda device in Home Assistant for:
   - `Area`
   - `Distance`
   - `VCC`
   - `Temperature`
   - `ADC Voltage`

## Source notes

The DFRobot sources used to shape this fork-specific behavior are:

- [Fermion: IN100 BLE Sensor Beacon wiki](https://wiki.dfrobot.com/tel0168/)
- [DFRobot Fermion product page](https://www.dfrobot.com/product-2765.html)
- [DFRobot getting-started guide for custom manufacturer data](https://wiki.dfrobot.com/tel0168/docs/22072)
- [Gravity: IN100 BLE Sensor Data Broadcasting Module wiki](https://wiki.dfrobot.com/tel0149/)

These sources describe the IN100 beacon family, custom manufacturer data, big-endian configuration, and the `0505` manufacturer-number example that this fork builds on.
