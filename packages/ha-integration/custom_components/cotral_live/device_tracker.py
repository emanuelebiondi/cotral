"""Device tracker platform for Cotral Live (Map markers)."""
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.components.device_tracker.const import SourceType
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
    """Set up Cotral Live device tracker based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # We will use a listener on the coordinator to dynamically add/remove trackers
    # For simplicity in this demo, we'll create a fixed set or re-create them.
    # The best practice is to track known vehicle codes and add new ones dynamically.
    
    tracked_vehicles = set()
    
    def update_trackers():
        new_entities = []
        if not coordinator.data or "poles" not in coordinator.data:
            return
            
        for pole_data in coordinator.data["poles"]:
            for transit_item in pole_data.get("transits", []):
                transit = transit_item.get("transit", {})
                vehicle_code = transit.get("automezzo", {}).get("codice")
                
                # We only track if we have a vehicle code and GPS positions
                positions = transit_item.get("vehiclePositions", [])
                if vehicle_code and str(vehicle_code) != "null" and positions:
                    if vehicle_code not in tracked_vehicles:
                        tracked_vehicles.add(vehicle_code)
                        new_entities.append(CotralBusTracker(coordinator, entry, vehicle_code))
        
        if new_entities:
            async_add_entities(new_entities)
            
    # Add initial entities
    update_trackers()
    
    # Register listener for future updates to add new buses
    coordinator.async_add_listener(update_trackers)

class CotralBusTracker(CoordinatorEntity, TrackerEntity):
    """Representation of a Cotral Bus on the map."""

    _attr_icon = "mdi:bus"

    def __init__(
        self, coordinator: CotralDataUpdateCoordinator, entry: ConfigEntry, vehicle_code: str
    ) -> None:
        """Initialize the tracker."""
        super().__init__(coordinator)
        self._entry = entry
        self._vehicle_code = vehicle_code
        self._attr_unique_id = f"{entry.entry_id}_bus_{vehicle_code}"
        self._attr_name = f"Bus Cotral {vehicle_code}"

    @property
    def source_type(self) -> SourceType:
        """Return the source type, eg gps or router, of the device."""
        return SourceType.GPS

    @property
    def latitude(self) -> float | None:
        """Return latitude value."""
        pos = self._get_position()
        if pos and "coordX" in pos and pos["coordX"]:
            try:
                # API returns string arrays sometimes for coordX
                val = pos["coordX"][0] if isinstance(pos["coordX"], list) else pos["coordX"]
                return float(val)
            except (ValueError, TypeError):
                pass
        return None

    @property
    def longitude(self) -> float | None:
        """Return longitude value."""
        pos = self._get_position()
        if pos and "coordY" in pos and pos["coordY"]:
            try:
                val = pos["coordY"][0] if isinstance(pos["coordY"], list) else pos["coordY"]
                return float(val)
            except (ValueError, TypeError):
                pass
        return None
        
    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        transit = self._get_transit_info()
        if not transit:
            return {}
        return {
            "percorso": transit.get("percorso"),
            "destinazione": transit.get("arrivoCorsa"),
            "ritardo": transit.get("ritardo"),
        }

    def _get_transit_info(self):
        """Find the transit info for this specific vehicle."""
        if not self.coordinator.data or "poles" not in self.coordinator.data:
            return None
            
        for pole_data in self.coordinator.data["poles"]:
            for transit_item in pole_data.get("transits", []):
                vehicle = transit_item.get("transit", {}).get("automezzo", {}).get("codice")
                if vehicle == self._vehicle_code:
                    return transit_item.get("transit")
        return None

    def _get_position(self):
        """Find the position info for this specific vehicle."""
        if not self.coordinator.data or "poles" not in self.coordinator.data:
            return None
            
        for pole_data in self.coordinator.data["poles"]:
            for transit_item in pole_data.get("transits", []):
                vehicle = transit_item.get("transit", {}).get("automezzo", {}).get("codice")
                if vehicle == self._vehicle_code:
                    positions = transit_item.get("vehiclePositions", [])
                    if positions:
                        return positions[0]
        return None
