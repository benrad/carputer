#!/bin/bash

# startup info found in /etc/rc.local
# GPIO pin 4 to pin closest to usb ports on car switch. GPIO pin 18 to other
#

sudo -v

#add kill script to init.d, symlink to rc0.d
mv ./K01aaKillCarputer /etc/init.d/killcarputer
chmod -x /etc/init.d/killcarputer
cd /etc/rc0.d/
ln -s ../init.d/killcarputer ./K01aaKillCarputer
cd /etc/rc0.d/
ln -s ../init.d/killcarputer ./K01aaKillCarputer

sed /etc/rc.local # add py script, & so it runs in background

#make kill script executable
#update-rc.d K01aaKillCarputer defaults
#####gps isn't getting next, should find way to bypass when not
#TODO: to run, need to change notswitch -> switch.sh and uncomment carputer.sh in rc.local
#cat /sys/class/gpio/gpio4/value

#hcitool scan | grep -v Scanning # will scan and select lines once found
#sudo bluez-simple-agent hci0 result from ^ might work?
#http://unix.stackexchange.com/questions/42526/how-to-get-my-bluetooth-keyboard-to-be-recognized-before-log-in
