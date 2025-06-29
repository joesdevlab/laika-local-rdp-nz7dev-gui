# 🚀 NZ7DEV Mission Control GUI

A modern, web-based interface for managing your NZ7DEV development environment with real-time RDP connection control and dynamic window positioning.

## ✨ Features

### 🎯 **Real-time Fleet Management**
- Live status monitoring of all 6 VMs (ALPHA, BRAVO, CHARLIE, DELTA, ECHO, FOXTROT)
- Network connectivity and RDP connection status
- Window positioning and workspace assignment tracking

### 🖥️ **Dynamic Control Interface**
- Individual VM control (start/stop/enable/disable)
- Real-time configuration updates
- Visual workspace layout representation
- One-click mission sequences

### 🚀 **Mission Control Integration**
- **Morning Routine** - Complete automated startup
- **Launch Fleet** - Start all RDP connections
- **LUDICROUS SPEED** - Ultra-fast window positioning
- **Position Windows** - Organize workspace layout
- **Emergency Stop** - Instant shutdown of all operations

### 📊 **Live Monitoring**
- WebSocket-powered real-time updates
- Connection status indicators
- Activity logging
- Configuration persistence

## 🛠️ Installation & Setup

### Prerequisites
- Linux system with Hyprland window manager
- Python 3.6+
- Your existing `nz7dev` bash script
- Network access to your VMs (192.168.1.20-26)

### Quick Start

1. **Place the GUI files** in the same directory as your `nz7dev` script:
   ```bash
   # Your directory should contain:
   # ├── nz7dev                 (your existing script)
   # ├── nz7dev_gui.py          (GUI backend)
   # ├── requirements.txt       (Python dependencies)
   # ├── run_gui.sh            (launcher script)
   # └── templates/
   #     └── index.html         (web interface)
   ```

2. **Launch the GUI:**
   ```bash
   ./run_gui.sh
   ```

3. **Open your browser** and navigate to:
   - Local: `http://localhost:5000`
   - Network: `http://YOUR_IP:5000`

The launcher script will automatically:
- Check dependencies
- Create a Python virtual environment
- Install required packages
- Start the GUI server

## 🎮 Using the Interface

### Main Dashboard
The dashboard displays all 6 VMs in a card-based layout showing:
- **Callsign** (ALPHA, BRAVO, etc.)
- **Network Status** (Online/Offline)
- **RDP Connection** (Connected/Disconnected)
- **Window Status** (Active/Inactive)
- **Configuration** (Geometry, workspace, position)

### VM Controls
Each VM card provides:
- **Toggle Switch** - Enable/disable VM for operations
- **Start Button** - Initiate RDP connection
- **Stop Button** - Terminate RDP connection
- **Config Button** - Modify VM settings (coming soon)

### Mission Control Panel
Quick access buttons for:
- 🌅 **Morning Routine** - Full automated startup
- 🚀 **Launch Fleet** - Start all enabled RDP connections
- ⚡ **LUDICROUS SPEED** - Ultra-fast fleet + positioning
- 🪟 **Position Windows** - Organize all windows
- 🛑 **Emergency Stop** - Abort all operations

### Workspace Visualization
Visual representation of:
- **Workspace 1-4** - Showing assigned VMs
- **Scratchpad** - Special workspace for specific VMs
- Real-time updates as configurations change

## ⚙️ Configuration

### VM Fleet Settings
The GUI manages the same VM configuration as your bash script:

| VM | Callsign | IP | Workspace | Position | Scratchpad |
|---|---|---|---|---|---|
| vm20 | ALPHA | 192.168.1.20 | 4 | left | No |
| vm21 | BRAVO | 192.168.1.21 | 2 | left | Yes |
| vm23 | CHARLIE | 192.168.1.23 | 1 | center | No |
| vm24 | DELTA | 192.168.1.24 | 4 | right | No |
| vm25 | ECHO | 192.168.1.25 | 2 | right | Yes |
| vm26 | FOXTROT | 192.168.1.26 | 3 | center | No |

