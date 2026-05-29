#!/usr/bin/env python3
from gpiozero import MotionSensor
import requests
import time

PIR_PIN = 17
HA_URL = "http://homeassistant.local:8123"
TOKEN = "YOUR_TOKEN_HERE"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def screensaver_on():
    requests.post(f"{HA_URL}/api/services/input_boolean/turn_on",
                  headers=HEADERS,
                  json={"entity_id": "input_boolean.wallpanel_screensaver"})
    print("Screensaver on")

def screensaver_off():
    requests.post(f"{HA_URL}/api/services/input_boolean/turn_off",
                  headers=HEADERS,
                  json={"entity_id": "input_boolean.wallpanel_screensaver"})
    print("Screensaver off")

pir = MotionSensor(PIR_PIN)
print("PIR started, waiting for motion...")

while True:
    if not pir.motion_detected:
        screensaver_off()
        pir.wait_for_motion()
    else:
        pir.wait_for_no_motion()
