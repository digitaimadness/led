#### [Linux only]
## some useful tools for your Asus Tuf laptop

### use keyboard⌨ backlight as an CPU/GPU load indicator with gradients from 🟦 (indicating both idle) to 🟥 (CPU 100% load) and 🟩 (GPU 100% load)

### activate powersave thermal throttle mode based on if running on battery🔋 or boost mode if 🎮 [FeralInteractive/gamemode](https://github.com/FeralInteractive/gamemode) is activated and running on charger🔌

#### Requirements

1. [hackbnw/faustus](https://github.com/hackbnw/faustus) driver must be installed and functioning! If your Asus TUF laptop is unsupported by the driver try building dkms module anyway and put following to your kernel parameters🫠, worked for me!
```
faustus.let_it_burn=1
```

2. Python dependencies:
```bash
pip install -r requirements.txt
```

### 🔨installation🔧
```bash
# Clone the repository
git clone https://github.com/digitaimadness/tuf-utils /tmp/tuf-utils
cd /tmp/tuf-utils

# Install dependencies
pip install -r requirements.txt

# Build and install
python setup.py build_ext --inplace
sudo mkdir /opt/tuf-utils
sudo mv tufutils.pyx tufutilsstarter.py tufutils.cpython-*-linux-gnu.so /opt/tuf-utils
sudo mv tuf-utils.service /etc/systemd/system
```

### ✨usage✨
```bash
sudo systemctl start tuf-utils.service
sudo systemctl stop tuf-utils.service
```

### 🌄autostart🌄
```bash
sudo systemctl enable tuf-utils.service
```