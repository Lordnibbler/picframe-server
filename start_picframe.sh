#!/bin/bash

# kill any previous instance
pkill -f "/home/pi/venv_picframe/bin/picframe" 2>/dev/null

# wait for display + HDMI + CEC to fully initialize
sleep 30

# activate env
source /home/pi/venv_picframe/bin/activate

# start picframe cleanly
exec picframe
