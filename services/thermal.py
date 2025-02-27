"""Thermal control service for Asus TUF laptops."""

import cython
import logging
from os import system
from ProcessMappingScanner import scanAllProcessesForMapping

from config import (
    BATTERY_STATUS_PATH,
    THROTTLE_POLICY_PATH,
    THROTTLE_POLICIES,
    GAMEMODE_PATH
)
from .base import BaseService

logger = logging.getLogger('TUFUtils.ThermalService')

@cython.cclass
class ThermalService(BaseService):
    """Service for controlling thermal throttling."""
    
    def __init__(self):
        """Initialize the thermal service."""
        super().__init__()
    
    @cython.cfunc
    def is_on_battery(self) -> cython.bint:
        """Check if the laptop is running on battery."""
        try:
            status = self._read_from_file(BATTERY_STATUS_PATH)
            return 'Discharging' in status
        except Exception as e:
            logger.error(f"Failed to check battery status: {str(e)}")
            return False
    
    @cython.cfunc
    def read_gamemode(self) -> cython.int:
        """Read gamemode status."""
        try:
            return int(self._read_from_file(GAMEMODE_PATH))
        except Exception as e:
            logger.error(f"Failed to read gamemode status: {str(e)}")
            return 0
    
    @cython.cfunc
    def read_thermal_throttle_policy(self) -> cython.int:
        """Read current thermal throttle policy."""
        try:
            return int(self._read_from_file(THROTTLE_POLICY_PATH))
        except Exception as e:
            logger.error(f"Failed to read thermal throttle policy: {str(e)}")
            return 0
    
    @cython.cfunc
    def set_thermal_throttle_policy(self, policy: cython.int) -> None:
        """Set thermal throttle policy."""
        try:
            self._write_to_file(THROTTLE_POLICY_PATH, str(policy))
            logger.info(f"Thermal throttle policy set to: {policy}")
        except Exception as e:
            logger.error(f"Failed to set thermal throttle policy: {str(e)}")
    
    def update_thermal_policy(self) -> None:
        """Update thermal policy based on system state."""
        try:
            on_battery: cython.bint = self.is_on_battery()
            current_policy: cython.int = self.read_thermal_throttle_policy()
            
            if on_battery:
                if current_policy != THROTTLE_POLICIES['silent']:
                    self.set_thermal_throttle_policy(THROTTLE_POLICIES['silent'])
                    system("sysctl kernel.sched_tt_balancer_opt=3")
            else:
                gamemode: cython.int = self.read_gamemode()
                if gamemode == 1:
                    if current_policy != THROTTLE_POLICIES['boost']:
                        self.set_thermal_throttle_policy(THROTTLE_POLICIES['boost'])
                        system("sysctl kernel.sched_tt_balancer_opt=1")
                elif scanAllProcessesForMapping("clang") != {}:
                    self.set_thermal_throttle_policy(THROTTLE_POLICIES['boost'])
                elif current_policy != THROTTLE_POLICIES['normal']:
                    self.set_thermal_throttle_policy(THROTTLE_POLICIES['normal'])
                    system("sysctl kernel.sched_tt_balancer_opt=1")
            
        except Exception as e:
            logger.error(f"Error updating thermal policy: {str(e)}")
            raise
