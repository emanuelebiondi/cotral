"""The Cotral Live integration."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .const import (
    DOMAIN,
    CONF_API_URL,
    CONF_STOP_CODE,
    CONF_ARRIVAL_STOP_CODE,
    CONF_UPDATE_INTERVAL,
    DEFAULT_API_URL,
    DEFAULT_UPDATE_INTERVAL,
)
from .coordinator import CotralDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.DEVICE_TRACKER]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Cotral Live from a config entry."""
    
    api_url = entry.data.get(CONF_API_URL, DEFAULT_API_URL)
    stop_code = entry.data.get(CONF_STOP_CODE)
    arrival_stop_code = entry.data.get(CONF_ARRIVAL_STOP_CODE)
    update_interval = entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)

    coordinator = CotralDataUpdateCoordinator(
        hass,
        api_url=api_url,
        stop_code=stop_code,
        arrival_stop_code=arrival_stop_code,
        update_interval=update_interval,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
