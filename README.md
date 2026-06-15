# MiniDash-Wallpanel-PIR

A Raspberry Pi GPIO PIR motion sensor that wakes a WallPanel screensaver via the Home Assistant REST API. When motion is detected at a wall-mounted dashboard, the screensaver stops and the dashboard is shown. WallPanel's own `idle_time` handles returning to the screensaver after inactivity.

---

## How it works

```
PIR sensor (GPIO17)
       ↓
Python script on Pi
       ↓
HA REST API call
       ↓
input_boolean.wallpanel_screensaver set to OFF
       ↓
WallPanel stops screensaver, shows dashboard
```

WallPanel's `idle_time` setting controls how long before the screensaver returns after inactivity.

---

## Hardware

- Raspberry Pi (tested on Pi 5) running Raspberry Pi OS
- Any standard 3-pin PIR motion sensor (tested with HC-SR501)
- Wall-mounted display

### PIR wiring

| PIR pin | Pi physical pin | Label  |
|---------|----------------|--------|
| VCC     | Pin 2          | 5V     |
| GND     | Pin 6          | GND    |
| OUT     | Pin 11         | GPIO17 |

### HC-SR501 recommended settings

- **Jumper**: set to **H** (repeatable trigger mode) — keeps retriggering while motion is present
- **Time delay pot**: set to minimum (~3s) — let WallPanel `idle_time` handle the return to screensaver
- **Sensitivity pot**: adjust to taste for your room size and placement

---

## Software dependencies

### On the Pi

```bash
sudo apt install python3-lgpio -y
```

The following are pre-installed on Raspberry Pi OS:

- `gpiozero`
- `requests`

### In Home Assistant

- [WallPanel](https://github.com/j-a-n/lovelace-wallpanel) — installed via HACS
- An `input_boolean` helper named `wallpanel_screensaver`

---

## Home Assistant setup

### 1. Create the helper

Settings → Devices & Services → Helpers → Create Helper → Toggle

Name it `wallpanel_screensaver`. The entity ID will be `input_boolean.wallpanel_screensaver`.

### 2. WallPanel dashboard config

Add to your dashboard raw config (Overview → Edit Dashboard → three dots → Raw configuration editor):

```yaml
wallpanel:
  enabled: true
  idle_time: 30
  display_time: 30
  screensaver_entity: input_boolean.wallpanel_screensaver
```

Adjust `idle_time` and `display_time` to taste.

### 3. Long-lived access token

In HA, click your profile (bottom left) → scroll to Long-Lived Access Tokens → Create Token. Copy it — you only see it once.

---

## Pi setup

### 1. The script

Copy `pir_screen.py` to your Pi and edit the top section:

```python
PIR_PIN = 17          # GPIO pin number (BCM)
HA_URL = "http://homeassistant.local:8123"
TOKEN = "YOUR_TOKEN_HERE"
```

> **Note on PIR logic:** Some PIR sensors have inverted output — `motion_detected` returns `True` at rest and `False` when motion occurs. The script uses `if not pir.motion_detected` to account for this. Test your sensor first (see Testing below) and adjust the logic if needed.

### 2. Systemd service

Save as `/etc/systemd/system/pir_screen.service`:

```ini
[Unit]
Description=PIR Screen Controller
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/YOUR_USER/pir_screen.py
Restart=always
User=YOUR_USER
WorkingDirectory=/home/YOUR_USER
Environment=PYTHONUNBUFFERED=1
Environment=GPIOZERO_PIN_FACTORY=lgpio

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable pir_screen.service
sudo systemctl start pir_screen.service
sudo systemctl status pir_screen.service
```

---

## Testing

Test the HA REST API from the Pi:

```bash
curl -X POST http://homeassistant.local:8123/api/services/input_boolean/turn_off \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "input_boolean.wallpanel_screensaver"}'
```

Test the PIR sensor to check which way its logic is oriented:

```bash
python3 -c "
from gpiozero import MotionSensor
import time
pir = MotionSensor(17)
while True:
    print(f'motion_detected: {pir.motion_detected}')
    time.sleep(1)
"
```

Watch the output while moving and staying still — if `True` means no motion, your sensor has inverted logic and the `not` in the script is correct. If `True` means motion, remove the `not`.

Check service logs:

```bash
sudo journalctl -u pir_screen.service -n 30 --no-pager
```

---

## Notes

- `GPIOZERO_PIN_FACTORY=lgpio` is required in the systemd service environment — without it gpiozero fails to initialise outside of a desktop session
- If your Pi is running Wayland and you want direct display control instead of (or in addition to) WallPanel, `wlopm` can turn the display on/off: `WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 wlopm --off HDMI-A-1`
