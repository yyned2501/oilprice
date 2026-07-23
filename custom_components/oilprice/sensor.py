import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_REGION
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN
from .coordinator import MyCoordinator

_LOGGER = logging.getLogger(__name__)

# Define sensor icons, units, and English display names.
# Chinese translations are provided via translations/zh-Hans.json entity section.
ICON_GAS_STATION = "mdi:gas-station"

SENSOR_TYPES: Dict[str, Dict[str, Any]] = {
    "89": {"name": "89# Gasoline", "unit": "元/升", "icon": ICON_GAS_STATION},
    "92": {"name": "92# Gasoline", "unit": "元/升", "icon": ICON_GAS_STATION},
    "95": {"name": "95# Gasoline", "unit": "元/升", "icon": ICON_GAS_STATION},
    "98": {"name": "98# Gasoline", "unit": "元/升", "icon": ICON_GAS_STATION},
    "0": {"name": "0# Diesel", "unit": "元/升", "icon": ICON_GAS_STATION},
    "next_change_date": {"name": "Next Adjustment", "unit": None, "icon": "mdi:calendar-clock"},
    "tips": {"name": "Price Forecast", "unit": None, "icon": "mdi:alert-decagram-outline"},
}


async def async_setup_entry(hass, config_entry, async_add_entities) -> None:
    """Set up oil price sensor entities from the config entry."""
    _LOGGER.info("正在加载今日油价传感器...")
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    # Always register all sensor entities regardless of whether coordinator has data yet.
    # Data will be populated asynchronously; entities show "unavailable" until then.
    async_add_entities(
        [
            OilPriceSensor(
                name=sensor_key,
                region=config_entry.data[CONF_REGION],
                coordinator=coordinator,
            )
            for sensor_key in SENSOR_TYPES
        ]
    )


class OilPriceSensor(CoordinatorEntity[MyCoordinator], SensorEntity):
    """Oil price and adjustment notification sensor backed by DataUpdateCoordinator."""

    _attr_has_entity_name = True

    def __init__(self, name: str, region: str, coordinator: MyCoordinator) -> None:
        """Initialize the sensor and bind it to the coordinator."""
        self.coordinator_name = f"{DOMAIN}_{region}"
        super().__init__(coordinator, context=self.coordinator_name)

        self._raw_key = name
        self._attr_unique_id = f"{region}_{name}"
        self._attr_translation_key = f"oil_{name}"

        # Match metadata for UI display
        meta = SENSOR_TYPES.get(name, {})
        self._attr_name = meta.get("name", name)
        self._attr_native_unit_of_measurement = meta.get("unit")
        self._attr_icon = meta.get("icon", ICON_GAS_STATION)

        # Enable measurement statistics for fuel price entities so HA can draw history charts
        if name in ("89", "92", "95", "98", "0"):
            self._attr_state_class = "measurement"

    @property
    def native_value(self) -> Optional[Any]:
        """Read the latest value from the coordinator cache — single source of truth."""
        if self.coordinator.data:
            return self.coordinator.data.get(self._raw_key)
        return None

    @property
    def device_info(self) -> DeviceInfo:
        """Aggregate all sensors for the same region into a single device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator_name)},
            name=f"今日油价 - {self.coordinator_name}",
            manufacturer="@YY",
            model=DOMAIN,
            sw_version="1.0.4",
        )
