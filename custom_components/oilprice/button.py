import logging
from homeassistant.const import CONF_REGION
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from . import DOMAIN
from .coordinator import MyCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config, async_add_entities):
    coordinator = hass.data[DOMAIN][config.entry_id]["coordinator"]
    async_add_entities(
        [
            RefreshButton(
                name="refresh",
                region=config.data[CONF_REGION],
                coordinator=coordinator,
            )
        ]
    )


class RefreshButton(CoordinatorEntity, ButtonEntity):
    _attr_has_entity_name = True

    def __init__(self, name: str, region: str, coordinator: MyCoordinator):
        self.coordinator_name = DOMAIN + "_" + region
        super().__init__(coordinator, context=self.coordinator_name)
        self._unique_did = name
        self._attr_unique_id = self._unique_did
        self._attr_name = name

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

    async def async_press(self):
        """Press the button."""
        return await self.coordinator.async_refresh()

    # @property
    # def name(self):
    #     return self._name

    # @property
    # def entity_id(self):
    #     return f"button.{self._attr_unique_id}"
