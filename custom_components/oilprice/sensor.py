import logging
import voluptuous as vol

from homeassistant.helpers.entity import DeviceInfo
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import CONF_REGION

from .coordinator import MyCoordinator
from . import DOMAIN
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import callback


__version__ = "0.0.1"
_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = ["requests", "beautifulsoup4"]

COMPONENT_REPO = "https://github.com/aalavender/OilPrice/"  # 原作者项目
ICON = "mdi:gas-station"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_REGION): cv.string,
    }
)


async def async_setup_entry(hass, config, async_add_entities):
    _LOGGER.info("async_setup_platform sensor oilprice")
    # coordinator = MyCoordinator(hass, config)
    coordinator = hass.data[DOMAIN][config.entry_id]["coordinator"]
    await coordinator.async_config_entry_first_refresh()
    async_add_entities(
        [
            OilPriceSensor(
                name=sensor_name,
                region=config.data[CONF_REGION],
                coordinator=coordinator,
            )
            for sensor_name in coordinator.sensors
        ]
    )


class OilPriceSensor(SensorEntity, CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, name: str, region: str, coordinator: MyCoordinator):
        self.coordinator_name = DOMAIN + "_" + region
        super().__init__(coordinator, context=self.coordinator_name)
        self._unique_did = region + "_" + name
        self._attr_unique_id = self._unique_did
        self._attr_name = name

        self._state = self.coordinator.sensors[name]

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.coordinator_name)
            },
            name=self.coordinator_name,
            manufacturer="@YY",
            model=DOMAIN,
            sw_version="0.0.1",
            # via_device=(DOMAIN, self.coordinator_name),
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._state = self.coordinator.sensors[self._attr_name]
        self.async_write_ha_state()

    @property
    def state(self):
        return self._state

    @property
    def icon(self):
        return ICON
