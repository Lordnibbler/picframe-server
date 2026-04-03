# picframe-server
web frontend and python backend for picframe digital picture frame on raspberry pi

## start it

```shell
source /home/pi/venv_picframe/bin/activate
pip install flask pyyaml ruamel.yaml  # only needed first time
python config.py
```

open your browser <http://192.168.50.117:5000> (replace the IP obviously)

## automatically start the web service on raspberry pi boot

make a new service:

```shell
mkdir -p /home/pi/.config/systemd/user
nano /home/pi/.config/systemd/user/picframe-web.service
```

paste this in the service file:

```ini
[Unit]
Description=PicFrame Web UI
After=network.target

[Service]
WorkingDirectory=/home/pi
ExecStart=/home/pi/venv_picframe/bin/python /home/pi/config.py
Restart=always
RestartSec=5

# optional but recommended
Environment=PICFRAME_WEB_SECRET=change-this

[Install]
WantedBy=default.target
```

enable the service:

```shell
systemctl --user daemon-reload
systemctl --user enable picframe-web.service
systemctl --user start picframe-web.service
```

automatically start the service on boot:

```shell
sudo loginctl enable-linger pi
```

check the service status:

```shell
systemctl status picframe-web.service
```

read logs if there are problems:

```shell
journalctl --user -u picframe-web.service -f
```

## use hdmi cec from the rpi to turn on the tv on boot

create systemd service file

```shell
sudo nano /etc/systemd/system/tv-on.service
```

paste this in


```ini
[Unit]
Description=Turn on TV via HDMI-CEC
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'sleep 5 && echo "on 0" | cec-client -s -d 1'

[Install]
WantedBy=multi-user.target
```

tell systemd about the service

```shell
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
```

enable it at boot

```shell
sudo systemctl enable tv-on.service
```

test it once

```shell
sudo systemctl start tv-on.service
```

## enable VNC

```shell
ssh pi@192.168.50.117

# Then run:
sudo raspi-config
```

Go to:
Interface Options → VNC → Enable

Exit and reboot (optional but safe):

```shell
sudo reboot
```

Most Raspberry Pi OS installs already include it, but just in case:

```shell
sudo apt update
sudo apt install realvnc-vnc-server realvnc-vnc-viewer

# Enable it:
sudo systemctl enable vncserver-x11-serviced
sudo systemctl start vncserver-x11-serviced
```

## copy my config and start script to the rpi

```shell
scp "./configuration.yaml" pi@192.168.50.117:~/picframe_data/config/configuration.yaml
scp "./start_picframe.sh" pi@192.168.50.117:~/
```
