import logging
from datetime import timedelta
import aiohttp
import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class CotralDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Cotral Live data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_url: str,
        stop_code: str,
        arrival_stop_code: str | None,
        update_interval: int,
    ) -> None:
        """Initialize."""
        self.api_url = api_url.rstrip("/")
        self.stop_code = stop_code
        self.arrival_stop_code = arrival_stop_code

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self):
        """Fetch data from API."""
        url = f"{self.api_url}/stops/{self.stop_code}/transits-positions"
        if self.arrival_stop_code:
            url += f"?arrivalStopCode={self.arrival_stop_code}"

        try:
            async with async_timeout.timeout(10):
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        response.raise_for_status()
                        data = await response.json()
                        return data
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
