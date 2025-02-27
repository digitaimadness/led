"""
Asus TUF laptop utilities for controlling keyboard backlight and thermal throttling.
This module provides functionality to:
1. Control keyboard backlight based on CPU/GPU utilization
2. Manage thermal throttling based on power source and gamemode status
"""

import cython
from time import sleep
from os import system, path, chmod
from ProcessMappingScanner import scanAllProcessesForMapping
from multiprocessing import Process
import logging
from typing import Optional, List, Dict
import signal
from functools import wraps
from time import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('TUFUtils')

def retry_with_backoff(max_retries: int = 3, initial_delay: float = 1.0):
    """Decorator for retrying operations with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for retry in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if retry == max_retries - 1:
                        raise
                    logger.warning(f"Retrying {func.__name__} after error: {str(e)}")
                    sleep(delay)
                    delay *= 2
        return wrapper
    return decorator

@cython.cclass
class utils:
    """Main utility class for Asus TUF laptop controls."""
    
    # Process tracking
    _processes: Dict[str, Process]
    _shutting_down: cython.bint
    
    def __init__(self) -> cython.int:
        """Initialize the utilities and set up initial states.
        
        Returns:
            int: 0 on success, -1 on failure
        """
        try:
            # Initialize process tracking
            self._processes = {}
            self._shutting_down = False
            
            # Set up signal handlers
            signal.signal(signal.SIGTERM, self._handle_shutdown)
            signal.signal(signal.SIGINT, self._handle_shutdown)
            
            # Initialize keyboard backlight
            self._write_to_file('/sys/devices/platform/faustus/kbbl/kbbl_mode', "0")
            self._write_to_file('/sys/devices/platform/faustus/kbbl/kbbl_speed', "0")
            self._write_to_file('/sys/devices/platform/faustus/kbbl/kbbl_flags', "ff")
            
            # Initialize state files
            self._write_to_file('/run/nvidiautilization', "")
            self._write_to_file('/run/gamemode', '0')
            chmod('/run/gamemode', 0o0777)
            
            logger.info("TUF Utils initialized successfully")
            self.main()
            return 0
        except Exception as e:
            logger.error(f"Failed to initialize TUF Utils: {str(e)}")
            return -1
    
    @cython.cfunc
    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def _write_to_file(self, filepath: str, content: str) -> None:
        """Write content to a file with error handling and retry.
        
        Args:
            filepath: Path to the file
            content: Content to write
        """
        try:
            with open(filepath, "w") as f:
                f.write(content)
        except IOError as e:
            logger.error(f"Failed to write to {filepath}: {str(e)}")
            raise
    
    @cython.cfunc
    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def _read_from_file(self, filepath: str) -> str:
        """Read content from a file with error handling and retry.
        
        Args:
            filepath: Path to the file
            
        Returns:
            str: File content
        """
        try:
            with open(filepath, "r") as f:
                return f.read()
        except IOError as e:
            logger.error(f"Failed to read from {filepath}: {str(e)}")
            raise
    
    @cython.cfunc
    def isonbattery(self) -> cython.bint:
        """Check if the laptop is running on battery.
        
        Returns:
            bool: True if on battery, False if on AC power
        """
        try:
            status = self._read_from_file('/sys/class/power_supply/BAT1/status')
            return 'Discharging' in status
        except Exception as e:
            logger.error(f"Failed to check battery status: {str(e)}")
            return False
    
    @cython.cfunc
    def readbrightness(self, brightnessdev: str) -> cython.int:
        """Read brightness value from a device.
        
        Args:
            brightnessdev: Path to brightness device file
            
        Returns:
            int: Brightness value
        """
        try:
            return int(self._read_from_file(brightnessdev))
        except Exception as e:
            logger.error(f"Failed to read brightness: {str(e)}")
            return 0
    
    @cython.cfunc
    def readgpuutilization(self) -> cython.int:
        """Read NVIDIA GPU utilization.
        
        Returns:
            int: GPU utilization percentage
        """
        try:
            system('/usr/bin/nvidia-smi -f=/run/nvidiautilization -q -d UTILIZATION,TEMPERATURE,MEMORY')
            content = self._read_from_file('/run/nvidiautilization')
            return int(content.split('\\n')[19].strip(' Gpu:%'))
        except Exception as e:
            logger.error(f"Failed to read GPU utilization: {str(e)}")
            return 0
    
    @cython.cfunc
    def readgamemode(self) -> cython.int:
        """Read gamemode status.
        
        Returns:
            int: 1 if gamemode is active, 0 otherwise
        """
        try:
            return int(self._read_from_file('/run/gamemode'))
        except Exception as e:
            logger.error(f"Failed to read gamemode status: {str(e)}")
            return 0
    
    @cython.cfunc
    def readthermalthrottlepolicy(self) -> cython.int:
        """Read current thermal throttle policy.
        
        Returns:
            int: Current policy value
        """
        try:
            return int(self._read_from_file('/sys/devices/platform/faustus/throttle_thermal_policy'))
        except Exception as e:
            logger.error(f"Failed to read thermal throttle policy: {str(e)}")
            return 0
    
    @cython.cfunc
    def setthermalthrottlepolicy(self, policy: cython.int) -> None:
        """Set thermal throttle policy.
        
        Args:
            policy: Policy value to set
        """
        try:
            self._write_to_file('/sys/devices/platform/faustus/throttle_thermal_policy', str(policy))
            logger.info(f"Thermal throttle policy set to: {policy}")
        except Exception as e:
            logger.error(f"Failed to set thermal throttle policy: {str(e)}")
    
    @cython.cfunc
    def setled(self, color: str, brightness: cython.int) -> None:
        """Set LED color and brightness.
        
        Args:
            color: Color name ('red', 'green', or 'blue')
            brightness: Brightness value (0-255)
        """
        try:
            self._write_to_file(f'/sys/devices/platform/faustus/kbbl/{color}', str(brightness))
        except Exception as e:
            logger.error(f"Failed to set LED {color} to {brightness}: {str(e)}")
    
    @cython.cfunc
    def commitled(self) -> None:
        """Commit LED changes."""
        try:
            self._write_to_file('/sys/devices/platform/faustus/kbbl/apply', "1")
        except Exception as e:
            logger.error(f"Failed to commit LED changes: {str(e)}")
    
    @cython.ccall
    def controlkeyboardled(self) -> None:
        """Control keyboard LED based on CPU and GPU utilization."""
        is2tick = False
        while True:
            try:
                # Get CPU utilization
                with open('/proc/stat', 'r') as f:
                    fields = [float(column) for column in f.readline().strip().split()[1:]]
                idle, total = fields[3], sum(fields)
                cpu_total = total
                cpu_idle = idle

                sleep(0.5)

                with open('/proc/stat', 'r') as f:
                    fields = [float(column) for column in f.readline().strip().split()[1:]]
                idle, total = fields[3], sum(fields)
                
                cpu_total_delta = total - cpu_total
                cpu_idle_delta = idle - cpu_idle
                cpu_utilization = int((1.0 - cpu_idle_delta/cpu_total_delta) * 100.0)
                
                # Get GPU utilization
                gpuutilization = self.readgpuutilization()
                
                # Calculate brightness coefficient
                brightnesscoef = 1
                if is2tick:
                    brightnesscoef = 0.8
                
                # Set LED colors based on utilization
                self.setled("red", brightnesscoef * cpu_utilization)
                self.setled("green", brightnesscoef * gpuutilization)
                self.setled("blue", brightnesscoef * (255 - max(cpu_utilization, gpuutilization)))
                self.commitled()
                
                is2tick = not is2tick
                sleep(1 if self.isonbattery() else 0.1)
                
            except Exception as e:
                logger.error(f"Error in keyboard LED control: {str(e)}")
                sleep(5)  # Wait before retrying
    
    @cython.ccall
    def controlthermalthrottle(self) -> None:
        """Control thermal throttling based on power source and system state."""
        while True:
            try:
                onbattery: cython.bint = self.isonbattery()
                thermalthrottlepolicy: cython.int = self.readthermalthrottlepolicy()
                
                if onbattery:
                    if thermalthrottlepolicy != 2:
                        self.setthermalthrottlepolicy(2)
                        system("sysctl kernel.sched_tt_balancer_opt=3")
                else:
                    gamemode: cython.int = self.readgamemode()
                    if gamemode == 1:
                        if thermalthrottlepolicy != 1:
                            self.setthermalthrottlepolicy(1)
                            system("sysctl kernel.sched_tt_balancer_opt=1")
                    elif scanAllProcessesForMapping("clang") != {}:
                        self.setthermalthrottlepolicy(1)
                    elif thermalthrottlepolicy != 0:
                        self.setthermalthrottlepolicy(0)
                        system("sysctl kernel.sched_tt_balancer_opt=1")
                
                sleep(5 if self.isonbattery() else 2.5)
                
            except Exception as e:
                logger.error(f"Error in thermal throttle control: {str(e)}")
                sleep(5)  # Wait before retrying
    
    def _handle_shutdown(self, signum: int, frame) -> None:
        """Handle shutdown signals gracefully.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        logger.info(f"Received shutdown signal {signum}, stopping processes...")
        self._shutting_down = True
        for name, process in self._processes.items():
            logger.info(f"Terminating {name} process...")
            process.terminate()
            process.join(timeout=5)
            if process.is_alive():
                logger.warning(f"{name} process did not terminate gracefully, killing...")
                process.kill()
        logger.info("All processes stopped")
        exit(0)
    
    def _monitor_processes(self) -> None:
        """Monitor and restart processes if they die unexpectedly."""
        while not self._shutting_down:
            for name, process in self._processes.items():
                if not process.is_alive() and not self._shutting_down:
                    logger.warning(f"{name} process died, restarting...")
                    new_process = Process(
                        target=getattr(self, name.lower()),
                        name=name
                    )
                    new_process.start()
                    self._processes[name] = new_process
            sleep(5)
    
    @cython.ccall
    def main(self) -> None:
        """Start the main control processes."""
        if cython.compiled:
            logger.info("Running in compiled mode for optimal performance")
        else:
            logger.warning("Running in interpreted mode - performance may be reduced")
        
        try:
            # Start control processes
            self._processes["ThermalThrottle"] = Process(
                target=self.controlthermalthrottle,
                name="ThermalThrottle"
            )
            self._processes["KeyboardLED"] = Process(
                target=self.controlkeyboardled,
                name="KeyboardLED"
            )
            
            # Start process monitor
            monitor_process = Process(
                target=self._monitor_processes,
                name="ProcessMonitor"
            )
            
            # Start all processes
            for name, process in self._processes.items():
                process.start()
                logger.info(f"{name} process started")
            
            monitor_process.start()
            logger.info("Process monitor started")
            
            # Wait for processes
            monitor_process.join()
            
        except Exception as e:
            logger.error(f"Failed to start control processes: {str(e)}")