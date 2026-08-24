"""DataUpdateCoordinator for Apple Maps Travel Time integration."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
import time
from typing import Any

import aiohttp
import jwt

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util.unit_system import METRIC_SYSTEM

from .const import (
    API_BASE_URL,
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
    CONF_DESTINATION,
    CONF_KEY_ID,
    CONF_ORIGIN,
    CONF_PRIVATE_KEY,
    CONF_TEAM_ID,
    CONF_TRAVEL_MODE,
    DEFAULT_TRAVEL_MODE,
    DOMAIN,
    TOKEN_REFRESH_MARGIN,
    TOKEN_VALIDITY_SECONDS,
)

_LOGGER = logging.getLogger(__name__)


def format_private_key(raw_key: str) -> str:
    """Format private key to valid PEM format if necessary."""
    key = raw_key.strip()
    if not key.startswith("-----BEGIN"):
        # Strip any internal whitespace/newlines and format with proper PEM headers
        cleaned = "".join(key.split())
        key = f"-----BEGIN PRIVATE KEY-----\n{cleaned}\n-----END PRIVATE KEY-----"
    return key


class AppleMapsDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Apple Maps ETA data."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry_data: dict[str, Any],
        entry_options: dict[str, Any],
        update_interval: timedelta,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self.entry_data = entry_data
        self.entry_options = entry_options

        self.team_id: str = entry_data[CONF_TEAM_ID]
        self.key_id: str = entry_data[CONF_KEY_ID]
        self.private_key_pem: str = format_private_key(entry_data[CONF_PRIVATE_KEY])

        self._cached_jwt: str | None = None
        self._jwt_expires_at: float = 0

    @property
    def origin(self) -> str:
        """Return the configured origin (options override data)."""
        return self.entry_options.get(CONF_ORIGIN, self.entry_data.get(CONF_ORIGIN, ""))

    @property
    def destination(self) -> str:
        """Return the configured destination (options override data)."""
        return self.entry_options.get(
            CONF_DESTINATION, self.entry_data.get(CONF_DESTINATION, "")
        )

    @property
    def travel_mode(self) -> str:
        """Return the configured travel mode (options override data)."""
        return self.entry_options.get(
            CONF_TRAVEL_MODE,
            self.entry_data.get(CONF_TRAVEL_MODE, DEFAULT_TRAVEL_MODE),
        )

    def _generate_jwt(self) -> str:
        """Generate ES256 signed JSON Web Token for Apple Maps Server API."""
        now = int(time.time())
        if self._cached_jwt and now < (self._jwt_expires_at - TOKEN_REFRESH_MARGIN):
            return self._cached_jwt

        expires_at = now + TOKEN_VALIDITY_SECONDS
        payload = {
            "iss": self.team_id,
            "iat": now,
            "exp": expires_at,
        }
        headers = {
            "alg": "ES256",
            "typ": "JWT",
            "kid": self.key_id,
        }

        try:
            token = jwt.encode(
                payload=payload,
                key=self.private_key_pem,
                algorithm="ES256",
                headers=headers,
            )
            self._cached_jwt = token
            self._jwt_expires_at = expires_at
            return token
        except Exception as err:
            _LOGGER.error("Failed to sign Apple Maps JWT: %s", err)
            raise UpdateFailed(f"JWT signing failed: {err}") from err

    def _resolve_location(self, location_str: str) -> tuple[float, float, str] | None:
        """Resolve entity ID or comma-separated coordinates to (lat, lon, friendly_name)."""
        loc = location_str.strip()

        # Check if it is a Home Assistant entity (zone, person, device_tracker)
        state = self.hass.states.get(loc)
        if state is not None:
            lat = state.attributes.get("latitude")
            lon = state.attributes.get("longitude")
            friendly_name = state.attributes.get("friendly_name", loc)
            if lat is not None and lon is not None:
                try:
                    return float(lat), float(lon), friendly_name
                except (ValueError, TypeError):
                    pass
            _LOGGER.warning("Entity %s has no valid GPS coordinates", loc)
            return None

        # Check if raw coordinate format: 'lat,lon' or 'lat, lon'
        if "," in loc:
            parts = loc.split(",")
            if len(parts) == 2:
                try:
                    lat = float(parts[0].strip())
                    lon = float(parts[1].strip())
                    return lat, lon, loc
                except ValueError:
                    pass

        _LOGGER.warning("Could not resolve location: %s", location_str)
        return None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch ETA from Apple Maps Server API."""
        token = await self.hass.async_add_executor_job(self._generate_jwt)

        origin_resolved = self._resolve_location(self.origin)
        destination_resolved = self._resolve_location(self.destination)

        if not origin_resolved:
            raise UpdateFailed(f"Unable to resolve origin coordinates: {self.origin}")
        if not destination_resolved:
            raise UpdateFailed(
                f"Unable to resolve destination coordinates: {self.destination}"
            )

        orig_lat, orig_lon, orig_name = origin_resolved
        dest_lat, dest_lon, dest_name = destination_resolved

        url = f"{API_BASE_URL}/eta"
        params = {
            "origin": f"{orig_lat},{orig_lon}",
            "destinations": f"{dest_lat},{dest_lon}",
            "transportType": self.travel_mode,
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        session = async_get_clientsession(self.hass)
        try:
            async with session.get(url, params=params, headers=headers, timeout=15) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise UpdateFailed(
                        f"Apple Maps API returned HTTP {resp.status}: {error_text}"
                    )

                data = await resp.json()
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Network error communicating with Apple Maps: {err}") from err

        etas = data.get("etas", [])
        if not etas:
            raise UpdateFailed("Apple Maps returned no route / ETA results for the given coordinates")

        first_eta = etas[0]
        duration_seconds = first_eta.get("expectedTravelTime", 0)
        distance_meters = first_eta.get("distanceMeters", 0)
        has_snarl = first_eta.get("hasSnarl", False)

        duration_minutes = round(duration_seconds / 60, 1)

        # Expected arrival ISO timestamp
        arrival_dt = datetime.now(timezone.utc) + timedelta(seconds=duration_seconds)
        expected_arrival = arrival_dt.isoformat()

        # Format human-friendly distance according to HA Unit System
        is_metric = self.hass.config.units is METRIC_SYSTEM
        if is_metric:
            distance_km = round(distance_meters / 1000, 2)
            distance_display = f"{distance_km} km"
        else:
            distance_mi = round(distance_meters / 1609.344, 2)
            distance_display = f"{distance_mi} mi"

        return {
            ATTR_DURATION_MINUTES: duration_minutes,
            ATTR_DURATION_SECONDS: duration_seconds,
            ATTR_DISTANCE_METERS: distance_meters,
            ATTR_DISTANCE_DISPLAY: distance_display,
            ATTR_EXPECTED_ARRIVAL: expected_arrival,
            ATTR_ORIGIN_NAME: orig_name,
            ATTR_DESTINATION_NAME: dest_name,
            ATTR_ORIGIN_RESOLVED: f"{orig_lat},{orig_lon}",
            ATTR_DESTINATION_RESOLVED: f"{dest_lat},{dest_lon}",
            ATTR_TRAVEL_MODE: self.travel_mode,
            ATTR_HAS_SNARL: has_snarl,
        }
