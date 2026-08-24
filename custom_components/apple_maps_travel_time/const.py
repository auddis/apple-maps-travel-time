"""Constants for the Apple Maps Travel Time integration."""

DOMAIN = "apple_maps_travel_time"

# Configuration keys
CONF_TEAM_ID = "team_id"
CONF_KEY_ID = "key_id"
CONF_PRIVATE_KEY = "private_key"
CONF_ORIGIN = "origin"
CONF_DESTINATION = "destination"
CONF_TRAVEL_MODE = "travel_mode"
CONF_SCAN_INTERVAL = "scan_interval"

# Defaults
DEFAULT_NAME = "Apple Maps Travel Time"
DEFAULT_SCAN_INTERVAL = 300  # seconds (5 minutes)
DEFAULT_TRAVEL_MODE = "Automobile"

# Available Modes in Apple Maps Server API
TRAVEL_MODE_AUTOMOBILE = "Automobile"
TRAVEL_MODE_TRANSIT = "Transit"
TRAVEL_MODE_WALKING = "Walking"
TRAVEL_MODE_CYCLING = "Cycling"

TRAVEL_MODES = [
    TRAVEL_MODE_AUTOMOBILE,
    TRAVEL_MODE_TRANSIT,
    TRAVEL_MODE_WALKING,
    TRAVEL_MODE_CYCLING,
]

# API Constants
API_BASE_URL = "https://maps-api.apple.com/v1"
TOKEN_VALIDITY_SECONDS = 3600  # 1 hour JWT lifespan
TOKEN_REFRESH_MARGIN = 300  # refresh 5 minutes before expiration

# Sensor Attributes
ATTR_DURATION_MINUTES = "duration_minutes"
ATTR_DURATION_SECONDS = "duration_seconds"
ATTR_DISTANCE_METERS = "distance_meters"
ATTR_DISTANCE_DISPLAY = "distance"
ATTR_EXPECTED_ARRIVAL = "expected_arrival"
ATTR_ORIGIN_RESOLVED = "origin_resolved"
ATTR_DESTINATION_RESOLVED = "destination_resolved"
ATTR_ORIGIN_NAME = "origin_name"
ATTR_DESTINATION_NAME = "destination_name"
ATTR_TRAVEL_MODE = "travel_mode"
ATTR_HAS_SNARL = "has_snarl"
