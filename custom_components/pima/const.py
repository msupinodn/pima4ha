"""Constants for the PIMA Alarm integration."""

DOMAIN = "pima"

# Configuration
CONF_ALARM_CODE = "alarm_code"

# Defaults
DEFAULT_PORT = 10150
DEFAULT_SCAN_INTERVAL = 600  # 10 minutes

# Minimum/Maximum values
MIN_SCAN_INTERVAL = 300  # 5 minutes
MAX_SCAN_INTERVAL = 3600  # 1 hour

# Timeouts
COMMAND_TIMEOUT = 30  # 30 seconds for command execution
RETRY_ATTEMPTS = 3

# States mapping
STATE_DISARMED = "disarmed"
STATE_ARMED_AWAY = "armed_away"
STATE_ARMED_HOME = "armed_home"
STATE_ARMED_NIGHT = "armed_night"

PIMA_STATE_MAP = {
    "0": STATE_DISARMED,
    "1": STATE_ARMED_AWAY,
    "2": STATE_ARMED_HOME,
    "3": STATE_ARMED_NIGHT,
}

# Protocol constants
FRAME_START = b'\xdb'
FRAME_END = b'\xdc'
COMMAND_FLAG = b'\xff'

# Wake-up UDP packets (knock sequence)
UDP_KNOCKS = [
    bytes.fromhex("96b13531814f5d34af3dd5cb71399e386f044fd5c95219b91fb66de33de070b7"),
    bytes.fromhex("496eef27096354c430a9826fa8fc45e388a24adb5e78c1d62cd0aa4d7cd395fe")
]