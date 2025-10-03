"""PIMA alarm system protocol implementation."""
import asyncio
import logging
import socket
import time
from typing import Optional

import crcmod

# Support both standalone and HA package imports
try:
    from .const import (
        COMMAND_FLAG,
        COMMAND_TIMEOUT,
        FRAME_END,
        FRAME_START,
        PIMA_STATE_MAP,
        RETRY_ATTEMPTS,
        UDP_KNOCKS,
    )
except ImportError:
    from const import (
        COMMAND_FLAG,
        COMMAND_TIMEOUT,
        FRAME_END,
        FRAME_START,
        PIMA_STATE_MAP,
        RETRY_ATTEMPTS,
        UDP_KNOCKS,
    )

_LOGGER = logging.getLogger(__name__)


class PimaProtocol:
    """Handle PIMA alarm system communication."""

    def __init__(self, host: str, port: int, alarm_code: str):
        """Initialize the PIMA protocol handler."""
        self.host = host
        self.port = port
        self.alarm_code = alarm_code
        self.timeout = COMMAND_TIMEOUT
        self.retry_attempts = RETRY_ATTEMPTS
        # Initialize CRC function for XMODEM
        self.crc_func = crcmod.predefined.mkCrcFun('xmodem')

    def _calculate_crc(self, data: bytes) -> bytes:
        """Calculate CRC16/XMODEM checksum."""
        crc = self.crc_func(data)
        return crc.to_bytes(2, byteorder="big")

    def _create_command(self, command: str) -> bytes:
        """Create a PIMA protocol command with framing and CRC."""
        data = command.encode("ascii")
        # CRC is calculated over 0xFF + data (not including db and dc framing)
        crc_data = COMMAND_FLAG + data
        crc = self._calculate_crc(crc_data)
        full_command = FRAME_START + COMMAND_FLAG + data + crc + FRAME_END

        _LOGGER.debug(
            "Command: '%s' -> %s",
            command,
            full_command.hex(),
        )

        return full_command

    def _parse_response(self, response: bytes) -> Optional[str]:
        """Parse a PIMA protocol response."""
        _LOGGER.debug("Response: %s", response.hex())

        if len(response) < 6:
            _LOGGER.debug("Response too short")
            return None

        if not (response.startswith(FRAME_START) and response.endswith(FRAME_END)):
            _LOGGER.debug("Missing frame delimiters")
            return None

        # Check if this is a command (db ff) or response (db only)
        if len(response) > 2 and response[1:2] == COMMAND_FLAG:
            # Command format: db ff <data> <crc> dc
            data_with_crc = response[3:-1]
        else:
            # Response format: db <data> <crc> dc
            data_with_crc = response[1:-1]

        if len(data_with_crc) < 2:
            _LOGGER.debug("Data too short")
            return None

        data = data_with_crc[:-2]
        received_crc = data_with_crc[-2:]
        calculated_crc = self._calculate_crc(data)

        if received_crc != calculated_crc:
            _LOGGER.warning("CRC mismatch")
            return None

        result = data.decode("ascii", errors="ignore")
        _LOGGER.debug("Parsed: '%s'", result)
        return result

    def _send_udp_knocks(self):
        """Send UDP wake-up packets to PIMA system."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)

            _LOGGER.debug("Sending UDP wake-up packets to %s:%s", self.host, self.port)
            for knock in UDP_KNOCKS:
                sock.sendto(knock, (self.host, self.port))
                time.sleep(0.1)

            sock.close()
        except Exception as err:
            _LOGGER.error("Failed to send UDP knocks: %s", err)
            raise

    def _connect_and_execute(self, command: str) -> Optional[str]:
        """Connect to PIMA and execute a command."""
        for attempt in range(self.retry_attempts):
            sock = None
            try:
                _LOGGER.info(
                    "Attempt %d/%d: Executing '%s'",
                    attempt + 1,
                    self.retry_attempts,
                    command,
                )

                # Send wake-up packets
                self._send_udp_knocks()
                time.sleep(1)

                # Connect via TCP
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.timeout)
                sock.connect((self.host, self.port))

                # Login
                login_cmd = self._create_command(f"PW={self.alarm_code}")
                sock.send(login_cmd)

                login_response = sock.recv(1024)
                login_result = self._parse_response(login_response)

                if not login_result or "R=1" not in login_result:
                    _LOGGER.error("Login failed: %s", login_result)
                    continue

                # Execute actual command
                actual_cmd = self._create_command(command)
                sock.send(actual_cmd)

                response = sock.recv(1024)
                result = self._parse_response(response)

                # Disconnect
                disconnect_cmd = self._create_command("DC=1")
                sock.send(disconnect_cmd)

                sock.close()
                _LOGGER.info("Command executed successfully: %s", result)
                return result

            except Exception as err:
                _LOGGER.error("Attempt %d failed: %s", attempt + 1, err)
                if sock:
                    try:
                        sock.close()
                    except:
                        pass

                if attempt < self.retry_attempts - 1:
                    time.sleep(2)

        _LOGGER.error("All %d attempts failed for '%s'", self.retry_attempts, command)
        return None

    async def async_get_status(self) -> Optional[str]:
        """Get alarm status asynchronously."""
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, self._connect_and_execute, "SS=1"
        )

        if not response:
            return None

        # Parse status from response
        if "S=" in response:
            status_code = response.split("S=")[1][0]
            return PIMA_STATE_MAP.get(status_code, "unknown")

        return "unknown"

    async def async_arm_away(self) -> bool:
        """Arm all zones (away mode)."""
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, self._connect_and_execute, "AR=1"
        )
        return response is not None and "S=1" in response

    async def async_arm_home(self) -> bool:
        """Arm home zones."""
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, self._connect_and_execute, "AR=2"
        )
        return response is not None and "S=2" in response

    async def async_arm_night(self) -> bool:
        """Arm night mode."""
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, self._connect_and_execute, "AR=3"
        )
        return response is not None and "S=3" in response

    async def async_disarm(self) -> bool:
        """Disarm alarm."""
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, self._connect_and_execute, "DA=1"
        )
        return response is not None and "S=0" in response