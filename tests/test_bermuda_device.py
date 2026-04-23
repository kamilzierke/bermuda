"""
Tests for BermudaDevice class in bermuda_device.py.
"""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.components.bluetooth import BaseHaScanner, BaseHaRemoteScanner

from custom_components.bermuda.bermuda_device import BermudaDevice
from custom_components.bermuda.const import ICON_DEFAULT_AREA, ICON_DEFAULT_FLOOR


@pytest.fixture
def mock_coordinator():
    """Fixture for mocking BermudaDataUpdateCoordinator."""
    coordinator = MagicMock()
    coordinator.options = {}
    coordinator.hass_version_min_2025_4 = True
    coordinator.get_manufacturer_from_id.return_value = (None, True)
    return coordinator


@pytest.fixture
def mock_scanner():
    """Fixture for mocking BaseHaScanner."""
    scanner = MagicMock(spec=BaseHaScanner)
    scanner.time_since_last_detection.return_value = 5.0
    scanner.source = "mock_source"
    return scanner


@pytest.fixture
def mock_remote_scanner():
    """Fixture for mocking BaseHaRemoteScanner."""
    scanner = MagicMock(spec=BaseHaRemoteScanner)
    scanner.time_since_last_detection.return_value = 5.0
    scanner.source = "mock_source"
    return scanner


@pytest.fixture
def bermuda_device(mock_coordinator):
    """Fixture for creating a BermudaDevice instance."""
    return BermudaDevice(address="AA:BB:CC:DD:EE:FF", coordinator=mock_coordinator)


@pytest.fixture
def bermuda_scanner(mock_coordinator):
    """Fixture for creating a BermudaDevice Scanner instance."""
    return BermudaDevice(address="11:22:33:44:55:66", coordinator=mock_coordinator)


def test_bermuda_device_initialization(bermuda_device):
    """Test BermudaDevice initialization."""
    assert bermuda_device.address == "aa:bb:cc:dd:ee:ff"
    assert bermuda_device.name.startswith("bermuda_")
    assert bermuda_device.area_icon == ICON_DEFAULT_AREA
    assert bermuda_device.floor_icon == ICON_DEFAULT_FLOOR
    assert bermuda_device.zone == "not_home"
    assert bermuda_device.in100_vcc is None
    assert bermuda_device.in100_temp_c is None
    assert bermuda_device.in100_adc_voltage is None
    assert bermuda_device.in100_raw_payload_hex is None
    assert bermuda_device.in100_last_payload_len is None
    assert bermuda_device.in100_detected is False


def test_async_as_scanner_init(bermuda_scanner, mock_scanner):
    """Test async_as_scanner_init method."""
    bermuda_scanner.async_as_scanner_init(mock_scanner)
    assert bermuda_scanner._hascanner == mock_scanner
    assert bermuda_scanner.is_scanner is True
    assert bermuda_scanner.is_remote_scanner is False


def test_async_as_scanner_update(bermuda_scanner, mock_scanner):
    """Test async_as_scanner_update method."""
    bermuda_scanner.async_as_scanner_update(mock_scanner)
    assert bermuda_scanner.last_seen > 0


def test_async_as_scanner_get_stamp(bermuda_scanner, mock_scanner, mock_remote_scanner):
    """Test async_as_scanner_get_stamp method."""
    bermuda_scanner.async_as_scanner_init(mock_scanner)
    bermuda_scanner.stamps = {"AA:BB:CC:DD:EE:FF": 123.45}

    stamp = bermuda_scanner.async_as_scanner_get_stamp("AA:bb:CC:DD:EE:FF")
    assert stamp is None

    bermuda_scanner.async_as_scanner_init(mock_remote_scanner)

    stamp = bermuda_scanner.async_as_scanner_get_stamp("AA:bb:CC:DD:EE:FF")
    assert stamp == 123.45

    stamp = bermuda_scanner.async_as_scanner_get_stamp("AA:BB:CC:DD:E1:FF")
    assert stamp is None


def test_make_name(bermuda_device):
    """Test make_name method."""
    bermuda_device.name_by_user = "Custom Name"
    name = bermuda_device.make_name()
    assert name == "Custom Name"
    assert bermuda_device.name == "Custom Name"


