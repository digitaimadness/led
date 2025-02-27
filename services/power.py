"""Power and fan control service for Asus TUF laptops."""

import cython
import logging
import asyncio
from typing import Dict, Tuple

from config import (
    FAN_CONTROL_PATH,
    FAN_MODES,
    FAN_TEMP_THRESHOLD,
    FAN_UPDATE_INTERVAL,
    POWER_PROFILE_PATH,
    POWER_PROFILES,
    GPU_POWER_PATH,
    GPU_MODES,
    TEMP_PATHS
)
from .base import BaseService

logger = logging.getLogger('TUFUtils.PowerService')

@cython.cclass
class PowerService(BaseService):
    """Service for controlling power profiles, fan speeds, and GPU power states."""
    
    def __init__(self):
        """Initialize the power service."""
        super().__init__()
    
    @cython.cfunc
    def read_temperatures(self) -> Tuple[float, float]:
        """Read CPU and GPU temperatures."""
        try:
            cpu_temp = float(self._read_from_file(TEMP_PATHS['cpu'])) / 1000.0
            gpu_temp = float(self._read_from_file(TEMP_PATHS['gpu'])) / 1000.0
            return cpu_temp, gpu_temp
        except Exception as e:
            logger.error(f"Failed to read temperatures: {str(e)}")
            return 0.0, 0.0
    
    @cython.cfunc
    def get_fan_mode(self) -> cython.int:
        """Get current fan mode."""
        try:
            return int(self._read_from_file(FAN_CONTROL_PATH))
        except Exception as e:
            logger.error(f"Failed to read fan mode: {str(e)}")
            return FAN_MODES['normal']
    
    @cython.cfunc
    def set_fan_mode(self, mode: cython.int) -> None:
        """Set fan mode."""
        try:
            self._write_to_file(FAN_CONTROL_PATH, str(mode))
            logger.info(f"Fan mode set to: {mode}")
        except Exception as e:
            logger.error(f"Failed to set fan mode: {str(e)}")
    
    @cython.cfunc
    def get_power_profile(self) -> cython.int:
        """Get current power profile."""
        try:
            return int(self._read_from_file(POWER_PROFILE_PATH))
        except Exception as e:
            logger.error(f"Failed to read power profile: {str(e)}")
            return POWER_PROFILES['balanced']
    
    @cython.cfunc
    def set_power_profile(self, profile: cython.int) -> None:
        """Set power profile."""
        try:
            self._write_to_file(POWER_PROFILE_PATH, str(profile))
            logger.info(f"Power profile set to: {profile}")
        except Exception as e:
            logger.error(f"Failed to set power profile: {str(e)}")
    
    @cython.cfunc
    def get_gpu_mode(self) -> cython.int:
        """Get current GPU power mode."""
        try:
            return int(self._read_from_file(GPU_POWER_PATH))
        except Exception as e:
            logger.error(f"Failed to read GPU mode: {str(e)}")
            return GPU_MODES['standard']
    
    @cython.cfunc
    def set_gpu_mode(self, mode: cython.int) -> None:
        """Set GPU power mode."""
        try:
            self._write_to_file(GPU_POWER_PATH, str(mode))
            logger.info(f"GPU mode set to: {mode}")
        except Exception as e:
            logger.error(f"Failed to set GPU mode: {str(e)}")
    
    async def auto_fan_control(self) -> None:
        """Automatically control fan speed based on temperature."""
        while True:
            try:
                cpu_temp, gpu_temp = self.read_temperatures()
                max_temp = max(cpu_temp, gpu_temp)
                current_mode = self.get_fan_mode()
                
                # Switch to boost mode if temperature exceeds threshold
                if max_temp >= FAN_TEMP_THRESHOLD and current_mode != FAN_MODES['boost']:
                    self.set_fan_mode(FAN_MODES['boost'])
                # Switch back to normal mode if temperature is well below threshold
                elif max_temp < (FAN_TEMP_THRESHOLD - 5) and current_mode == FAN_MODES['boost']:
                    self.set_fan_mode(FAN_MODES['normal'])
                
            except Exception as e:
                logger.error(f"Error in auto fan control: {str(e)}")
            finally:
                await asyncio.sleep(FAN_UPDATE_INTERVAL)
    
    def optimize_power_settings(self, on_battery: bool, performance_mode: bool) -> None:
        """Optimize power settings based on power source and performance mode."""
        try:
            if on_battery:
                # On battery: optimize for battery life
                self.set_power_profile(POWER_PROFILES['powersave'])
                self.set_gpu_mode(GPU_MODES['eco'])
                if not performance_mode:
                    self.set_fan_mode(FAN_MODES['silent'])
            else:
                if performance_mode:
                    # Performance mode: maximize performance
                    self.set_power_profile(POWER_PROFILES['performance'])
                    self.set_gpu_mode(GPU_MODES['boost'])
                    self.set_fan_mode(FAN_MODES['boost'])
                else:
                    # Normal operation: balanced settings
                    self.set_power_profile(POWER_PROFILES['balanced'])
                    self.set_gpu_mode(GPU_MODES['standard'])
                    self.set_fan_mode(FAN_MODES['normal'])
            
        except Exception as e:
            logger.error(f"Error optimizing power settings: {str(e)}")
            raise
