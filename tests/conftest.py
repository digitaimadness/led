"""Test configuration and fixtures for Asus TUF utilities."""

import os
import pytest
import tempfile
from typing import Dict, Generator, Any

@pytest.fixture
def mock_sys_files() -> Generator[Dict[str, str], None, None]:
    """Create temporary files to mock system files."""
    temp_files = {}
    try:
        # Create temp directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create faustus base directory
            faustus_dir = os.path.join(temp_dir, 'sys/devices/platform/faustus')
            os.makedirs(faustus_dir)
            
            # Create keyboard LED files
            kbbl_dir = os.path.join(faustus_dir, 'kbbl')
            os.makedirs(kbbl_dir)
            for file in ['kbbl_mode', 'kbbl_speed', 'kbbl_flags', 'red', 'green', 'blue', 'apply']:
                path = os.path.join(kbbl_dir, file)
                with open(path, 'w') as f:
                    f.write('0')
                temp_files[file] = path
            
            # Create thermal files
            thermal_file = os.path.join(faustus_dir, 'throttle_thermal_policy')
            with open(thermal_file, 'w') as f:
                f.write('0')
            temp_files['throttle_thermal_policy'] = thermal_file
            
            # Create power management files
            for file in ['fan_boost_mode', 'power_profile', 'gpu_power']:
                path = os.path.join(faustus_dir, file)
                with open(path, 'w') as f:
                    f.write('0')
                temp_files[file] = path
            
            # Create temperature files
            thermal_dir = os.path.join(temp_dir, 'sys/class/thermal')
            os.makedirs(thermal_dir)
            for i in range(2):
                zone_dir = os.path.join(thermal_dir, f'thermal_zone{i}')
                os.makedirs(zone_dir)
                temp_file = os.path.join(zone_dir, 'temp')
                with open(temp_file, 'w') as f:
                    f.write('45000')
                temp_files[f'thermal_zone{i}'] = temp_file
            
            # Create battery status file
            power_dir = os.path.join(temp_dir, 'sys/class/power_supply/BAT1')
            os.makedirs(power_dir)
            status_file = os.path.join(power_dir, 'status')
            with open(status_file, 'w') as f:
                f.write('Charging')
            temp_files['battery_status'] = status_file
            
            # Create GPU utilization file
            run_dir = os.path.join(temp_dir, 'run')
            os.makedirs(run_dir)
            gpu_file = os.path.join(run_dir, 'nvidiautilization')
            with open(gpu_file, 'w') as f:
                f.write('0')
            temp_files['gpu_utilization'] = gpu_file
            
            yield temp_files
    finally:
        # Cleanup is handled by TemporaryDirectory context manager
        pass

@pytest.fixture
def mock_config(mock_sys_files: Dict[str, str], monkeypatch: Any) -> None:
    """Mock configuration constants."""
    from config import (
        FAUSTUS_BASE_PATH,
        KBBL_BASE_PATH,
        BATTERY_STATUS_PATH,
        NVIDIA_UTILIZATION_PATH,
        THROTTLE_POLICY_PATH,
        FAN_CONTROL_PATH,
        POWER_PROFILE_PATH,
        GPU_POWER_PATH,
        TEMP_PATHS,
        KBBL_PATHS
    )
    
    # Update paths to use temp files
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(mock_sys_files['kbbl_mode'])))
    monkeypatch.setattr('config.FAUSTUS_BASE_PATH', os.path.join(base_dir, 'sys/devices/platform/faustus'))
    monkeypatch.setattr('config.KBBL_BASE_PATH', os.path.join(base_dir, 'sys/devices/platform/faustus/kbbl'))
    monkeypatch.setattr('config.BATTERY_STATUS_PATH', mock_sys_files['battery_status'])
    monkeypatch.setattr('config.NVIDIA_UTILIZATION_PATH', mock_sys_files['gpu_utilization'])
    monkeypatch.setattr('config.THROTTLE_POLICY_PATH', mock_sys_files['throttle_thermal_policy'])
    monkeypatch.setattr('config.FAN_CONTROL_PATH', mock_sys_files['fan_boost_mode'])
    monkeypatch.setattr('config.POWER_PROFILE_PATH', mock_sys_files['power_profile'])
    monkeypatch.setattr('config.GPU_POWER_PATH', mock_sys_files['gpu_power'])
    monkeypatch.setattr('config.TEMP_PATHS', {
        'cpu': mock_sys_files['thermal_zone0'],
        'gpu': mock_sys_files['thermal_zone1']
    })
    
    # Update keyboard LED paths
    new_kbbl_paths = {}
    for key in KBBL_PATHS:
        new_kbbl_paths[key] = mock_sys_files[key]
    monkeypatch.setattr('config.KBBL_PATHS', new_kbbl_paths)