def test_process_advertisement(bermuda_device, bermuda_scanner):
    """Test process_advertisement method."""
    advertisement_data = MagicMock()
    bermuda_device.process_advertisement(bermuda_scanner, advertisement_data)
    assert len(bermuda_device.adverts) == 1


# def test_process_manufacturer_data(bermuda_device):
#     """Test process_manufacturer_data method."""
#     mock_advert = MagicMock()
#     mock_advert.service_uuids = ["0000abcd-0000-1000-8000-00805f9b34fb"]
#     mock_advert.manufacturer_data = [{"004C": b"\x02\x15"}]
#     bermuda_device.process_manufacturer_data(mock_advert)
#     assert bermuda_device.manufacturer == "Apple Inc."


def test_process_manufacturer_data_in100_payload(bermuda_device):
    """Decode the latest IN100 payload from manufacturer data 0x0505."""
    mock_advert = MagicMock()
    mock_advert.service_uuids = []
    mock_advert.manufacturer_data = [{0x0505: bytes.fromhex("680A4C0C6D0000")}]

    bermuda_device.process_manufacturer_data(mock_advert)

    assert bermuda_device.in100_vcc == 3.25
    assert bermuda_device.in100_temp_c == 26.36
    assert bermuda_device.in100_adc_voltage == 3.181
    assert bermuda_device.in100_raw_payload_hex == "680a4c0c6d0000"
    assert bermuda_device.in100_last_payload_len == 7
    assert bermuda_device.in100_detected is True
    assert bermuda_device.manufacturer == "InPlay / DFRobot"


def test_process_manufacturer_data_in100_payload_ignores_trailing_bytes(bermuda_device):
    """Only the first five bytes of the telemetry payload should be decoded."""
    mock_advert = MagicMock()
    mock_advert.service_uuids = []
    mock_advert.manufacturer_data = [{0x0505: bytes.fromhex("680A740C6DFFFF")}]

    bermuda_device.process_manufacturer_data(mock_advert)

    assert bermuda_device.in100_vcc == 3.25
    assert bermuda_device.in100_temp_c == 26.76
    assert bermuda_device.in100_adc_voltage == 3.181


def test_process_manufacturer_data_in100_short_payload_resets_values(bermuda_device):
    """Malformed short IN100 payloads should not raise and should clear parsed values."""
    bermuda_device.in100_vcc = 9.99
    bermuda_device.in100_temp_c = 99.99
    bermuda_device.in100_adc_voltage = 9.99

    mock_advert = MagicMock()
    mock_advert.service_uuids = []
    mock_advert.manufacturer_data = [{0x0505: bytes.fromhex("680A4C")}]

    bermuda_device.process_manufacturer_data(mock_advert)

    assert bermuda_device.in100_vcc is None
    assert bermuda_device.in100_temp_c is None
    assert bermuda_device.in100_adc_voltage is None
    assert bermuda_device.in100_raw_payload_hex == "680a4c"
    assert bermuda_device.in100_last_payload_len == 3
    assert bermuda_device.in100_detected is True


def test_process_manufacturer_data_in100_uses_only_latest_history_entry(bermuda_device):
    """Ignore stale 0x0505 payloads outside the latest manufacturer data entry."""
    mock_advert = MagicMock()
    mock_advert.service_uuids = []
    mock_advert.manufacturer_data = [
        {0x004C: bytes.fromhex("0215" + "00112233445566778899AABBCCDDEEFF" + "0001" + "0002" + "C5")},
        {0x0505: bytes.fromhex("680A4C0C6D0000")},
    ]

    bermuda_device.process_manufacturer_data(mock_advert)

    assert bermuda_device.in100_vcc is None
    assert bermuda_device.in100_temp_c is None
    assert bermuda_device.in100_adc_voltage is None
    assert bermuda_device.beacon_uuid == "00112233445566778899aabbccddeeff"
    assert bermuda_device.beacon_major == "1"
    assert bermuda_device.beacon_minor == "2"


def test_to_dict(bermuda_device):
    """Test to_dict method."""
    device_dict = bermuda_device.to_dict()
    assert isinstance(device_dict, dict)
    assert device_dict["address"] == "aa:bb:cc:dd:ee:ff"


def test_repr(bermuda_device):
    """Test __repr__ method."""
    repr_str = repr(bermuda_device)
    assert repr_str == f"{bermuda_device.name} [{bermuda_device.address}]"
