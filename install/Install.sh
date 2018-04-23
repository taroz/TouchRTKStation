#!/bin/sh

cd /home/pi/

apt-get update -y

# Install pyqt5
apt-get install -y qt5-default pyqt5-dev pyqt5-dev-tools

# Install RTKLIB
git clone -b rtklib_2.4.3 https://github.com/tomojitakasu/RTKLIB.git
cd ./RTKLIB/app/str2str/gcc/
make
cd ../../rtkrcv/gcc/
make

# Install LCD Driver
cd /home/pi/
wget http://www.waveshare.com/w/upload/0/00/LCD-show-170703.tar.gz
tar xzvf LCD*.tar.gz
cd ./LCD-show/
chmod +x LCD4-show
./LCD4-show
