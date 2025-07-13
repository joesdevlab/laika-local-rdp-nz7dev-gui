#!/usr/bin/env python3
"""
NZ7DEV RDP/VNC/SSH Manager - Simplified Edition
Basic RDP/VNC/SSH session management with machine detection and resolution presets
"""

import os
import json
import subprocess
import threading
import time
import logging
import socket
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from flask import Flask, render_template, request, jsonify
import concurrent.futures

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rdp_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'nz7dev-rdp-manager-2024'

# Standard credentials
STANDARD_USERNAME = "nz7dev"
STANDARD_PASSWORD = "lemonlime"

@dataclass
class Machine:
    """Machine data with multiple service support"""
    ip: str
    hostname: str = ""
    os_version: str = "Unknown"
    online: bool = False
    rdp_enabled: bool = False
    vnc_enabled: bool = False
    ssh_enabled: bool = False
    connected: bool = False
    connection_id: Optional[str] = None
    connection_type: Optional[str] = None
    last_seen: Optional[datetime] = None

@dataclass
class ResolutionPreset:
    """Resolution preset data"""
    name: str
    width: int
    height: int
    description: str = ""

@dataclass
class Connection:
    """Active connection (RDP/VNC/SSH)"""
    connection_id: str
    ip: str
    process: subprocess.Popen
    resolution: str
    connection_type: str  # 'rdp', 'vnc', or 'ssh'
    started: datetime

class ResolutionManager:
    """Manage resolution presets for RDP connections"""
    
    def __init__(self, presets_file: str = "presets.json"):
        self.presets_file = presets_file
        self.presets: Dict[str, ResolutionPreset] = {}
        self.load_presets()
    
    def load_presets(self):
        """Load presets from JSON file"""
        default_presets = {
            "full_hd": ResolutionPreset("Full HD", 1920, 1080, "Standard 1080p resolution"),
            "hd": ResolutionPreset("HD", 1280, 720, "Standard 720p resolution"),
            "4k": ResolutionPreset("4K", 3840, 2160, "4K Ultra HD resolution"),
            "wide": ResolutionPreset("Wide", 1920, 1200, "Wide screen resolution"),
            "compact": ResolutionPreset("Compact", 1024, 768, "Compact resolution for smaller screens"),
            "custom_wide": ResolutionPreset("Custom Wide", 1918, 1040, "Custom wide format resolution"),
            "tall_screen": ResolutionPreset("Tall Screen", 1720, 1400, "Tall aspect ratio screen"),
            "ultrawide": ResolutionPreset("Ultrawide", 3438, 1400, "Ultrawide monitor resolution")
        }
        
        try:
            if os.path.exists(self.presets_file):
                with open(self.presets_file, 'r') as f:
                    data = json.load(f)
                    for key, preset_data in data.items():
                        self.presets[key] = ResolutionPreset(**preset_data)
                logger.info(f"Loaded {len(self.presets)} resolution presets")
            else:
                self.presets = default_presets
                self.save_presets()
                logger.info("Created default resolution presets")
        except Exception as e:
            logger.error(f"Failed to load presets: {e}")
            self.presets = default_presets
    
    def save_presets(self):
        """Save presets to JSON file"""
        try:
            data = {key: asdict(preset) for key, preset in self.presets.items()}
            with open(self.presets_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.presets)} resolution presets")
        except Exception as e:
            logger.error(f"Failed to save presets: {e}")
    
    def add_preset(self, name: str, width: int, height: int, description: str = "") -> bool:
        """Add new resolution preset"""
        try:
            key = name.lower().replace(' ', '_').replace('-', '_')
            self.presets[key] = ResolutionPreset(name, width, height, description)
            self.save_presets()
            logger.info(f"Added resolution preset: {name} ({width}x{height})")
            return True
        except Exception as e:
            logger.error(f"Failed to add preset: {e}")
            return False
    
    def edit_preset(self, key: str, name: str, width: int, height: int, description: str = "") -> bool:
        """Edit existing resolution preset"""
        try:
            if key in self.presets:
                self.presets[key] = ResolutionPreset(name, width, height, description)
                self.save_presets()
                logger.info(f"Updated resolution preset: {key} -> {name} ({width}x{height})")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to edit preset: {e}")
            return False
    
    def delete_preset(self, key: str) -> bool:
        """Delete resolution preset"""
        try:
            if key in self.presets:
                del self.presets[key]
                self.save_presets()
                logger.info(f"Deleted resolution preset: {key}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete preset: {e}")
            return False
    
    def get_presets(self) -> Dict[str, ResolutionPreset]:
        """Get all resolution presets"""
        return self.presets.copy()
    
    def get_preset(self, key: str) -> Optional[ResolutionPreset]:
        """Get specific resolution preset"""
        return self.presets.get(key)

