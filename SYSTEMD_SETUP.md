# Tidbyt Systemd Service Setup

This directory contains example systemd service files and setup scripts for running Tidbyt as a background service on your Raspberry Pi.

## Installation

### 1. Copy Files to Appropriate Locations

```bash
# Copy the service file
sudo cp tidbyt.service /etc/systemd/system/tidbyt.service

# Copy the web service file (if using web dashboard)
sudo cp tidbyt-web.service /etc/systemd/system/tidbyt-web.service

# Set permissions
sudo chmod 644 /etc/systemd/system/tidbyt*.service
```

### 2. Edit Service File for Your Setup

```bash
sudo nano /etc/systemd/system/tidbyt.service
```

Make sure to adjust:
- `User=pi` - Change if your username is different
- `WorkingDirectory=/home/pi/tidbyt` - Adjust path if needed
- `ExecStart=/usr/bin/python3 /home/pi/tidbyt/tidbyt_web.py` - Point to correct script

### 3. Enable and Start Service

```bash
# Reload systemd daemon
sudo systemctl daemon-reload

# Enable service (auto-start on boot)
sudo systemctl enable tidbyt.service

# Start the service immediately
sudo systemctl start tidbyt.service

# Check status
sudo systemctl status tidbyt.service

# View logs
sudo journalctl -u tidbyt.service -f
```

## Service Files

### tidbyt.service
Runs the CLI version for direct control. Good if you want to SSH in and control it manually.

### tidbyt-web.service
Runs the web dashboard. Best for remote control via browser.

## Common Commands

```bash
# Start service
sudo systemctl start tidbyt

# Stop service
sudo systemctl stop tidbyt

# Restart service
sudo systemctl restart tidbyt

# Check if running
sudo systemctl status tidbyt

# View recent logs (last 50 lines)
sudo journalctl -u tidbyt.service -n 50

# Follow logs in real-time
sudo journalctl -u tidbyt.service -f

# Disable auto-start at boot
sudo systemctl disable tidbyt.service

# Enable auto-start at boot
sudo systemctl enable tidbyt.service
```

## Troubleshooting

### Service won't start
```bash
# Check logs
sudo journalctl -u tidbyt.service -n 100

# Check syntax
sudo systemd-analyze verify tidbyt.service
```

### Permission denied errors
Make sure the service file has the correct user. For GPIO access, you may need:
```bash
# Add pi user to gpio group (if using non-sudo method)
sudo usermod -a -G gpio pi
sudo usermod -a -G video pi
```

### Can't connect to web dashboard
- Check the service is running: `sudo systemctl status tidbyt.service`
- Check firewall: `sudo ufw allow 5000`
- Try accessing from Pi itself: `curl http://localhost:5000`

### Display shows nothing
- Check logs: `sudo journalctl -u tidbyt.service -f`
- Verify matrix power supply is connected
- Check GPIO pins are correct
- Test with: `sudo python3 /home/pi/tidbyt/tidbyt_matrix.py`

## Auto-Restart on Failure

The service file includes:
```ini
Restart=on-failure
RestartSec=10
```

This will automatically restart the service if it crashes, waiting 10 seconds between attempts.

## Running Multiple Instances

You can run multiple services with different configurations:

1. Copy tidbyt.service to tidbyt-app.service
2. Edit to use different settings
3. Give it a unique name in `[Unit]` section
4. Enable both services

Example for a second instance on different pins:
```bash
sudo cp tidbyt.service /etc/systemd/system/tidbyt-app2.service
sudo nano /etc/systemd/system/tidbyt-app2.service
# Edit ExecStart to use different script or config
sudo systemctl daemon-reload
sudo systemctl enable tidbyt-app2.service
sudo systemctl start tidbyt-app2.service
```

## Auto-Reload Configuration

The web dashboard reloads the config file on each startup. To reload without restarting:

```bash
sudo systemctl restart tidbyt.service
```

Or edit tidbyt_main.py to watch the config file for changes and reload automatically.

## Resources

- Systemd docs: https://www.freedesktop.org/wiki/Software/systemd/
- Raspberry Pi docs: https://www.raspberrypi.com/documentation/
- GPIO in systemd: https://forums.raspberrypi.com/

---

Happy displaying! 🎨
