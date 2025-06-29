# 🚀 NZ7DEV GUI - Always-On Setup Guide

This guide shows you how to keep your NZ7DEV Mission Control GUI always available without manually running scripts.

## 🎯 Quick Setup (Recommended)

### Option 1: Install as System Service (Best for Always-On)

```bash
# Run the initial setup once
./run_gui.sh   # This creates the virtual environment and installs dependencies

# Install as a service that runs automatically
./install_service.sh install
```

**That's it!** Your GUI is now:
- ✅ Running automatically
- ✅ Starts on login  
- ✅ Restarts if it crashes
- ✅ Available at `http://localhost:5000`

### Quick Service Commands

```bash
./install_service.sh status    # Check if running
./install_service.sh logs      # View real-time logs
./install_service.sh restart   # Restart the service
./install_service.sh url       # Show access URLs
./install_service.sh stop      # Stop temporarily
./install_service.sh start     # Start again
```

## 🔧 Alternative Options

### Option 2: Manual Background Process

If you prefer not to use systemd:

```bash
# Start in background (survives terminal close)
nohup ./run_gui.sh > gui.log 2>&1 &

# Check if running
ps aux | grep nz7dev_gui

# Stop manually
pkill -f nz7dev_gui.py
```

### Option 3: Desktop Autostart

Add to your desktop environment's autostart:

```bash
# Copy desktop entry to autostart
mkdir -p ~/.config/autostart
cp nz7dev-gui.desktop ~/.config/autostart/

# Or add to your shell profile
echo './path/to/nz7dev-gui/run_gui.sh &' >> ~/.bashrc
```

### Option 4: Tmux/Screen Session

For development use:

```bash
# Create persistent tmux session
tmux new-session -d -s nz7dev-gui './run_gui.sh'

# Attach to see logs
tmux attach -t nz7dev-gui

# Detach with Ctrl+B, D (session continues running)
```

## 📊 Service Management

### Check Status
```bash
./install_service.sh status
```

### View Logs
```bash
# Real-time logs
./install_service.sh logs

# Recent logs only  
journalctl --user -u nz7dev-gui -n 50

# All logs since boot
journalctl --user -u nz7dev-gui --since "today"
```

### Performance Monitoring
```bash
# Check resource usage
systemctl --user show nz7dev-gui --property=MemoryCurrent
systemctl --user show nz7dev-gui --property=CPUUsageNSec

# See service details
systemctl --user status nz7dev-gui
```

## 🌐 Access Methods

Once running, access your GUI from:

| Method | URL | Best For |
|---|---|---|
| **Local Browser** | `http://localhost:5000` | Same machine |
| **IP Address** | `http://YOUR_IP:5000` | Other devices on network |
| **Desktop Shortcut** | Click "NZ7DEV Mission Control" in apps | Quick access |
| **Bookmark** | Save `localhost:5000` in browser | Daily use |

### Find Your Network IP
```bash
hostname -I | awk '{print $1}'
# Example: 192.168.1.100

# Then access from other devices:
# http://192.168.1.100:5000
```

## 🔒 Security Considerations

### Network Access
The GUI runs on `0.0.0.0:5000` (all interfaces) by default for network access.

**To restrict to localhost only**, edit `nz7dev_gui.py`:
```python
# Change this line:
socketio.run(app, host='0.0.0.0', port=5000, debug=True)

# To this:
socketio.run(app, host='127.0.0.1', port=5000, debug=True)
```

### Firewall Configuration
```bash
# Allow access from your network (optional)
sudo ufw allow from 192.168.1.0/24 to any port 5000

# Or allow all access (less secure)
sudo ufw allow 5000
```

## 🛠️ Troubleshooting

### GUI Not Starting
```bash
# Check if port is already in use
netstat -tuln | grep :5000

# Kill any existing processes
pkill -f nz7dev_gui.py

# Check service logs
./install_service.sh logs
```

### Service Issues
```bash
# Reload systemd if service file changed
systemctl --user daemon-reload

# Reset failed services
systemctl --user reset-failed

# Reinstall service
./install_service.sh uninstall
./install_service.sh install
```

### Dependencies Missing
```bash
# Reinstall Python dependencies
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

### Permission Issues
```bash
# Fix script permissions
chmod +x nz7dev
chmod +x run_gui.sh
chmod +x install_service.sh

# Fix virtual environment
rm -rf venv
./run_gui.sh  # Recreates venv
```

## 📱 Mobile Access

The GUI works great on mobile devices:

1. **Find your computer's IP**: `hostname -I`
2. **Connect phone/tablet to same WiFi**
3. **Open browser to**: `http://YOUR_IP:5000`
4. **Add to home screen** for app-like experience

## 🎮 Integration Tips

### Browser Bookmarks
- **Chrome**: ⭐ Bookmark `http://localhost:5000`
- **Firefox**: Add to bookmark bar
- **Mobile**: "Add to Home Screen"

### Desktop Integration
```bash
# Add to applications menu
cp nz7dev-gui.desktop ~/.local/share/applications/

# Update desktop database
update-desktop-database ~/.local/share/applications/
```

### Keyboard Shortcuts
Add to your window manager config:
```bash
# Hyprland example (~/.config/hypr/hyprland.conf)
bind = SUPER, F5, exec, xdg-open http://localhost:5000
```

## 🔄 Updates and Maintenance

### Updating the GUI
```bash
# Stop service
./install_service.sh stop

# Update files (git pull, copy new files, etc.)
# ...

# Restart service  
./install_service.sh start
```

### Backup Configuration
```bash
# Backup your VM configurations
cp -r ~/.nz7dev/config ~/nz7dev-backup/

# Backup service files
cp ~/.config/systemd/user/nz7dev-gui.service ~/nz7dev-backup/
```

## 💡 Pro Tips

1. **Bookmark this URL**: `http://localhost:5000` for instant access
2. **Use service logs** for debugging: `./install_service.sh logs`
3. **Mobile bookmark**: Add to phone home screen for native app feel
4. **Network access**: Share with team members via your IP address
5. **Always check status**: `./install_service.sh status` shows everything

## 🎯 Summary

**For most users, the recommended setup is:**

```bash
# One-time setup
./run_gui.sh                    # Initial setup
./install_service.sh install    # Install as service

# Daily usage
# Just open browser to http://localhost:5000
# GUI is always running in background!
```

Your NZ7DEV Mission Control GUI will now be available 24/7 without any manual intervention! 🚀 