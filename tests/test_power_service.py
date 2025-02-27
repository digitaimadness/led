"""Tests for the power management service."""

import os
import pytest
from services.power import PowerService

def test_power_service_initialization(mock_config):
    """Test PowerService initialization."""
    service = PowerService()
    assert service is not None
    assert not service._performance_mode

def test_read_temperature(mock_config):
    """Test temperature reading."""
    service = PowerService()
    cpu_temp = service.read_cpu_temperature()
    gpu_temp = service.read_gpu_temperature()
    assert cpu_temp == 45.0  # From mock file
    assert gpu_temp == 45.0  # From mock file

def test_fan_boost_control(mock_config):
    """Test fan boost control."""
    service = PowerService()
    
    # Test enabling fan boost
    service.set_fan_boost(True)
    with open(service._fan_control_path, 'r') as f:
        assert f.read().strip() == '2'  # Maximum boost
    
    # Test disabling fan boost
    service.set_fan_boost(False)
    with open(service._fan_control_path, 'r') as f:
        assert f.read().strip() == '0'  # Normal mode

def test_power_profile_control(mock_config):
    """Test power profile control."""
    service = PowerService()
    
    # Test performance profile
    service.set_power_profile('performance')
    with open(service._power_profile_path, 'r') as f:
        assert f.read().strip() == '2'
    
    # Test balanced profile
    service.set_power_profile('balanced')
    with open(service._power_profile_path, 'r') as f:
        assert f.read().strip() == '1'
    
    # Test powersave profile
    service.set_power_profile('powersave')
    with open(service._power_profile_path, 'r') as f:
        assert f.read().strip() == '0'

def test_gpu_power_control(mock_config):
    """Test GPU power state control."""
    service = PowerService()
    
    # Test boost mode
    service.set_gpu_power_state('boost')
    with open(service._gpu_power_path, 'r') as f:
        assert f.read().strip() == '2'
    
    # Test standard mode
    service.set_gpu_power_state('standard')
    with open(service._gpu_power_path, 'r') as f:
        assert f.read().strip() == '1'
    
    # Test eco mode
    service.set_gpu_power_state('eco')
    with open(service._gpu_power_path, 'r') as f:
        assert f.read().strip() == '0'

def test_auto_fan_control(mock_config):
    """Test automatic fan control."""
    service = PowerService()
    
    # Test high temperature scenario
    with open(service._temp_paths['cpu'], 'w') as f:
        f.write('85000')  # 85°C
    with open(service._temp_paths['gpu'], 'w') as f:
        f.write('82000')  # 82°C
    
    service.auto_fan_control()
    with open(service._fan_control_path, 'r') as f:
        assert f.read().strip() == '2'  # Should be in boost mode
    
    # Test normal temperature scenario
    with open(service._temp_paths['cpu'], 'w') as f:
        f.write('65000')  # 65°C
    with open(service._temp_paths['gpu'], 'w') as f:
        f.write('62000')  # 62°C
    
    service.auto_fan_control()
    with open(service._fan_control_path, 'r') as f:
        assert f.read().strip() == '1'  # Should be in normal mode

def test_optimize_power_settings(mock_config):
    """Test power settings optimization."""
    service = PowerService()
    
    # Test on battery, no performance mode
    service.optimize_power_settings(on_battery=True, performance_mode=False)
    with open(service._power_profile_path, 'r') as f:
        assert f.read().strip() == '0'  # Should be powersave
    with open(service._gpu_power_path, 'r') as f:
        assert f.read().strip() == '0'  # Should be eco
    
    # Test on AC, performance mode
    service.optimize_power_settings(on_battery=False, performance_mode=True)
    with open(service._power_profile_path, 'r') as f:
        assert f.read().strip() == '2'  # Should be performance
    with open(service._gpu_power_path, 'r') as f:
        assert f.read().strip() == '2'  # Should be boost
    
    # Test on AC, no performance mode
    service.optimize_power_settings(on_battery=False, performance_mode=False)
    with open(service._power_profile_path, 'r') as f:
        assert f.read().strip() == '1'  # Should be balanced
    with open(service._gpu_power_path, 'r') as f:
        assert f.read().strip() == '1'  # Should be standard