### Dynamic Updates
- Configuration changes are saved to `~/.nz7dev/config/mission.yaml`
- Changes are immediately reflected in both GUI and bash script
- Real-time synchronization via WebSocket

## 🔧 Advanced Usage

### API Endpoints
The GUI provides a REST API for programmatic control:

```bash
# Get fleet status
curl http://localhost:5000/api/status

# Start specific VM
curl -X POST http://localhost:5000/api/vm/vm20/start

# Stop specific VM
curl -X POST http://localhost:5000/api/vm/vm20/stop

# Update VM configuration
curl -X POST -H "Content-Type: application/json" \
  -d '{"workspace": 3, "position": "center"}' \
  http://localhost:5000/api/vm/vm20/config

# Execute mission commands
curl -X POST http://localhost:5000/api/fleet/morning
curl -X POST http://localhost:5000/api/fleet/fastup
```

### Integration with Existing Script
The GUI seamlessly integrates with your existing `nz7dev` script:
- Uses the same configuration files
- Executes the same mission sequences
- Provides additional real-time monitoring
- Maintains full compatibility

### Network Access
Access the GUI from any device on your network:
```bash
# Find your IP address
hostname -I

# Access from other devices
http://YOUR_IP_ADDRESS:5000
```

## 🎨 Interface Highlights

### NASA Mission Control Theme
- Dark space-themed design
- Blue and cyan accent colors
- Animated status indicators
- Professional typography

### Real-time Updates
- WebSocket connection for instant updates
- Live status monitoring every 5 seconds
- Immediate feedback on all operations
- Toast notifications for actions

### Responsive Design
- Works on desktop and mobile devices
- Adaptive layout for different screen sizes
- Touch-friendly controls
- Optimized for productivity

## 🚨 Troubleshooting

### Common Issues

**GUI won't start:**
```bash
# Check if port 5000 is available
netstat -tuln | grep :5000

# Kill any existing processes
pkill -f nz7dev_gui.py
```

**VMs not connecting:**
- Verify VM IP addresses are reachable
- Check network connectivity: `ping 192.168.1.20`
- Ensure RDP services are running on VMs
- Verify credentials in configuration

**WebSocket connection failed:**
- Check firewall settings
- Ensure port 5000 is accessible
- Restart the GUI server

**Missing dependencies:**
```bash
# Reinstall dependencies
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

### Logging
Check GUI logs for detailed information:
```bash
# View real-time logs
tail -f ~/.nz7dev/logs/mission_control.log

# Check GUI server output
# (displayed in terminal where GUI is running)
```

## 🤝 Integration with Original Script

The GUI enhances your existing workflow without replacing it:

### Command Line (Original)
```bash
./nz7dev morning    # Full morning routine
./nz7dev up         # Launch fleet
./nz7dev status     # Check status
./nz7dev down       # Emergency stop
```

### Web Interface (New)
- Same functionality with visual interface
- Real-time monitoring and control
- Individual VM management
- Dynamic configuration

### Best of Both Worlds
- Use GUI for monitoring and control
- Use CLI for automation and scripting
- Both share the same configuration
- Seamless interoperability

## 📈 Future Enhancements

Planned features for future releases:
- [ ] Drag-and-drop workspace assignment
- [ ] Custom VM configurations
- [ ] Performance metrics and graphs
- [ ] Dark/light theme toggle
- [ ] Mobile app companion
- [ ] Multi-user access control
- [ ] Configuration templates
- [ ] Automated health checks

## 🎯 Mission Accomplished!

Your NZ7DEV Mission Control GUI is now ready for deployment! This interface provides:

✅ **Complete visual control** over your development environment  
✅ **Real-time monitoring** of all systems  
✅ **Dynamic configuration** management  
✅ **Professional NASA-themed** interface  
✅ **Full integration** with existing automation  

**Ready to launch?** Run `./run_gui.sh` and navigate to `http://localhost:5000` to take control of your development fleet!

---

*Built with ❤️ for the NZ7DEV Mission Control System* 