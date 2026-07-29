"""Sensor platform for Cotral Live."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CotralDataUpdateCoordinator

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Cotral Live sensor based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([CotralNextBusSensor(coordinator, entry)])

class CotralNextBusSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Cotral Next Bus Sensor."""

    _attr_icon = "mdi:bus"

    def __init__(self, coordinator: CotralDataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_next_bus"
        self._attr_name = f"Prossimo Bus {coordinator.stop_code}"

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor (time of next bus)."""
        next_transit, _ = self._get_next_transit()
        if not next_transit:
            return "Nessun transito"
        
        transit_info = next_transit.get("transit", {})
        # Use tempoTransito (estimated arrival time) or orarioPartenzaCorsa
        return transit_info.get("tempoTransito") or transit_info.get("orarioPartenzaCorsa", "Sconosciuto")

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        next_transit, pole_data = self._get_next_transit()
        if not next_transit:
            return {}
        
        transit_info = next_transit.get("transit", {})
        attrs = {
            "percorso": transit_info.get("percorso"),
            "destinazione": transit_info.get("arrivoCorsa"),
            "ritardo": transit_info.get("ritardo"),
            "automezzo": transit_info.get("automezzo", {}).get("codice"),
        }

        # Calculate distance if we have both coordinates
        try:
            positions = next_transit.get("vehiclePositions", [])
            if positions and pole_data and "pole" in pole_data:
                pole = pole_data["pole"]
                p_lat = float(pole.get("coordX", 0))
                p_lon = float(pole.get("coordY", 0))
                
                v_pos = positions[0]
                # Vehicle positions might be arrays of strings
                v_lat = float(v_pos["coordX"][0] if isinstance(v_pos["coordX"], list) else v_pos["coordX"])
                v_lon = float(v_pos["coordY"][0] if isinstance(v_pos["coordY"], list) else v_pos["coordY"])
                
                if p_lat and p_lon and v_lat and v_lon:
                    from homeassistant.util.location import distance
                    dist_meters = distance(p_lat, p_lon, v_lat, v_lon)
                    if dist_meters is not None:
                        attrs["distanza_km"] = round(dist_meters / 1000.0, 2)
        except (ValueError, TypeError, KeyError, IndexError):
            pass

        return attrs

    def _get_next_transit(self):
        """Helper to find the first available transit."""
        if not self.coordinator.data or "poles" not in self.coordinator.data:
            return None, None
        
        # Gather all transits from all poles
        all_transits = []
        for pole_data in self.coordinator.data["poles"]:
            for t in pole_data.get("transits", []):
                all_transits.append((t, pole_data))
        
        if not all_transits:
            return None, None
            
        # We just return the first one from the list for simplicity
        return all_transits[0]
