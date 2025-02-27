"""Main TUF utilities class for Asus TUF laptops."""

import cython
import logging
import asyncio
import signal
from os import chmod
from typing import Dict, Optional
from multiprocessing import Process

from config import (
    NVIDIA_UTILIZATION_PATH,
    GAMEMODE_PATH,
    GAMEMODE_PERMISSIONS,
    BATTERY_POLL_INTERVAL,
    CHARGER_POLL_INTERVAL,
    PROCESS_MONITOR_INTERVAL,
    FAN_UPDATE_INTERVAL
)
from services.keyboard import KeyboardService
from services.thermal import ThermalService
from services.power import PowerService

logger = logging.getLogger('TUFUtils')

@cython.cclass
class TUFUtils:
    """Main class for controlling Asus TUF laptop features."""
    
    _keyboard_service: KeyboardService
    _thermal_service: ThermalService
    _power_service: PowerService
    _processes: Dict[str, Process]
    _running: cython.bint
    _performance_mode: cython.bint
    
    def __init__(self):
        """Initialize TUF utilities."""
        self._keyboard_service = KeyboardService()
        self._thermal_service = ThermalService()
        self._power_service = PowerService()
        self._processes = {}
        self._running = True
        self._performance_mode = False
        self._setup_signal_handlers()
        self._initialize_gamemode()
    
    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._handle_shutdown)
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self._running = False
        self.cleanup()
    
    def _initialize_gamemode(self):
        """Initialize gamemode file."""
        try:
            with open(GAMEMODE_PATH, 'w') as f:
                f.write('0')
            chmod(GAMEMODE_PATH, GAMEMODE_PERMISSIONS)
            logger.info("Gamemode initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize gamemode: {str(e)}")
    
    def _monitor_process(self, process_name: str, target_func, *args, **kwargs):
        """Monitor and restart a process if it dies."""
        while self._running:
            if process_name not in self._processes or not self._processes[process_name].is_alive():
                logger.info(f"Starting {process_name} process...")
                process = Process(target=target_func, args=args, kwargs=kwargs)
                process.start()
                self._processes[process_name] = process
            asyncio.sleep(PROCESS_MONITOR_INTERVAL)
    
    async def _read_gpu_utilization(self) -> cython.int:
        """Read GPU utilization asynchronously."""
        try:
            async with aiofiles.open(NVIDIA_UTILIZATION_PATH, 'r') as f:
                content = await f.read()
                return int(content)
        except Exception as e:
            logger.error(f"Failed to read GPU utilization: {str(e)}")
            return 0
    
    async def _control_keyboard_led(self):
        """Control keyboard LED based on system utilization."""
        while self._running:
            try:
                gpu_utilization = await self._read_gpu_utilization()
                is_dimmed = self._thermal_service.is_on_battery()
                await self._keyboard_service.update_leds(gpu_utilization, is_dimmed)
            except Exception as e:
                logger.error(f"Error in keyboard LED control: {str(e)}")
            finally:
                await asyncio.sleep(CHARGER_POLL_INTERVAL if is_dimmed else BATTERY_POLL_INTERVAL)
    
    def _control_thermal(self):
        """Control thermal throttling."""
        while self._running:
            try:
                self._thermal_service.update_thermal_policy()
            except Exception as e:
                logger.error(f"Error in thermal control: {str(e)}")
            finally:
                asyncio.sleep(BATTERY_POLL_INTERVAL)
    
    def _control_power(self):
        """Control power and fan settings."""
        while self._running:
            try:
                on_battery = self._thermal_service.is_on_battery()
                self._power_service.optimize_power_settings(on_battery, self._performance_mode)
            except Exception as e:
                logger.error(f"Error in power control: {str(e)}")
            finally:
                asyncio.sleep(FAN_UPDATE_INTERVAL)
    
    def set_performance_mode(self, enabled: bool):
        """Enable or disable performance mode."""
        try:
            self._performance_mode = enabled
            on_battery = self._thermal_service.is_on_battery()
            self._power_service.optimize_power_settings(on_battery, enabled)
            logger.info(f"Performance mode {'enabled' if enabled else 'disabled'}")
        except Exception as e:
            logger.error(f"Failed to set performance mode: {str(e)}")
    
    def start(self):
        """Start all control processes."""
        try:
            # Start process monitoring
            Process(target=self._monitor_process, args=("keyboard", self._control_keyboard_led)).start()
            Process(target=self._monitor_process, args=("thermal", self._control_thermal)).start()
            Process(target=self._monitor_process, args=("power", self._control_power)).start()
            Process(target=self._monitor_process, args=("fan", self._power_service.auto_fan_control)).start()
            logger.info("TUF utilities started successfully")
        except Exception as e:
            logger.error(f"Failed to start TUF utilities: {str(e)}")
            self.cleanup()
            raise
    
    def cleanup(self):
        """Clean up resources."""
        self._running = False
        for process in self._processes.values():
            process.terminate()
            process.join()
        self._keyboard_service.cleanup()
        self._thermal_service.cleanup()
        self._power_service.cleanup()
        logger.info("TUF utilities cleaned up successfully")
