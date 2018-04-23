#!/bin/sh
cd /home/pi/
mkdir .config/autostart
mv ./TouchRTKStation/install/TouchRTKStationpy.desktop ./.config/autostart/
chmod +x ./.config/autostart/TouchRTKStationpy.desktop

reboot
