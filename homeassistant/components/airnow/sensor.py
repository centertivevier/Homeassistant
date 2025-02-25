"""Support for the AirNow sensor service."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONCENTRATION_PARTS_PER_MILLION,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import AirNowDataUpdateCoordinator
from .const import (
    ATTR_API_AQI,
    ATTR_API_AQI_DESCRIPTION,
    ATTR_API_AQI_LEVEL,
    ATTR_API_O3,
    ATTR_API_PM25,
    DEFAULT_NAME,
    DOMAIN,
)

ATTRIBUTION = "Data provided by AirNow"

PARALLEL_UPDATES = 1

ATTR_DESCR = "description"
ATTR_LEVEL = "level"


@dataclass
class AirNowEntityDescriptionMixin:
    """Mixin for required keys."""

    value_fn: Callable[[Any], StateType]
    extra_state_attributes_fn: Callable[[Any], dict[str, str]] | None


@dataclass
class AirNowEntityDescription(SensorEntityDescription, AirNowEntityDescriptionMixin):
    """Describes Airnow sensor entity."""


SENSOR_TYPES: tuple[AirNowEntityDescription, ...] = (
    AirNowEntityDescription(
        key=ATTR_API_AQI,
        translation_key="aqi",
        icon="mdi:blur",
        native_unit_of_measurement="aqi",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get(ATTR_API_AQI),
        extra_state_attributes_fn=lambda data: {
            ATTR_DESCR: data[ATTR_API_AQI_DESCRIPTION],
            ATTR_LEVEL: data[ATTR_API_AQI_LEVEL],
        },
    ),
    AirNowEntityDescription(
        key=ATTR_API_PM25,
        translation_key="pm25",
        icon="mdi:blur",
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get(ATTR_API_PM25),
        extra_state_attributes_fn=None,
    ),
    AirNowEntityDescription(
        key=ATTR_API_O3,
        translation_key="o3",
        icon="mdi:blur",
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get(ATTR_API_O3),
        extra_state_attributes_fn=None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AirNow sensor entities based on a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = [AirNowSensor(coordinator, description) for description in SENSOR_TYPES]

    async_add_entities(entities, False)


class AirNowSensor(CoordinatorEntity[AirNowDataUpdateCoordinator], SensorEntity):
    """Define an AirNow sensor."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    entity_description: AirNowEntityDescription

    def __init__(
        self,
        coordinator: AirNowDataUpdateCoordinator,
        description: AirNowEntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = (
            f"{coordinator.latitude}-{coordinator.longitude}-{description.key.lower()}"
        )
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, self._attr_unique_id)},
            manufacturer=DEFAULT_NAME,
            name=DEFAULT_NAME,
        )

    @property
    def native_value(self) -> StateType:
        """Return the state."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Return the state attributes."""
        if self.entity_description.extra_state_attributes_fn:
            return self.entity_description.extra_state_attributes_fn(
                self.coordinator.data
            )
        return None
