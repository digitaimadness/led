"""Tests for the main TUF utilities class."""

import os
import pytest
import asyncio
import signal
from multiprocessing import Process
from tuf_utils import TUFUtils

def test_tuf_utils_initialization(mock_config):
    """Test TUFUtils initialization."""
    utils = TUFUtils()
    assert utils is not None
    assert utils._running
    assert not utils._performance_mode
    assert isinstance(utils._processes, dict)

def test_gamemode_initialization(mock_config, tmp_path):
    """Test gamemode file initialization."""
    # Mock gamemode path
    gamemode_path = tmp_path / 'gamemode'
    from config import GAMEMODE_PATH, GAMEMODE_PERMISSIONS
    import sys
    sys.modules['config'].GAMEMODE_PATH = str(gamemode_path)
    
    utils = TUFUtils()
    assert os.path.exists(gamemode_path)
    with open(gamemode_path, 'r') as f:
        assert f.read().strip() == '0'
    assert oct(os.stat(gamemode_path).st_mode)[-3:] == str(GAMEMODE_PERMISSIONS)

def test_signal_handling(mock_config):
    """Test signal handling."""
    utils = TUFUtils()
    assert utils._running
    
    # Simulate SIGTERM
    utils._handle_shutdown(signal.SIGTERM, None)
    assert not utils._running

def test_performance_mode(mock_config):
    """Test performance mode toggle."""
    utils = TUFUtils()
    assert not utils._performance_mode
    
    # Enable performance mode
    utils.set_performance_mode(True)
    assert utils._performance_mode
    with open(utils._power_service._power_profile_path, 'r') as f:
        assert f.read().strip() == '2'  # Should be performance
    with open(utils._power_service._gpu_power_path, 'r') as f:
        assert f.read().strip() == '2'  # Should be boost
    
    # Disable performance mode
    utils.set_performance_mode(False)
    assert not utils._performance_mode
    with open(utils._power_service._power_profile_path, 'r') as f:
        assert f.read().strip() == '1'  # Should be balanced
    with open(utils._power_service._gpu_power_path, 'r') as f:
        assert f.read().strip() == '1'  # Should be standard

@pytest.mark.asyncio
async def test_gpu_utilization_reading(mock_config):
    """Test GPU utilization reading."""
    utils = TUFUtils()
    
    # Test normal reading
    with open(utils._power_service._gpu_utilization_path, 'w') as f:
        f.write('75')
    util = await utils._read_gpu_utilization()
    assert util == 75
    
    # Test error handling
    with open(utils._power_service._gpu_utilization_path, 'w') as f:
        f.write('invalid')
    util = await utils._read_gpu_utilization()
    assert util == 0

def test_process_monitoring(mock_config):
    """Test process monitoring."""
    utils = TUFUtils()
    
    # Mock process that exits quickly
    def mock_process():
        pass
    
    # Start monitoring
    process = Process(target=utils._monitor_process, args=('test', mock_process))
    process.start()
    
    # Let the monitor run briefly
    asyncio.sleep(0.1)
    
    # Check that process was restarted
    assert 'test' in utils._processes
    assert utils._processes['test'].is_alive()
    
    # Cleanup
    utils._running = False
    process.terminate()
    process.join()

def test_cleanup(mock_config):
    """Test cleanup process."""
    utils = TUFUtils()
    
    # Add some test processes
    def mock_process():
        while True:
            asyncio.sleep(0.1)
    
    process1 = Process(target=mock_process)
    process2 = Process(target=mock_process)
    process1.start()
    process2.start()
    utils._processes = {'p1': process1, 'p2': process2}
    
    # Run cleanup
    utils.cleanup()
    
    # Verify cleanup
    assert not utils._running
    for process in utils._processes.values():
        assert not process.is_alive()
    
    # Verify services cleanup
    assert not utils._keyboard_service._running
    assert not utils._thermal_service._running
    assert not utils._power_service._running
