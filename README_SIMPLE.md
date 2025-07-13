# NZ7DEV RDP/VNC Manager - Simplified Edition

A streamlined RDP/VNC session manager with dynamic machine detection and resolution presets.

## Features

- **Dynamic Machine Detection**: Automatically scans network for machines with RDP/VNC enabled
- **Dual Protocol Support**: Connect via RDP (xfreerdp) or VNC (Remmina)
- **Standardized Credentials**: Uses nz7dev/lemon for all connections
- **Resolution Presets**: Save and manage custom resolution presets
- **Dark Mode Interface**: Modern dark theme for better visibility
- **Simple Data Table**: Clean interface showing all discovered machines
- **One-Click Connect/Disconnect**: Easy session management

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements_simple.txt
```

2. Ensure required clients are installed:
```bash
# Ubuntu/Debian
sudo apt install freerdp2-x11 remmina

# Arch Linux
sudo pacman -S freerdp remmina
```

## Usage

1. Start the application:
```bash
python3 nz7dev_rdp_simple.py
# or
./run_simple.sh
```

2. Open your browser to `http://localhost:5000`

3. The application will automatically scan your network (192.168.1.x) for machines

4. Use the web interface to:
   - View discovered machines with RDP/VNC capabilities
   - Connect to sessions using your preferred protocol
   - Add/delete custom resolution presets
   - Refresh network scan

## Default Resolution Presets

- **Full HD**: 1920×1080 (Standard 1080p)
- **HD**: 1280×720 (Standard 720p)
- **4K**: 3840×2160 (4K Ultra HD)
- **Wide**: 1920×1200 (Wide screen)
- **Compact**: 1024×768 (Compact screen)

## Protocol Support

### RDP (Remote Desktop Protocol)
- **Client**: xfreerdp
- **Port**: 3389
- **OS**: Typically Windows machines
- **Features**: Full desktop access, clipboard sharing, compression

### VNC (Virtual Network Computing)
- **Client**: Remmina
- **Port**: 5900
- **OS**: Linux, Windows, macOS
- **Features**: Cross-platform remote desktop access

## Network Configuration

By default, the application scans the `192.168.1.x` network range. To change this, modify the `network_base` parameter in the `MachineScanner` class initialization.

## Credentials

All connections use the standardized credentials:
- **Username**: nz7dev
- **Password**: lemon

## Interface

The application features a modern dark mode interface with:
- **Color-coded service badges**: RDP (blue), VNC (orange)
- **Connection status indicators**: Online/offline, connected/disconnected
- **Smart connection buttons**: Only show available protocols
- **Real-time updates**: Auto-refresh every 30 seconds

## File Structure

- `nz7dev_rdp_simple.py` - Main application
- `templates/index.html` - Dark mode web interface
- `presets.json` - Resolution presets storage (auto-created)
- `rdp_manager.log` - Application logs
- `run_simple.sh` - Launcher script with dependency checking

## Troubleshooting

1. **No machines found**: Ensure machines are online and RDP/VNC is enabled
2. **Connection failed**: Check credentials and network connectivity
3. **xfreerdp not found**: Install FreeRDP client package
4. **Remmina not found**: Install Remmina VNC client package
5. **Permission denied**: Ensure user has network access permissions

## API Endpoints

- `GET /api/machines` - Get discovered machines
- `POST /api/machines/refresh` - Refresh network scan
- `POST /api/connect` - Connect to RDP/VNC session
- `POST /api/disconnect` - Disconnect session
- `GET /api/presets` - Get resolution presets
- `POST /api/presets` - Add resolution preset
- `DELETE /api/presets/<key>` - Delete resolution preset

## Dependencies

- **Python**: Flask, psutil
- **RDP Client**: xfreerdp (FreeRDP)
- **VNC Client**: Remmina
- **Network**: Port 3389 (RDP), Port 5900 (VNC) access 