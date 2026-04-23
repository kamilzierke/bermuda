"""Tests for Bermuda sensor entities."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from homeassistant.components.sensor.const import SensorDeviceClass, SensorStateClass
from homeassistant.const import EntityCategory, UnitOfTemperature
from homeassistant.helpers.dispatcher import async_dispatcher_send

from custom_components.bermuda.bermuda_device import BermudaDevice
from custom_components.bermuda.const import DOMAIN, SIGNAL_DEVICE_NEW
from custom_components.bermuda.sensor import (
    BermudaSensorAdcVoltage,
    BermudaSensorTemperature,
    BermudaSensorVcc,
    async_setup_entry,
)


async def test_device_new_creates_in100_sensor_entities(hass) -> None:
    """Ensure the per-device setup path creates the IN100 sensors."""
    coordinator = MagicMock()
    coordinator.hass = hass
    coordinator.options = {}
    coordinator.get_manufacturer_from_id.return_value = (None, True)
    coordinator.have_floors = False
    coordinator.scanner_list = []
    coordinator.get_scanners = []
    coordinator.sensor_created = MagicMock()
    coordinator.data = {}

    device = BermudaDevice(address="AA:BB:CC:DD:EE:FF", coordinator=coordinator)
    device.in100_vcc = 3.25
    device.in100_temp_c = 26.36
    device.in100_adc_voltage = 3.181
    coordinator.devices = {device.address: device}

    entry = MagicMock()
    entry.runtime_data = SimpleNamespace(coordinator=coordinator)
    entry.async_on_unload = MagicMock()

    created_entities = []

    def async_add_entities(entities, update_before_add=False) -> None:
        created_entities.extend(entities)

    await async_setup_entry(hass, entry, async_add_entities)
    async_dispatcher_send(hass, SIGNAL_DEVICE_NEW, device.address)
    await hass.async_block_till_done()

    vcc_entities = [entity for entity in created_entities if isinstance(entity, BermudaSensorVcc)]
    temp_entities = [entity for entity in created_entities if isinstance(entity, BermudaSensorTemperature)]
    adc_entities = [entity for entity in created_entities if isinstance(entity, BermudaSensorAdcVoltage)]

    assert len(vcc_entities) == 1
    assert len(temp_entities) == 1
    assert len(adc_entities) == 1

    vcc_entity = vcc_entities[0]
    temp_entity = temp_entities[0]
    adc_entity = adc_entities[0]

    assert vcc_entity.unique_id == f"{device.unique_id}_vcc"
    assert vcc_entity.name == "VCC"
    assert vcc_entity.native_value == 3.25
    assert vcc_entity.device_class == SensorDeviceClass.VOLTAGE
    assert vcc_entity.native_unit_of_measurement == "V"
    assert vcc_entity.state_class == SensorStateClass.MEASUREMENT
    assert vcc_entity.entity_registry_enabled_default is True
    assert vcc_entity.entity_category == EntityCategory.DIAGNOSTIC
    assert vcc_entity.device_info["identifiers"] == {(DOMAIN, device.unique_id)}

    assert temp_entity.unique_id == f"{device.unique_id}_temperature"
    assert temp_entity.name == "Temperature"
    assert temp_entity.native_value == 26.36
    assert temp_entity.device_class == SensorDeviceClass.TEMPERATURE
    assert temp_entity.native_unit_of_measurement == UnitOfTemperature.CELSIUS
    assert temp_entity.state_class == SensorStateClass.MEASUREMENT
    assert temp_entity.entity_registry_enabled_default is True
    assert temp_entity.device_info["identifiers"] == {(DOMAIN, device.unique_id)}

    assert adc_entity.unique_id == f"{device.unique_id}_adc_voltage"
    assert adc_entity.name == "ADC Voltage"
    assert adc_entity.native_value == 3.181
    assert adc_entity.device_class == SensorDeviceClass.VOLTAGE
    assert adc_entity.native_unit_of_measurement == "V"
    assert adc_entity.state_class == SensorStateClass.MEASUREMENT
    assert adc_entity.entity_registry_enabled_default is True
    assert adc_entity.device_info["identifiers"] == {(DOMAIN, device.unique_id)}

    coordinator.sensor_created.assert_called_once_with(device.address)
