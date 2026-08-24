# Apple Maps Travel Time for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)
[![GitHub Release](https://img.shields.io/github/v/release/auddis/apple-maps-travel-time)](https://github.com/auddis/apple-maps-travel-time/releases)

A custom Home Assistant integration that calculates real-time travel duration, distances, traffic slowdowns, and expected arrival times using the official **Apple Maps Server API** with your Apple Developer Account (**25,000 free API calls per day**).

---

## Features

- 🏎 **Real-time ETAs & Traffic**: Powered by Apple Maps traffic intelligence and route computation.
- 🚗 **Multi-modal Transit**: Supports `Automobile`, `Transit`, `Walking`, and `Cycling`.
- 📍 **Dynamic Tracking**: Accepts raw `lat,lon` coordinates or any Home Assistant tracking entities:
  - `person.name`
  - `device_tracker.my_phone`
  - `zone.home` / `zone.work`
- 🔒 **Automatic ES256 Token Handling**: Signs and caches Apple JWT authentication tokens in the background with zero maintenance.
- ⚙️ **Full UI Configuration**: Configurable via standard UI Config Flow and Options Flow without touching `configuration.yaml`.
- 📊 **Rich Attributes**:
  - `duration_minutes` (Sensor State)
  - `distance` (formatted in `mi` or `km` based on HA unit system)
  - `distance_meters`
  - `expected_arrival` (ISO timestamp)
  - `has_snarl` (indicates significant traffic jam/slowdown)
  - `origin_resolved` / `destination_resolved`

---

## Prerequisites (Apple Developer Account)

To use Apple Maps Server API:
1. Log into your [Apple Developer Account](https://developer.apple.com/account).
2. Go to **Certificates, Identifiers & Profiles**:
   - **Identifiers**: Click `+` → Select **Maps IDs** → Enter an Identifier (e.g. `maps.com.yourname.homeassistant`).
   - **Keys**: Click `+` → Enter a Key Name → Check **MapKit JS / Maps Server API** → Select your Maps ID → Download the `.p8` file.
3. Keep track of:
   - **Team ID**: 10-character alphanumeric ID in the upper right of your developer portal.
   - **Key ID**: 10-character Key ID for the downloaded key.
   - **Private Key**: The entire text inside the downloaded `.p8` file.

---

## Installation

### Option 1: HACS (Custom Repository)
1. Open **HACS** in Home Assistant.
2. Click the three dots `...` in the top right → **Custom repositories**.
3. Add repository URL `https://github.com/auddis/apple-maps-travel-time` (or your repo path) with Category **Integration**.
4. Click **Download**.
5. Restart Home Assistant.

### Option 2: Manual Installation
1. Copy the `custom_components/apple_maps_travel_time` folder into your Home Assistant directory:
   `<config_dir>/custom_components/apple_maps_travel_time/`
2. Restart Home Assistant.

---

## Configuration

1. In Home Assistant, go to **Settings** → **Devices & Services** → **Add Integration**.
2. Search for **Apple Maps Travel Time**.
3. Fill in the form:
   - **Name**: e.g., `Commute to Work`
   - **Team ID**: Your 10-character Apple Developer Team ID
   - **Key ID**: Your 10-character Key ID
   - **Private Key**: Paste the contents of your `.p8` file
   - **Origin**: `zone.home` or `device_tracker.my_phone` or `37.7749,-122.4194`
   - **Destination**: `zone.work` or `37.33182,-122.03118`
   - **Travel Mode**: `Automobile` (default), `Transit`, `Walking`, `Cycling`
   - **Scan Interval**: `300` (5 minutes)

---

## Example Lovelace Card

```yaml
type: entities
title: Commute
entities:
  - entity: sensor.commute_to_work
    name: Travel Time
    secondary_info: last-updated
  - type: attribute
    entity: sensor.commute_to_work
    attribute: distance
    name: Distance
  - type: attribute
    entity: sensor.commute_to_work
    attribute: expected_arrival
    name: Expected Arrival
```

---

## Example Automation (Traffic Alert)

Send a push notification if the morning commute is delayed by traffic:

```yaml
alias: "Notify: Heavy Traffic on Morning Commute"
trigger:
  - platform: numeric_state
    entity_id: sensor.commute_to_work
    above: 35
condition:
  - condition: time
    after: "07:30:00"
    before: "08:30:00"
    weekday:
      - mon
      - tue
      - wed
      - thu
      - fri
action:
  - service: notify.notify
    data:
      title: "🚗 Traffic Alert"
      message: >
        Apple Maps reports commute time is currently {{ states('sensor.commute_to_work') }} minutes (normally 25m).
```
