"""Sensor platform for Apple Maps Travel Time integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_DESTINATION_NAME,
    ATTR_DESTINATION_RESOLVED,
    ATTR_DISTANCE_DISPLAY,
    ATTR_DISTANCE_METERS,
    ATTR_DURATION_MINUTES,
    ATTR_DURATION_SECONDS,
    ATTR_EXPECTED_ARRIVAL,
    ATTR_HAS_SNARL,
    ATTR_ORIGIN_NAME,
    ATTR_ORIGIN_RESOLVED,
    ATTR_TRAVEL_MODE,
    DOMAIN,
    TRAVEL_MODE_AUTOMOBILE,
    TRAVEL_MODE_CYCLING,
    TRAVEL_MODE_TRANSIT,
    TRAVEL_MODE_WALKING,
)
from .coordinator import AppleMapsDataUpdateCoordinator

ICONS = {
    TRAVEL_MODE_AUTOMOBILE: "mdi:car",
    TRAVEL_MODE_TRANSIT: "mdi:bus",
    TRAVEL_MODE_WALKING: "mdi:walk",
    TRAVEL_MODE_CYCLING: "mdi:bike",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Apple Maps sensor platform."""
    coordinator: AppleMapsDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AppleMapsTravelTimeSensor(coordinator, entry)], True)


class AppleMapsTravelTimeSensor(
    CoordinatorEntity[AppleMapsDataUpdateCoordinator], SensorEntity
):
    """Representation of an Apple Maps Travel Time sensor."""

    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AppleMapsDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_travel_time"
        self._attr_name = entry.title

    @property
    def icon(self) -> str:
        """Return dynamic icon based on current travel mode."""
        mode = self.coordinator.data.get(ATTR_TRAVEL_MODE, TRAVEL_MODE_AUTOMOBILE)
        return ICONS.get(mode, "mdi:map-marker-distance")

    @property
    def native_value(self) -> float | None:
        """Return the estimated travel duration in minutes."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(ATTR_DURATION_MINUTES)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return detailed route attributes."""
        if not self.coordinator.data:
            return {}

        return {
            ATTR_DURATION_MINUTES: self.coordinator.data.get(ATTR_DURATION_MINUTES),
            ATTR_DURATION_SECONDS: self.coordinator.data.get(ATTR_DURATION_SECONDS),
            ATTR_DISTANCE_METERS: self.coordinator.data.get(ATTR_DISTANCE_METERS),
            ATTR_DISTANCE_DISPLAY: self.coordinator.data.get(ATTR_DISTANCE_DISPLAY),
            ATTR_EXPECTED_ARRIVAL: self.coordinator.data.get(ATTR_EXPECTED_ARRIVAL),
            ATTR_ORIGIN_NAME: self.coordinator.data.get(ATTR_ORIGIN_NAME),
            ATTR_DESTINATION_NAME: self.coordinator.data.get(ATTR_DESTINATION_NAME),
            ATTR_ORIGIN_RESOLVED: self.coordinator.data.get(ATTR_ORIGIN_RESOLVED),
            ATTR_DESTINATION_RESOLVED: self.coordinator.data.get(ATTR_DESTINATION_RESOLVED),
            ATTR_TRAVEL_MODE: self.coordinator.data.get(ATTR_TRAVEL_MODE),
            ATTR_HAS_SNARL: self.coordinator.data.get(ATTR_HAS_SNARL),
        }
