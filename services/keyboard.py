"""Keyboard LED control service for Asus TUF laptops."""

import cython
import logging
import asyncio
import aiofiles
from time import time
from functools import lru_cache
from typing import Dict

from config import (
    KBBL_PATHS,
    LED_BRIGHTNESS_NORMAL,
    LED_BRIGHTNESS_DIM,
    LED_MAX_VALUE,
    CPU_UPDATE_INTERVAL
)
from .base import BaseService

logger = logging.getLogger('TUFUtils.KeyboardService')

@cython.cclass
class KeyboardService(BaseService):
    """Service for controlling keyboard LED."""
    
    _last_cpu_stats: Dict[str, float]
    _last_cpu_time: float
    
    def __init__(self):
        """Initialize the keyboard service."""
        super().__init__()
        self._last_cpu_stats = {}
        self._last_cpu_time = time()
        self._initialize_keyboard()
    
    def _initialize_keyboard(self):
        """Initialize keyboard backlight settings."""
        try:
            self._write_to_file(KBBL_PATHS['mode'], "0")
            self._write_to_file(KBBL_PATHS['speed'], "0")
            self._write_to_file(KBBL_PATHS['flags'], "ff")
            logger.info("Keyboard LED initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize keyboard LED: {str(e)}")
            raise
    
    @cython.cfunc
    @lru_cache(maxsize=1)
    def _calculate_cpu_utilization(self) -> int:
        """Calculate CPU utilization with caching."""
        try:
            current_time = time()
            # Only update if enough time has passed
            if current_time - self._last_cpu_time >= CPU_UPDATE_INTERVAL:
                with self._get_cached_file('/proc/stat') as f:
                    fields = [float(column) for column in f.readline().strip().split()[1:]]
                idle, total = fields[3], sum(fields)
                
                if self._last_cpu_stats:
                    idle_delta = idle - self._last_cpu_stats['idle']
                    total_delta = total - self._last_cpu_stats['total']
                    utilization = int((1.0 - idle_delta/total_delta) * 100.0)
                else:
                    utilization = 0
                
                self._last_cpu_stats = {'idle': idle, 'total': total}
                self._last_cpu_time = current_time
                
                return utilization
            else:
                # Return last calculated value if not enough time has passed
                return int((1.0 - (self._last_cpu_stats.get('idle_delta', 0) / 
                                 self._last_cpu_stats.get('total_delta', 1))) * 100.0)
        except Exception as e:
            logger.error(f"Error calculating CPU utilization: {str(e)}")
            return 0
    
    async def _write_to_file_async(self, filepath: str, content: str) -> None:
        """Write content to a file asynchronously."""
        try:
            async with aiofiles.open(filepath, "w") as f:
                await f.write(content)
        except IOError as e:
            logger.error(f"Failed to write to {filepath}: {str(e)}")
            raise
    
    async def set_led_async(self, color: str, brightness: int) -> None:
        """Set LED color and brightness asynchronously."""
        try:
            await self._write_to_file_async(KBBL_PATHS[color], str(brightness))
        except Exception as e:
            logger.error(f"Failed to set LED {color} to {brightness}: {str(e)}")
    
    async def commit_led_async(self) -> None:
        """Commit LED changes asynchronously."""
        try:
            await self._write_to_file_async(KBBL_PATHS['apply'], "1")
        except Exception as e:
            logger.error(f"Failed to commit LED changes: {str(e)}")
    
    async def update_leds(self, gpu_utilization: int, is_dimmed: bool = False) -> None:
        """Update LED colors based on CPU and GPU utilization."""
        try:
            cpu_utilization = self._calculate_cpu_utilization()
            brightness_coef = LED_BRIGHTNESS_DIM if is_dimmed else LED_BRIGHTNESS_NORMAL
            
            await asyncio.gather(
                self.set_led_async("red", int(brightness_coef * cpu_utilization)),
                self.set_led_async("green", int(brightness_coef * gpu_utilization)),
                self.set_led_async("blue", int(brightness_coef * (LED_MAX_VALUE - max(cpu_utilization, gpu_utilization))))
            )
            await self.commit_led_async()
            
        except Exception as e:
            logger.error(f"Error updating LEDs: {str(e)}")
            raise
