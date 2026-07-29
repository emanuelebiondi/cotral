"""Config flow for Cotral Live integration."""
import logging
import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    SelectOptionDict,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .const import (
    DOMAIN,
    CONF_API_URL,
    CONF_STOP_CODE,
    CONF_ARRIVAL_STOP_CODE,
    CONF_UPDATE_INTERVAL,
    DEFAULT_API_URL,
    DEFAULT_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

STEP_SEARCH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_URL, default=DEFAULT_API_URL): str,
        vol.Required("origin_search"): str,
        vol.Optional("destination_search"): str,
    }
)

async def _fetch_stops(api_url: str, search_query: str) -> list[dict]:
    """Fetch stops from the API."""
    url = f"{api_url.rstrip('/')}/stops/{search_query}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    return await response.json()
    except Exception as err:
        _LOGGER.error("Error fetching stops for %s: %s", search_query, err)
    return []

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Cotral Live."""

    VERSION = 1

    def __init__(self):
        """Initialize."""
        self.api_url = None
        self.origin_stops = []
        self.dest_stops = []

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step - Search stops."""
        errors = {}

        if user_input is not None:
            self.api_url = user_input[CONF_API_URL]
            origin_query = user_input["origin_search"]
            dest_query = user_input.get("destination_search")

            self.origin_stops = await _fetch_stops(self.api_url, origin_query)
            if not self.origin_stops:
                errors["origin_search"] = "no_stops_found"
            
            if dest_query:
                self.dest_stops = await _fetch_stops(self.api_url, dest_query)
                if not self.dest_stops:
                    errors["destination_search"] = "no_stops_found"

            if not errors:
                return await self.async_step_select_stops()

        return self.async_show_form(
            step_id="user", data_schema=STEP_SEARCH_SCHEMA, errors=errors
        )

    async def async_step_select_stops(self, user_input=None) -> FlowResult:
        """Handle stop selection from search results."""
        if user_input is not None:
            data = {
                CONF_API_URL: self.api_url,
                CONF_STOP_CODE: user_input[CONF_STOP_CODE],
                CONF_ARRIVAL_STOP_CODE: user_input.get(CONF_ARRIVAL_STOP_CODE),
                CONF_UPDATE_INTERVAL: user_input[CONF_UPDATE_INTERVAL],
            }
            return self.async_create_entry(
                title=f"Cotral Stop {data[CONF_STOP_CODE]}",
                data=data,
            )

        origin_options = [
            SelectOptionDict(value=s["codiceStop"], label=f"{s['nomeStop']} ({s['codiceStop']})")
            for s in self.origin_stops
        ]
        
        schema = {
            vol.Required(CONF_STOP_CODE): SelectSelector(
                SelectSelectorConfig(options=origin_options, mode=SelectSelectorMode.DROPDOWN)
            )
        }

        if self.dest_stops:
            dest_options = [
                SelectOptionDict(value=s["codiceStop"], label=f"{s['nomeStop']} ({s['codiceStop']})")
                for s in self.dest_stops
            ]
            schema[vol.Optional(CONF_ARRIVAL_STOP_CODE)] = SelectSelector(
                SelectSelectorConfig(options=dest_options, mode=SelectSelectorMode.DROPDOWN)
            )
            
        schema[vol.Required(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL)] = NumberSelector(
            NumberSelectorConfig(min=10, max=600, step=10, mode=NumberSelectorMode.BOX)
        )

        return self.async_show_form(
            step_id="select_stops",
            data_schema=vol.Schema(schema),
        )
