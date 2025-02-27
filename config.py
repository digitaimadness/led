"""Configuration constants for Asus TUF utilities."""

# File paths
FAUSTUS_BASE_PATH = '/sys/devices/platform/faustus'
KBBL_BASE_PATH = f'{FAUSTUS_BASE_PATH}/kbbl'
BATTERY_STATUS_PATH = '/sys/class/power_supply/BAT1/status'
PROC_STAT_PATH = '/proc/stat'
NVIDIA_UTILIZATION_PATH = '/run/nvidiautilization'
GAMEMODE_PATH = '/run/gamemode'

# Keyboard backlight settings
KBBL_PATHS = {
    'mode': f'{KBBL_BASE_PATH}/kbbl_mode',
    'speed': f'{KBBL_BASE_PATH}/kbbl_speed',
    'flags': f'{KBBL_BASE_PATH}/kbbl_flags',
    'red': f'{KBBL_BASE_PATH}/red',
    'green': f'{KBBL_BASE_PATH}/green',
    'blue': f'{KBBL_BASE_PATH}/blue',
    'apply': f'{KBBL_BASE_PATH}/apply'
}

# Thermal throttle settings
THROTTLE_POLICY_PATH = f'{FAUSTUS_BASE_PATH}/throttle_thermal_policy'
THROTTLE_POLICIES = {
    'normal': 0,
    'boost': 1,
    'silent': 2
}

# File permissions
GAMEMODE_PERMISSIONS = 0o0777

# Timing settings
BATTERY_POLL_INTERVAL = 1.0
CHARGER_POLL_INTERVAL = 0.1
ERROR_RETRY_INTERVAL = 5.0
PROCESS_MONITOR_INTERVAL = 5.0
CPU_UPDATE_INTERVAL = 0.5

# LED settings
LED_BRIGHTNESS_NORMAL = 1.0
LED_BRIGHTNESS_DIM = 0.8
LED_MAX_VALUE = 255

# Error handling
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1.0
