"""Support for PIMA Alarm control panel."""
import logging

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_DISARMED,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .logging_utils import log_calls

_LOGGER = logging.getLogger(__name__)


@log_calls()
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PIMA alarm control panel from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities([PimaAlarm(coordinator, config_entry)])


class PimaAlarm(CoordinatorEntity, AlarmControlPanelEntity):
    """Representation of a PIMA Alarm control panel."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_code_arm_required = False
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_HOME
        | AlarmControlPanelEntityFeature.ARM_AWAY
        | AlarmControlPanelEntityFeature.ARM_NIGHT
    )

    @log_calls()
    def __init__(self, coordinator, config_entry):
        """Initialize the alarm control panel."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{config_entry.entry_id}_alarm"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": "PIMA Alarm",
            "manufacturer": "PIMA",
            "model": "Net4Pro",
        }

    @property
    def state(self):
        """Return the state of the device."""
        if not self.coordinator.data:
            return None

        pima_state = self.coordinator.data.get("state")

        # Map PIMA states to HA states
        state_map = {
            "disarmed": STATE_ALARM_DISARMED,
            "armed_away": STATE_ALARM_ARMED_AWAY,
            "armed_home": STATE_ALARM_ARMED_HOME,
            "armed_night": STATE_ALARM_ARMED_NIGHT,
        }

        return state_map.get(pima_state)

    @log_calls()
    async def async_alarm_disarm(self, code=None):
        """Send disarm command."""
        _LOGGER.debug("Disarming alarm")
        success = await self.coordinator.protocol.async_disarm()

        if success:
            # Optimistically update the state
            self.coordinator.data = {"state": "disarmed"}
            self.async_write_ha_state()
        else:
            _LOGGER.error("Failed to disarm alarm")

    @log_calls()
    async def async_alarm_arm_away(self, code=None):
        """Send arm away command."""
        _LOGGER.debug("Arming alarm (away)")
        success = await self.coordinator.protocol.async_arm_away()

        if success:
            # Optimistically update the state
            self.coordinator.data = {"state": "armed_away"}
            self.async_write_ha_state()
        else:
            _LOGGER.error("Failed to arm alarm (away)")

    @log_calls()
    async def async_alarm_arm_home(self, code=None):
        """Send arm home command."""
        _LOGGER.debug("Arming alarm (home)")
        success = await self.coordinator.protocol.async_arm_home()

        if success:
            # Optimistically update the state
            self.coordinator.data = {"state": "armed_home"}
            self.async_write_ha_state()
        else:
            _LOGGER.error("Failed to arm alarm (home)")

    @log_calls()
    async def async_alarm_arm_night(self, code=None):
        """Send arm night command."""
        _LOGGER.debug("Arming alarm (night)")
        success = await self.coordinator.protocol.async_arm_night()

        if success:
            # Optimistically update the state
            self.coordinator.data = {"state": "armed_night"}
            self.async_write_ha_state()
        else:
            _LOGGER.error("Failed to arm alarm (night)")