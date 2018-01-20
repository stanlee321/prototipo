#!/bin/sh
# launcher.sh
# nav to home dir, then to this dir, then exec python script, then back to home

# @reboot sleep 60 && sh /home/alvarohurtado/trafficFlow/prototipo/launcher.sh > /home/alvarohurtado/trafficFlow/prototipo/logs/cronlog 2>&1
# @reboot sleep 60 && sh /home/pi/trafficFlow/prototipo/launcher.sh > /home/pi/trafficFlow/prototipo/logs/cronlog 2>&1

cd /
cd /home/pi/trafficFlow/prototipo
python3 prototipo25.py Show
cd /
