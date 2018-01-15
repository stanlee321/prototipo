#!/bin/sh
#!/usr/bin/python3
#!/usr/bin/env/python3
#!/home/myuser/bin/python3
#!/home/alvarohurtado/.local/lib/python3.5/site-packages/numpy
#!/usr/local/lib/python3.5/dist-packages

# @reboot sleep 60 && sh /home/alvarohurtado/trafficFlow/prototipo/launcher.sh > /home/alvarohurtado/trafficFlow/prototipo/logs/cronlog 2>&1
# @reboot sleep 60 && sh /home/pi/trafficFlow/prototipo/launcher.sh > /home/pi/trafficFlow/prototipo/logs/cronlog 2>&1

cd /
cd /home/alvarohurtado/trafficFlow/prototipo
sudo python3 crontab.py
#cd /home/pi/trafficFlow/prototipo
#python3 prototipo25.py
cd /
