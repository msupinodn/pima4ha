"""The PIMA Alarm integration."""
import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_ALARM_CODE, DEFAULT_SCAN_INTERVAL, DOMAIN
from .pima_protocol import PimaProtocol

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.ALARM_CONTROL_PANEL]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PIMA Alarm from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    alarm_code = entry.data[CONF_ALARM_CODE]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    # Create protocol handler
    protocol = PimaProtocol(host, port, alarm_code)

    # Create coordinator for background updates
    coordinator = PimaDataUpdateCoordinator(
        hass,
        protocol,
        scan_interval,
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class PimaDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching PIMA alarm data."""

    def __init__(
        self,
        hass: HomeAssistant,
        protocol: PimaProtocol,
        scan_interval: int,
    ):
        """Initialize the coordinator."""
        self.protocol = protocol

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self):
        """Fetch data from PIMA alarm system."""
        try:
            _LOGGER.debug("Polling PIMA alarm status")
            status = await self.protocol.async_get_status()

            if status is None:
                raise UpdateFailed("Failed to get status from PIMA alarm")

            _LOGGER.debug("PIMA status: %s", status)
            return {"state": status}

        except Exception as err:
            _LOGGER.error("Error communicating with PIMA alarm: %s", err)
            raise UpdateFailed(f"Error communicating with PIMA alarm: {err}")