class MachineScanner:
    """Scan network for machines with RDP/VNC/SSH enabled"""
    
    def __init__(self, network_base: str = "192.168.1"):
        self.network_base = network_base
        self.machines: Dict[str, Machine] = {}
        self.scan_lock = threading.Lock()
    
    
    def ping_host(self, ip: str, timeout: int = 1) -> bool:
        """Ping a host to check if it's online"""
        try:
            result = subprocess.run(
                ['ping', '-c', '1', '-W', str(timeout), ip],
                capture_output=True,
                timeout=timeout + 0.5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return False
    
    def check_port(self, ip: str, port: int, timeout: int = 1) -> bool:
        """Check if a port is open"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def check_rdp_port(self, ip: str, timeout: int = 1) -> bool:
        """Check if RDP port (3389) is open"""
        return self.check_port(ip, 3389, timeout)
    
    def check_vnc_port(self, ip: str, timeout: int = 1) -> bool:
        """Check if VNC port (5900) is open"""
        return self.check_port(ip, 5900, timeout)
    
    def check_ssh_port(self, ip: str, timeout: int = 1) -> bool:
        """Check if SSH port (22) is open"""
        return self.check_port(ip, 22, timeout)
    
    def get_hostname(self, ip: str) -> str:
        """Get hostname for IP address"""
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname
        except:
            return f"Unknown-{ip.split('.')[-1]}"
    
    def detect_os_type(self, ip: str, rdp_enabled: bool, vnc_enabled: bool, ssh_enabled: bool) -> str:
        """Detect OS type based on available services"""
        if rdp_enabled and ssh_enabled:
            return "Windows/WSL"
        elif rdp_enabled:
            return "Windows"
        elif vnc_enabled and ssh_enabled:
            return "Ubuntu Desktop"
        elif ssh_enabled:
            return "Linux Server"
        elif vnc_enabled:
            return "Linux/VNC"
        else:
            return "Unknown"
    
    def scan_single_host(self, ip: str) -> Optional[Machine]:
        """Scan a single host for RDP/VNC/SSH"""
        try:
            # Check for services first, then ping
            rdp_enabled = self.check_rdp_port(ip)
            vnc_enabled = self.check_vnc_port(ip)
            ssh_enabled = self.check_ssh_port(ip)
            
            # Only return if at least one service is available
            if not rdp_enabled and not vnc_enabled and not ssh_enabled:
                return None
            
            # If we found services, the machine is considered online
            # even if ping is disabled
            online = self.ping_host(ip)
            if not online and (rdp_enabled or vnc_enabled or ssh_enabled):
                online = True  # Services available = machine is online
            
            hostname = self.get_hostname(ip)
            os_version = self.detect_os_type(ip, rdp_enabled, vnc_enabled, ssh_enabled)
            
            return Machine(
                ip=ip,
                hostname=hostname,
                os_version=os_version,
                online=online,
                rdp_enabled=rdp_enabled,
                vnc_enabled=vnc_enabled,
                ssh_enabled=ssh_enabled,
                last_seen=datetime.now()
            )
        except Exception as e:
            logger.debug(f"Error scanning {ip}: {e}")
            return None
    
    def scan_network(self, start_ip: int = 1, end_ip: int = 254) -> Dict[str, Machine]:
        """Scan network range for machines with RDP/VNC/SSH"""
        logger.info(f"Scanning network {self.network_base}.{start_ip}-{end_ip}")
        
        discovered_machines = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            # Submit all scan tasks
            future_to_ip = {
                executor.submit(self.scan_single_host, f"{self.network_base}.{i}"): i
                for i in range(start_ip, end_ip + 1)
            }
            
            # Collect results
            for future in concurrent.futures.as_completed(future_to_ip):
                try:
                    machine = future.result()
                    if machine and (machine.rdp_enabled or machine.vnc_enabled or machine.ssh_enabled):
                        discovered_machines[machine.ip] = machine
                        services = []
                        if machine.rdp_enabled:
                            services.append("RDP")
                        if machine.vnc_enabled:
                            services.append("VNC")
                        if machine.ssh_enabled:
                            services.append("SSH")
                        logger.info(f"Found machine: {machine.ip} ({machine.hostname}) - {machine.os_version} - {'/'.join(services)}")
                except Exception as e:
                    logger.debug(f"Scan error: {e}")
        
        with self.scan_lock:
            # Update machines with discovered ones only
            self.machines.clear()
            self.machines.update(discovered_machines)
        
        logger.info(f"Network scan complete. Found {len(discovered_machines)} machines with RDP/VNC/SSH")
        return discovered_machines.copy()
    
    def get_machines(self) -> Dict[str, Machine]:
        """Get current machine list"""
        with self.scan_lock:
            return self.machines.copy()
    
    def refresh_scan(self):
        """Refresh network scan in background"""
        threading.Thread(target=self.scan_network, daemon=True).start()

class ConnectionManager:
    """Manage RDP/VNC/SSH connections"""
    
    def __init__(self, resolution_manager: ResolutionManager):
        self.resolution_manager = resolution_manager
        self.active_connections: Dict[str, Connection] = {}
        self.connection_lock = threading.Lock()
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        def cleanup_loop():
            while True:
                try:
                    self._cleanup_dead_connections()
                    time.sleep(30)
                except Exception as e:
                    logger.error(f"Cleanup error: {e}")
                    time.sleep(60)
        
        thread = threading.Thread(target=cleanup_loop, daemon=True)
        thread.start()
    
    def _cleanup_dead_connections(self):
        """Remove dead connections"""
        with self.connection_lock:
            dead_connections = [
                conn_id for conn_id, conn in self.active_connections.items()
                if conn.process.poll() is not None
            ]
            
            for conn_id in dead_connections:
                logger.info(f"Cleaning up dead connection: {conn_id}")
                del self.active_connections[conn_id]
    
    def connect_rdp(self, ip: str, resolution_key: str = "full_hd") -> Dict[str, str]:
        """Connect to RDP session using xfreerdp"""
        try:
            # Get resolution
            presets = self.resolution_manager.get_presets()
            if resolution_key not in presets:
                resolution_key = "full_hd"
            
            preset = presets[resolution_key]
            resolution = f"{preset.width}x{preset.height}"
            
            logger.info(f"Connecting to {ip} via RDP with resolution {resolution}")
            
            # Try multiple RDP connection methods
            connection_methods = [
                # Method 1: Standard connection
                [
                    'xfreerdp',
                    f'/v:{ip}',
                    f'/u:{STANDARD_USERNAME}',
                    f'/p:{STANDARD_PASSWORD}',
                    f'/w:{preset.width}',
                    f'/h:{preset.height}',
                    '/cert:ignore',
                    '/compression',
                    '/clipboard',
                    '+auto-reconnect',
                    '/log-level:ERROR'
                ],
                # Method 2: Disable NLA
                [
                    'xfreerdp',
                    f'/v:{ip}',
                    f'/u:{STANDARD_USERNAME}',
                    f'/p:{STANDARD_PASSWORD}',
                    f'/w:{preset.width}',
                    f'/h:{preset.height}',
                    '/cert:ignore',
                    '/compression',
                    '/clipboard',
                    '-authentication',
                    '/log-level:ERROR'
                ],
                # Method 3: Force RDP security
                [
                    'xfreerdp',
                    f'/v:{ip}',
                    f'/u:{STANDARD_USERNAME}',
                    f'/p:{STANDARD_PASSWORD}',
                    f'/w:{preset.width}',
                    f'/h:{preset.height}',
                    '/cert:ignore',
                    '/compression',
                    '/clipboard',
                    '/sec:rdp',
                    '-authentication',
                    '/log-level:ERROR'
                ],
                # Method 4: TLS security
                [
                    'xfreerdp',
                    f'/v:{ip}',
                    f'/u:{STANDARD_USERNAME}',
                    f'/p:{STANDARD_PASSWORD}',
                    f'/w:{preset.width}',
                    f'/h:{preset.height}',
                    '/cert:ignore',
                    '/clipboard',
                    '/sec:tls',
                    '-authentication',
                    '/log-level:ERROR'
                ]
            ]
            
            process = None
            last_error = ""
            
            for i, cmd in enumerate(connection_methods, 1):
                logger.info(f"Trying RDP connection method {i} to {ip}")
                try:
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.PIPE,
                        start_new_session=True
                    )
                    
                    # Wait to see if connection succeeds
                    time.sleep(2)
                    if process.poll() is None:
                        # Process is still running, connection likely successful
                        logger.info(f"RDP connection method {i} succeeded")
                        break
                    else:
                        # Process exited, connection failed
                        _, stderr = process.communicate()
                        last_error = stderr.decode() if stderr else f"Method {i} failed"
                        logger.warning(f"RDP connection method {i} failed: {last_error}")
                        process = None
                        
                except Exception as e:
                    logger.warning(f"RDP connection method {i} exception: {e}")
                    last_error = str(e)
                    process = None
            
            if process is None:
                return {"success": False, "error": f"RDP connection failed with all methods. Last error: {last_error}"}
            
            # Track connection
            connection_id = f"rdp_{ip}_{int(time.time())}"
            connection = Connection(
                connection_id=connection_id,
                ip=ip,
                process=process,
                resolution=resolution,
                connection_type="rdp",
                started=datetime.now()
            )
            
            with self.connection_lock:
                self.active_connections[connection_id] = connection
            
            logger.info(f"RDP connection started: {connection_id}")
            return {"success": True, "connection_id": connection_id}
            
        except Exception as e:
            logger.error(f"Failed to connect to {ip} via RDP: {e}")
            return {"success": False, "error": str(e)}
    
    def connect_vnc(self, ip: str, resolution_key: str = "full_hd") -> Dict[str, str]:
        """Connect to VNC session using vncviewer or Remmina"""
        try:
            logger.info(f"Connecting to {ip} via VNC")
            
            # Try vncviewer first, then fall back to Remmina
            cmd = None
            
            # Check if vncviewer is available
            try:
                subprocess.run(['which', 'vncviewer'], check=True, capture_output=True)
                cmd = [
                    'vncviewer',
                    f'{ip}:5900',
                    '-passwd',
                    '/dev/stdin'
                ]
                # For vncviewer, we need to pass password differently
                process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                # Send password
                process.stdin.write(f'{STANDARD_PASSWORD}\n'.encode())
                process.stdin.close()
                
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Fall back to Remmina
                cmd = [
                    'remmina',
                    '-c',
                    f'vnc://{ip}:5900'
                ]
                
                # Start VNC process with Remmina
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
            
            # Wait briefly to check if process started successfully
            time.sleep(0.5)
            if process.poll() is not None:
                return {"success": False, "error": "VNC client failed to start"}
            
            # Track connection
            connection_id = f"vnc_{ip}_{int(time.time())}"
            connection = Connection(
                connection_id=connection_id,
                ip=ip,
                process=process,
                resolution="auto",  # VNC uses auto resolution
                connection_type="vnc",
                started=datetime.now()
            )
            
            with self.connection_lock:
                self.active_connections[connection_id] = connection
            
            logger.info(f"VNC connection started: {connection_id}")
            return {"success": True, "connection_id": connection_id}
            
        except Exception as e:
            logger.error(f"Failed to connect to {ip} via VNC: {e}")
            return {"success": False, "error": str(e)}
    
    def connect_ssh(self, ip: str, resolution_key: str = "full_hd") -> Dict[str, str]:
        """Connect to SSH session using available terminal"""
        try:
            logger.info(f"Connecting to {ip} via SSH")
            
            # Try different terminal emulators
            terminal_commands = [
                # Kitty
                ['kitty', '--title', f'SSH: {ip}', 'ssh', f'{STANDARD_USERNAME}@{ip}'],
                # GNOME Terminal
                ['gnome-terminal', '--title', f'SSH: {ip}', '--', 'ssh', f'{STANDARD_USERNAME}@{ip}'],
                # Konsole
                ['konsole', '--title', f'SSH: {ip}', '-e', 'ssh', f'{STANDARD_USERNAME}@{ip}'],
                # xterm
                ['xterm', '-title', f'SSH: {ip}', '-e', 'ssh', f'{STANDARD_USERNAME}@{ip}'],
                # Alacritty
                ['alacritty', '--title', f'SSH: {ip}', '-e', 'ssh', f'{STANDARD_USERNAME}@{ip}']
            ]
            
            process = None
            cmd_used = None
            
            for cmd in terminal_commands:
                try:
                    # Check if terminal is available
                    subprocess.run(['which', cmd[0]], check=True, capture_output=True)
                    
                    # Start SSH process in terminal
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True
                    )
                    cmd_used = cmd[0]
                    break
                    
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
            
            if process is None:
                return {"success": False, "error": "No suitable terminal emulator found"}
            
            # Wait briefly to check if process started successfully
            time.sleep(0.5)
            if process.poll() is not None:
                return {"success": False, "error": f"SSH terminal ({cmd_used}) failed to start"}
            
            # Track connection
            connection_id = f"ssh_{ip}_{int(time.time())}"
            connection = Connection(
                connection_id=connection_id,
                ip=ip,
                process=process,
                resolution="terminal",  # SSH doesn't use resolution
                connection_type="ssh",
                started=datetime.now()
            )
            
            with self.connection_lock:
                self.active_connections[connection_id] = connection
            
            logger.info(f"SSH connection started: {connection_id} using {cmd_used}")
            return {"success": True, "connection_id": connection_id}
            
        except Exception as e:
            logger.error(f"Failed to connect to {ip} via SSH: {e}")
            return {"success": False, "error": str(e)}
    
    def connect(self, ip: str, connection_type: str, resolution_key: str = "full_hd") -> Dict[str, str]:
        """Connect to RDP/VNC/SSH session"""
        try:
            # Check if already connected
            existing = self.get_connection_by_ip(ip)
            if existing:
                return {"success": False, "error": f"Already connected to {ip}"}
            
            if connection_type == "rdp":
                return self.connect_rdp(ip, resolution_key)
            elif connection_type == "vnc":
                return self.connect_vnc(ip, resolution_key)
            elif connection_type == "ssh":
                return self.connect_ssh(ip, resolution_key)
            else:
                return {"success": False, "error": "Invalid connection type"}
                
        except Exception as e:
            logger.error(f"Failed to connect to {ip}: {e}")
            return {"success": False, "error": str(e)}
    
    def disconnect(self, ip: str) -> Dict[str, str]:
        """Disconnect session by IP"""
        try:
            connection = self.get_connection_by_ip(ip)
            if not connection:
                return {"success": False, "error": f"No connection found for {ip}"}
            
            logger.info(f"Disconnecting from {ip} ({connection.connection_type.upper()})")
            
            # Kill process
            try:
                # First try graceful termination
                connection.process.terminate()
                connection.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    # Force kill if graceful termination fails
                    connection.process.kill()
                    connection.process.wait(timeout=2)
                except (subprocess.TimeoutExpired, ProcessLookupError):
                    pass
            except ProcessLookupError:
                pass
            
            # Remove from tracking
            with self.connection_lock:
                del self.active_connections[connection.connection_id]
            
            logger.info(f"Disconnected from {ip}")
            return {"success": True, "message": f"Disconnected from {ip}"}
            
        except Exception as e:
            logger.error(f"Failed to disconnect from {ip}: {e}")
            return {"success": False, "error": str(e)}
    
    def get_connection_by_ip(self, ip: str) -> Optional[Connection]:
        """Get connection by IP address"""
        with self.connection_lock:
            for connection in self.active_connections.values():
                if connection.ip == ip:
                    return connection
            return None
    
    def get_active_connections(self) -> Dict[str, Connection]:
        """Get all active connections"""
        with self.connection_lock:
            return self.active_connections.copy()

class RemoteApp:
    """Main RDP/VNC/SSH application"""
    
    def __init__(self):
        self.resolution_manager = ResolutionManager()
        self.connection_manager = ConnectionManager(self.resolution_manager)
        self.machine_scanner = MachineScanner()
        self.last_scan_time = None
        
        # Initial scan
        self.refresh_machines()
    
    def refresh_machines(self):
        """Refresh machine scan"""
        self.machine_scanner.refresh_scan()
        self.last_scan_time = datetime.now()
    
    def get_machines_with_status(self) -> List[Dict]:
        """Get machines with connection status"""
        machines = self.machine_scanner.get_machines()
        active_connections = self.connection_manager.get_active_connections()
        
        result = []
        for ip, machine in machines.items():
            # Check if connected
            connection = next((conn for conn in active_connections.values() if conn.ip == ip), None)
            connected = connection is not None
            connection_type = connection.connection_type if connection else None
            
            result.append({
                "ip": machine.ip,
                "hostname": machine.hostname,
                "os_version": machine.os_version,
                "online": machine.online,
                "rdp_enabled": machine.rdp_enabled,
                "vnc_enabled": machine.vnc_enabled,
                "ssh_enabled": machine.ssh_enabled,
                "connected": connected,
                "connection_type": connection_type,
                "last_seen": machine.last_seen.isoformat() if machine.last_seen else None
            })
        
        return result

# Global app instance
remote_app = RemoteApp()

# API Routes
@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/machines')
def api_machines():
    """Get all machines"""
    machines = remote_app.get_machines_with_status()
    return jsonify({
        "success": True,
        "machines": machines,
        "last_scan": remote_app.last_scan_time.isoformat() if remote_app.last_scan_time else None
    })

@app.route('/api/machines/refresh', methods=['POST'])
def api_refresh_machines():
    """Refresh machine scan"""
    remote_app.refresh_machines()
    return jsonify({"success": True, "message": "Machine scan started"})

@app.route('/api/connect', methods=['POST'])
def api_connect():
    """Connect to RDP/VNC/SSH session"""
    data = request.get_json()
    if not data or 'ip' not in data:
        return jsonify({"success": False, "error": "IP address required"}), 400
    
    ip = data['ip']
    connection_type = data.get('connection_type', 'rdp')
    resolution_key = data.get('resolution', 'full_hd')
    
    result = remote_app.connection_manager.connect(ip, connection_type, resolution_key)
    return jsonify(result)

@app.route('/api/disconnect', methods=['POST'])
def api_disconnect():
    """Disconnect session"""
    data = request.get_json()
    if not data or 'ip' not in data:
        return jsonify({"success": False, "error": "IP address required"}), 400
    
    ip = data['ip']
    result = remote_app.connection_manager.disconnect(ip)
    return jsonify(result)

@app.route('/api/presets')
def api_get_presets():
    """Get resolution presets"""
    presets = remote_app.resolution_manager.get_presets()
    return jsonify({
        "success": True,
        "presets": {key: asdict(preset) for key, preset in presets.items()}
    })

@app.route('/api/presets', methods=['POST'])
def api_add_preset():
    """Add resolution preset"""
    data = request.get_json()
    if not data or not all(key in data for key in ['name', 'width', 'height']):
        return jsonify({"success": False, "error": "Name, width, and height required"}), 400
    
    success = remote_app.resolution_manager.add_preset(
        data['name'],
        int(data['width']),
        int(data['height']),
        data.get('description', '')
    )
    
    return jsonify({"success": success})

@app.route('/api/presets/<preset_key>', methods=['PUT'])
def api_edit_preset(preset_key):
    """Edit resolution preset"""
    data = request.get_json()
    if not data or not all(key in data for key in ['name', 'width', 'height']):
        return jsonify({"success": False, "error": "Name, width, and height required"}), 400
    
    success = remote_app.resolution_manager.edit_preset(
        preset_key,
        data['name'],
        int(data['width']),
        int(data['height']),
        data.get('description', '')
    )
    
    return jsonify({"success": success})

@app.route('/api/presets/<preset_key>', methods=['DELETE'])
def api_delete_preset(preset_key):
    """Delete resolution preset"""
    success = remote_app.resolution_manager.delete_preset(preset_key)
    return jsonify({"success": success})

if __name__ == '__main__':
    # Create templates directory
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    print("🚀 NZ7DEV RDP/VNC/SSH Manager starting...")
    print("📡 Navigate to http://localhost:5001")
    print("🔑 Using standard credentials: nz7dev/lemonlime")
    print("🖥️  Supports RDP (xfreerdp), VNC (Remmina), SSH (Kitty)")
    print("📐 Resolution presets available for RDP connections")
    print("🔍 Scanning network for RDP/VNC/SSH enabled machines")
    
    try:
        app.run(host='0.0.0.0', port=5001, debug=True)
    except KeyboardInterrupt:
        logger.info("Shutting down...") 