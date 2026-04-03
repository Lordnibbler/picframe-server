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
