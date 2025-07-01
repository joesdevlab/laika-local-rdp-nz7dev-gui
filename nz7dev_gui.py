#!/usr/bin/env python3
"""
NZ7DEV Mission Control GUI - Optimized Edition
A high-performance web-based interface for managing RDP connections and window positioning
"""

import os
import json
import subprocess
import threading
import time
import yaml
import logging
import asyncio
import concurrent.futures
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from functools import lru_cache, wraps
from flask import Flask, render_template, request, jsonify, abort
from flask_socketio import SocketIO, emit
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mission_control.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Performance optimizations
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'nz7dev-mission-control-2024')
app.config['JSON_SORT_KEYS'] = False  # Disable key sorting for performance
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Custom log handler for WebSocket emission
class WebSocketLogHandler(logging.Handler):
    def emit(self, record):
        try:
            log_data = {
                'message': record.getMessage(),
                'level': record.levelname,
                'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'logger': record.name
            }
            socketio.emit('log_message', log_data)
        except Exception:
            pass  # Silently ignore errors in log emission

# Add WebSocket handler to logger
websocket_handler = WebSocketLogHandler()
websocket_handler.setLevel(logging.INFO)
logger.addHandler(websocket_handler)

# Configuration Management
@dataclass
class VMConfig:
    """VM Configuration with validation"""
    callsign: str
    ip: str
    credentials: str
    geometry: str
    workspace: int
    position: str
    scratchpad: bool = False
    enabled: bool = True
    
    def __post_init__(self):
        """Validate configuration on creation"""
        if not self.ip or not self._is_valid_ip(self.ip):
            raise ValueError(f"Invalid IP address: {self.ip}")
        if self.workspace < 1 or self.workspace > 10:
            raise ValueError(f"Workspace must be 1-10: {self.workspace}")
        if self.position not in ['left', 'center', 'right']:
            raise ValueError(f"Position must be left/center/right: {self.position}")
    
    @staticmethod
    def _is_valid_ip(ip: str) -> bool:
        """Basic IP validation"""
        parts = ip.split('.')
        return len(parts) == 4 and all(part.isdigit() and 0 <= int(part) <= 255 for part in parts)

@dataclass
class ConnectionInfo:
    """RDP Connection tracking"""
    connection_id: str
    process: subprocess.Popen
    ip: str
    username: str
    geometry: str
    workspace: int
    position: str
    started: datetime
    last_checked: Optional[datetime] = None
    status: str = 'running'

class ConfigManager:
    """Centralized configuration management"""
    
    def __init__(self):
        self.config_dir = os.path.expanduser('~/.nz7dev/config')
        self.config_file = os.path.join(self.config_dir, 'mission.yaml')
        self.script_path = './nz7dev'
        self._fleet_config = self._load_fleet_config()
    
    def _load_fleet_config(self) -> Dict[str, VMConfig]:
        """Load and validate fleet configuration"""
        default_config = {
            'vm20': VMConfig('ALPHA', '192.168.1.20', 'nz7dev:lemonlime', '957x1042', 4, 'left'),
            'vm21': VMConfig('BRAVO', '192.168.1.21', 'nz7dev:lemonlime', '1717x1402', 2, 'left', True),
            'vm23': VMConfig('CHARLIE', '192.168.1.23', 'User:lemonlime', '1915x1042', 1, 'center'),
            'vm24': VMConfig('DELTA', '192.168.1.24', 'nz7dev:lemonlime', '957x1042', 4, 'right'),
            'vm25': VMConfig('ECHO', '192.168.1.25', 'User:lemonlime', '1717x1402', 2, 'right', True),
            'vm26': VMConfig('FOXTROT', '192.168.1.26', 'User:lemonlime', '1915x1042', 3, 'center'),
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = yaml.safe_load(f)
                    # TODO: Parse from YAML and create VMConfig objects
                    return default_config
            return default_config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return default_config
    
    @property
    def fleet_config(self) -> Dict[str, VMConfig]:
        return self._fleet_config
    
    def update_vm_config(self, vm_name: str, updates: Dict[str, Any]) -> bool:
        """Update VM configuration with validation"""
        if vm_name not in self._fleet_config:
            return False
        
        try:
            current = asdict(self._fleet_config[vm_name])
            current.update(updates)
            self._fleet_config[vm_name] = VMConfig(**current)
            return self.save_config()
        except Exception as e:
            logger.error(f"Failed to update config for {vm_name}: {e}")
            return False
    
    def save_config(self) -> bool:
        """Save configuration to file"""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            # Convert to YAML format
            yaml_config = {
                'mission_control': {
                    'callsign': 'HOUSTON',
                    'commander': 'auto',
                    'log_level': 'INFO'
                },
                'development_fleet': {}
            }
            
            for vm_name, config in self._fleet_config.items():
                yaml_config['development_fleet'][vm_name] = {
                    'callsign': config.callsign,
                    'ip_address': config.ip,
                    'connection_type': 'rdp',
                    'credentials': config.credentials,
                    'display_geometry': config.geometry,
                    'workspace': config.workspace,
                    'position': config.position,
                    'scratchpad': config.scratchpad,
                    'auto_connect': config.enabled
                }
            
            with open(self.config_file, 'w') as f:
                yaml.dump(yaml_config, f, default_flow_style=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False

class NetworkOptimizer:
    """Optimized network operations with caching and connection pooling"""
    
    def __init__(self):
        self._ping_cache = {}
        self._cache_duration = timedelta(seconds=10)  # Cache ping results for 10 seconds
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
    
    def ping_target(self, ip: str, timeout: int = 1) -> bool:
        """Optimized ping with caching"""
        now = datetime.now()
        
        # Check cache first
        if ip in self._ping_cache:
            cached_time, cached_result = self._ping_cache[ip]
            if now - cached_time < self._cache_duration:
                return cached_result
        
        # Perform ping
        try:
            result = subprocess.run(
                ['ping', '-c', '1', '-W', str(timeout), ip],
                capture_output=True,
                timeout=timeout + 0.5,  # Slightly longer timeout for subprocess
                text=True
            )
            is_alive = result.returncode == 0
            self._ping_cache[ip] = (now, is_alive)
            return is_alive
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            self._ping_cache[ip] = (now, False)
            return False
    
    def ping_multiple(self, ips: List[str]) -> Dict[str, bool]:
        """Ping multiple IPs concurrently"""
        futures = {ip: self._executor.submit(self.ping_target, ip) for ip in ips}
        return {ip: future.result() for ip, future in futures.items()}
    
    def cleanup_cache(self):
        """Clean expired cache entries"""
        now = datetime.now()
        expired = [ip for ip, (timestamp, _) in self._ping_cache.items() 
                  if now - timestamp > self._cache_duration]
        for ip in expired:
            del self._ping_cache[ip]

class HyprlandManager:
    """Optimized Hyprland window management"""
    
    def __init__(self):
        self._clients_cache = None
        self._cache_time = None
        self._cache_duration = timedelta(seconds=2)  # Cache clients for 2 seconds
    
    @lru_cache(maxsize=32)
    def _get_cached_clients(self, timestamp: float) -> str:
        """Cache hyprctl clients output"""
        try:
            result = subprocess.run(
                ['hyprctl', 'clients', '-j'],  # JSON output for faster parsing
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.stdout if result.returncode == 0 else ""
        except subprocess.TimeoutExpired:
            logger.warning("hyprctl clients timed out")
            return ""
    
    def get_clients(self) -> List[Dict[str, Any]]:
        """Get hyprland clients with caching"""
        now = datetime.now()
        
        if (self._clients_cache is None or 
            self._cache_time is None or 
            now - self._cache_time > self._cache_duration):
            
            # Use timestamp for cache key to ensure fresh data
            timestamp = time.time()
            clients_json = self._get_cached_clients(timestamp)
            
            try:
                self._clients_cache = json.loads(clients_json) if clients_json else []
                self._cache_time = now
            except json.JSONDecodeError:
                logger.error("Failed to parse hyprctl clients JSON")
                self._clients_cache = []
        
        return self._clients_cache or []
    
    def check_window_exists(self, window_title: str) -> bool:
        """Check if window exists efficiently"""
        clients = self.get_clients()
        return any(client.get('title', '').startswith(window_title) for client in clients)
    
    def position_window(self, window_title: str, workspace: int, position: str, geometry: str) -> bool:
        """Position window with batch operations"""
        try:
            width, height = map(int, geometry.split('x'))
            
            # Calculate position
            position_map = {
                'center': (960, 100),
                'left': (100, 100),
                'right': (1800, 100)
            }
            x, y = position_map.get(position, (100, 100))
            
            # Batch hyprctl commands for efficiency
            commands = [
                f'movetoworkspacesilent {workspace},title:"{window_title}"',
                f'resizewindowpixel exact {width} {height},title:"{window_title}"',
                f'movewindowpixel exact {x} {y},title:"{window_title}"'
            ]
            
            # Execute as batch
            cmd = ['hyprctl', '--batch'] + [';'.join(commands)]
            result = subprocess.run(cmd, capture_output=True, timeout=5)
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Failed to position window {window_title}: {e}")
            return False

class RDPManager:
    """Optimized RDP connection management"""
    
    def __init__(self, hyprland_manager: HyprlandManager):
        self.hyprland = hyprland_manager
        self.active_connections: Dict[str, ConnectionInfo] = {}
        self._cleanup_thread = None
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        def cleanup_loop():
            while True:
                try:
                    self._cleanup_dead_connections()
                    time.sleep(30)  # Cleanup every 30 seconds
                except Exception as e:
                    logger.error(f"Cleanup thread error: {e}")
                    time.sleep(60)
        
        self._cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        self._cleanup_thread.start()
    
    def _cleanup_dead_connections(self):
        """Remove dead connections"""
        dead_connections = []
        for conn_id, conn_info in self.active_connections.items():
            if conn_info.process.poll() is not None:
                dead_connections.append(conn_id)
        
        for conn_id in dead_connections:
            logger.info(f"Cleaning up dead connection: {conn_id}")
            del self.active_connections[conn_id]
    
    def spawn_connection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Spawn RDP connection with optimization"""
        try:
            # Validate input
            required_fields = ['ip']
            if not all(field in params for field in required_fields):
                logger.warning("RDP spawn failed: Missing required fields")
                return {'success': False, 'error': 'Missing required fields'}
            
            ip = params['ip']
            username = params.get('username', 'User')
            password = params.get('password', 'lemonlime')
            geometry = params.get('geometry', '1920x1080')
            workspace = params.get('workspace', 1)
            position = params.get('position', 'center')
            fullscreen = params.get('fullscreen', False)
            
            logger.info(f"Spawning RDP connection to {ip} ({geometry}, workspace {workspace}) with user {username}")
            
            # Build optimized FreeRDP command
            cmd = [
                'xfreerdp',
                f'/v:{ip}',
                f'/u:{username}',
                f'/p:{password}',
                '/cert-ignore',
                '/compression',
                '/gfx:progressive',  # Better graphics performance
                '/network:auto',     # Automatic network optimization
                '/timeout:10000',    # Connection timeout
                '/log-level:WARN',   # Reduce log verbosity but capture errors
            ]
            
            # Add geometry or fullscreen
            if fullscreen:
                cmd.append('/f')
            else:
                cmd.append(f'/size:{geometry}')
            
            # Add optional features
            if params.get('drive_redirection', False):
                cmd.append('/drive:home,/home')
            
            if params.get('clipboard', True):
                cmd.append('+clipboard')
            
            if params.get('sound', False):
                cmd.append('/sound:sys:pulse')
            
            # Start connection with better error handling
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    preexec_fn=os.setsid  # Create new process group for better cleanup
                )
                logger.info(f"RDP process started for {ip} (PID: {process.pid})")
            except OSError as e:
                logger.error(f"Failed to start RDP client for {ip}: {e}")
                return {'success': False, 'error': f'Failed to start RDP client: {e}'}
            
            # Track connection
            connection_id = f"rdp_{ip}_{int(time.time())}"
            conn_info = ConnectionInfo(
                connection_id=connection_id,
                process=process,
                ip=ip,
                username=username,
                geometry=geometry,
                workspace=workspace,
                position=position,
                started=datetime.now()
            )
            
            self.active_connections[connection_id] = conn_info
            logger.info(f"RDP connection {connection_id} registered and tracking started")
            
            # Monitor connection status asynchronously
            def monitor_connection():
                try:
                    # Wait briefly for connection to establish or fail
                    time.sleep(2)
                    poll_result = process.poll()
                    
                    if poll_result is not None:
                        # Process has exited, check for errors
                        stdout, stderr = process.communicate(timeout=5)
                        if poll_result != 0:
                            # Connection failed
                            error_msg = "Connection failed"
                            if stderr:
                                stderr_str = stderr.decode('utf-8', errors='ignore')
                                if 'LOGON_FAILURE' in stderr_str:
                                    error_msg = f"Authentication failed - check username/password for {ip}"
                                elif 'CONNECTION_REFUSED' in stderr_str:
                                    error_msg = f"Connection refused by {ip} - RDP service may not be running"
                                elif 'NETWORK_ERROR' in stderr_str:
                                    error_msg = f"Network error connecting to {ip}"
                                else:
                                    error_msg = f"RDP connection to {ip} failed: {stderr_str.strip()[:200]}"
                            
                            logger.error(f"RDP connection to {ip} failed: {error_msg}")
                            # Connection will be cleaned up by the cleanup thread
                        else:
                            logger.info(f"RDP connection to {ip} established successfully")
                    
                    # Position window if process is still running
                    if process.poll() is None:
                        time.sleep(1)  # Additional wait for window to appear
                        window_title = f"FreeRDP: {ip}"
                        success = self.hyprland.position_window(window_title, workspace, position, geometry)
                        if success:
                            logger.info(f"Window positioned successfully for {ip}")
                        else:
                            # Try alternate window title formats
                            alternate_titles = [
                                f"{ip} - FreeRDP",
                                f"RDP - {ip}",
                                f"FreeRDP ({ip})"
                            ]
                            for title in alternate_titles:
                                success = self.hyprland.position_window(title, workspace, position, geometry)
                                if success:
                                    logger.info(f"Window positioned successfully for {ip} using title: {title}")
                                    break
                            else:
                                logger.warning(f"Failed to position window for {ip} - window title may not match expected format")
                    
                except Exception as e:
                    logger.error(f"Error monitoring connection to {ip}: {e}")
            
            threading.Thread(target=monitor_connection, daemon=True).start()
            
            return {
                'success': True,
                'connection_id': connection_id,
                'message': f'RDP connection to {ip} initiated - establishing connection...'
            }
            
        except Exception as e:
            logger.error(f"Failed to spawn RDP connection: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_active_connections(self) -> Dict[str, Dict[str, Any]]:
        """Get active connections with status"""
        self._cleanup_dead_connections()  # Clean before returning
        
        return {
            conn_id: {
                'ip': conn_info.ip,
                'username': conn_info.username,
                'geometry': conn_info.geometry,
                'workspace': conn_info.workspace,
                'position': conn_info.position,
                'started': conn_info.started.isoformat(),
                'duration': str(datetime.now() - conn_info.started),
                'status': 'running' if conn_info.process.poll() is None else 'stopped'
            }
            for conn_id, conn_info in self.active_connections.items()
        }
    
    def kill_connection(self, connection_id: str) -> Dict[str, Any]:
        """Kill specific connection"""
        if connection_id not in self.active_connections:
            logger.warning(f"Attempted to kill non-existent connection: {connection_id}")
            return {'success': False, 'error': 'Connection not found'}
        
        try:
            conn_info = self.active_connections[connection_id]
            logger.info(f"Terminating RDP connection {connection_id} to {conn_info.ip}")
            
            # Graceful shutdown first
            try:
                os.killpg(os.getpgid(conn_info.process.pid), 15)  # SIGTERM to process group
                conn_info.process.wait(timeout=5)
                logger.info(f"Connection {connection_id} terminated gracefully")
            except (subprocess.TimeoutExpired, ProcessLookupError, OSError):
                # Force kill if graceful shutdown fails
                try:
                    os.killpg(os.getpgid(conn_info.process.pid), 9)  # SIGKILL to process group
                    logger.warning(f"Connection {connection_id} force-killed after graceful shutdown failed")
                except (ProcessLookupError, OSError):
                    logger.info(f"Connection {connection_id} process already terminated")
                    pass  # Process already dead
            
            del self.active_connections[connection_id]
            logger.info(f"Connection {connection_id} removed from tracking")
            return {'success': True, 'message': 'Connection terminated successfully'}
            
        except Exception as e:
            logger.error(f"Failed to kill connection {connection_id}: {e}")
            return {'success': False, 'error': str(e)}

class MissionControl:
    """Optimized Mission Control with better performance"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.network_optimizer = NetworkOptimizer()
        self.hyprland_manager = HyprlandManager()
        self.rdp_manager = RDPManager(self.hyprland_manager)
        
        self.status_thread = None
        self.running = False
        self._last_status_update = None
        self._status_cache = None
        self._status_cache_duration = timedelta(seconds=3)  # Cache status for 3 seconds
    
    def start_monitoring(self):
        """Start optimized background monitoring"""
        if not self.running:
            self.running = True
            self.status_thread = threading.Thread(target=self._monitor_status, daemon=True)
            self.status_thread.start()
            logger.info("Mission Control monitoring started - real-time fleet status tracking active")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        logger.info("Mission Control monitoring stopped")
    
    def _monitor_status(self):
        """Optimized background monitoring with rate limiting"""
        logger.info("Background monitoring thread started")
        consecutive_errors = 0
        max_errors = 5
        
        while self.running:
            try:
                # Clean up caches periodically
                self.network_optimizer.cleanup_cache()
                
                # Get status and emit to connected clients
                status = self.get_fleet_status()
                socketio.emit('status_update', status)
                
                # Log status summary periodically (every 10th update)
                if hasattr(self, '_status_update_count'):
                    self._status_update_count += 1
                else:
                    self._status_update_count = 1
                
                if self._status_update_count % 10 == 0:
                    online_count = sum(1 for vm_data in status.values() if vm_data.get('online', False))
                    connected_count = sum(1 for vm_data in status.values() if vm_data.get('rdp_connected', False))
                    logger.info(f"Fleet status update #{self._status_update_count}: {online_count}/6 online, {connected_count}/6 RDP connected")
                
                # Reset error counter on success
                consecutive_errors = 0
                
                # Adaptive sleep based on number of connected clients
                connected_clients = len(socketio.server.manager.rooms.get('/', {}).keys())
                sleep_time = max(3, 8 - connected_clients)  # 3-8 seconds based on load
                time.sleep(sleep_time)
                
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Monitoring error #{consecutive_errors}: {e}")
                
                # If too many consecutive errors, increase sleep time
                if consecutive_errors >= max_errors:
                    logger.warning(f"Too many consecutive monitoring errors ({consecutive_errors}), increasing sleep time")
                    time.sleep(30)  # Sleep longer on persistent errors
                    consecutive_errors = 0  # Reset counter
                else:
                    time.sleep(10)
        
        logger.info("Background monitoring thread stopped")
    
    def get_fleet_status(self) -> Dict[str, Any]:
        """Get comprehensive fleet status with caching"""
        now = datetime.now()
        
        # Use cached status if recent
        if (self._status_cache and self._last_status_update and 
            now - self._last_status_update < self._status_cache_duration):
            return self._status_cache
        
        # Get all IPs for batch ping
        fleet_ips = [config.ip for config in self.config_manager.fleet_config.values()]
        ping_results = self.network_optimizer.ping_multiple(fleet_ips)
        
        # Build status for each VM
        status = {}
        for vm_name, config in self.config_manager.fleet_config.items():
            vm_status = {
                'name': vm_name,
                'callsign': config.callsign,
                'ip': config.ip,
                'geometry': config.geometry,
                'workspace': config.workspace,
                'position': config.position,
                'scratchpad': config.scratchpad,
                'enabled': config.enabled,
                'online': ping_results.get(config.ip, False),
                'rdp_connected': self._check_rdp_service(vm_name),
                'window_active': self.hyprland_manager.check_window_exists(f"FreeRDP: {config.ip}"),
                'last_updated': now.isoformat()
            }
            status[vm_name] = vm_status
        
        # Cache the result
        self._status_cache = status
        self._last_status_update = now
        
        return status
    
    def _check_rdp_service(self, vm_name: str) -> bool:
        """Check RDP service status with timeout"""
        try:
            service_name = f"nz7dev-{vm_name}.service"
            result = subprocess.run(
                ['systemctl', '--user', 'is-active', service_name],
                capture_output=True,
                text=True,
                timeout=3  # Increased timeout for reliability
            )
            is_active = result.stdout.strip() == 'active'
            if is_active:
                logger.debug(f"RDP service {service_name} is active")
            return is_active
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def execute_script_command(self, command: str) -> Dict[str, Any]:
        """Execute nz7dev script with timeout and validation"""
        if not command or command not in ['up', 'down', 'morning', 'fastup', 'windows']:
            logger.warning(f"Invalid fleet command attempted: {command}")
            return {'success': False, 'error': 'Invalid command'}
        
        try:
            logger.info(f"Executing fleet command: {command} (timeout: 60s)")
            
            # Add environment variable to prevent GUI service interference
            env = os.environ.copy()
            env['NZ7DEV_GUI_PROTECTED'] = '1'  # Signal to script to protect GUI service
            
            result = subprocess.run(
                [self.config_manager.script_path, command],
                capture_output=True,
                text=True,
                timeout=60,  # Increased timeout for fleet operations
                env=env
            )
            
            if result.returncode == 0:
                logger.info(f"Fleet command '{command}' completed successfully")
                if result.stdout.strip():
                    logger.debug(f"Command output: {result.stdout.strip()[:500]}...")  # Limit log output
                
                # Invalidate status cache after successful fleet operation
                self._status_cache = None
                self._last_status_update = None
                logger.info("Fleet status cache invalidated after command execution")
                
            else:
                logger.error(f"Fleet command '{command}' failed with exit code {result.returncode}")
                if result.stderr.strip():
                    logger.error(f"Command error: {result.stderr.strip()[:500]}...")  # Limit error output
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None
            }
        except subprocess.TimeoutExpired:
            logger.error(f"Fleet command '{command}' timed out after 60 seconds")
            return {'success': False, 'error': 'Command timed out after 60 seconds'}
        except FileNotFoundError:
            logger.error(f"Fleet script not found: {self.config_manager.script_path}")
            return {'success': False, 'error': 'Script not found'}
        except Exception as e:
            logger.error(f"Fleet command '{command}' execution error: {e}")
            return {'success': False, 'error': str(e)}

    def validate_fleet_status(self) -> Dict[str, Any]:
        """Comprehensive fleet status validation and health check"""
        try:
            status = self.get_fleet_status()
            
            # Calculate health metrics
            total_vms = len(status)
            online_vms = sum(1 for vm_data in status.values() if vm_data.get('online', False))
            connected_vms = sum(1 for vm_data in status.values() if vm_data.get('rdp_connected', False))
            window_active_vms = sum(1 for vm_data in status.values() if vm_data.get('window_active', False))
            
            # Calculate percentages
            online_percentage = (online_vms / total_vms * 100) if total_vms > 0 else 0
            connectivity_percentage = (connected_vms / online_vms * 100) if online_vms > 0 else 0
            
            # Determine overall health status
            if online_percentage >= 80 and connectivity_percentage >= 70:
                health_status = "EXCELLENT"
                health_color = "#00ff88"
            elif online_percentage >= 60 and connectivity_percentage >= 50:
                health_status = "GOOD"
                health_color = "#00d4ff"
            elif online_percentage >= 40:
                health_status = "DEGRADED"
                health_color = "#ffb800"
            else:
                health_status = "CRITICAL"
                health_color = "#ff4757"
            
            # Identify problem VMs
            offline_vms = [vm_data['callsign'] for vm_data in status.values() if not vm_data.get('online', False)]
            disconnected_vms = [vm_data['callsign'] for vm_data in status.values() 
                              if vm_data.get('online', False) and not vm_data.get('rdp_connected', False)]
            
            return {
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'fleet_health': {
                    'overall_status': health_status,
                    'health_color': health_color,
                    'online_percentage': round(online_percentage, 1),
                    'connectivity_percentage': round(connectivity_percentage, 1)
                },
                'metrics': {
                    'total_vms': total_vms,
                    'online_vms': online_vms,
                    'connected_vms': connected_vms,
                    'window_active_vms': window_active_vms,
                    'offline_vms': len(offline_vms),
                    'disconnected_vms': len(disconnected_vms)
                },
                'issues': {
                    'offline_vms': offline_vms,
                    'disconnected_vms': disconnected_vms
                },
                'fleet_data': status
            }
            
        except Exception as e:
            logger.error(f"Fleet status validation failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

# Global optimized instance
mission_control = MissionControl()

# Input validation decorator
def validate_json(*required_fields):
    """Decorator for JSON input validation"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Invalid JSON'}), 400
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return jsonify({'error': f'Missing required fields: {missing_fields}'}), 400
            
            return f(data, *args, **kwargs)
        return decorated_function
    return decorator

# Optimized API Routes
@app.route('/')
def index():
    """Main dashboard with optimized template"""
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    """Get fleet status with caching headers"""
    status = mission_control.get_fleet_status()
    response = jsonify(status)
    response.headers['Cache-Control'] = 'public, max-age=3'  # Allow 3-second caching
    return response

@app.route('/api/rdp/spawn', methods=['POST'])
@validate_json('ip')
def api_spawn_rdp(data):
    """Spawn RDP connection with validation"""
    result = mission_control.rdp_manager.spawn_connection(data)
    return jsonify(result), 200 if result['success'] else 400

@app.route('/api/rdp/connections')
def api_get_connections():
    """Get active RDP connections"""
    connections = mission_control.rdp_manager.get_active_connections()
    return jsonify(connections)

@app.route('/api/rdp/connection/<connection_id>/kill', methods=['POST'])
def api_kill_connection(connection_id):
    """Kill specific RDP connection"""
    if not connection_id:
        abort(400)
    
    result = mission_control.rdp_manager.kill_connection(connection_id)
    return jsonify(result), 200 if result['success'] else 404

@app.route('/api/vm/<vm_name>/config', methods=['POST'])
@validate_json()
def api_update_vm_config(data, vm_name):
    """Update VM configuration"""
    success = mission_control.config_manager.update_vm_config(vm_name, data)
    if success:
        # Invalidate status cache
        mission_control._status_cache = None
        return jsonify({'success': True, 'message': 'Configuration updated'})
    else:
        return jsonify({'success': False, 'error': 'Failed to update configuration'}), 400

@app.route('/api/config')
def api_get_config():
    """Get current configuration"""
    config = {name: asdict(vm_config) for name, vm_config in mission_control.config_manager.fleet_config.items()}
    return jsonify(config)

@app.route('/api/fleet/<command>', methods=['POST'])
def api_fleet_command(command):
    """Execute fleet commands"""
    result = mission_control.execute_script_command(command)
    return jsonify(result), 200 if result['success'] else 400

@app.route('/api/fleet/validate')
def api_validate_fleet_status():
    """Validate fleet status"""
    result = mission_control.validate_fleet_status()
    return jsonify(result), 200 if result['status'] == 'success' else 500

# Optimized WebSocket handlers
@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('status_update', mission_control.get_fleet_status())

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('request_status')
def handle_request_status():
    """Handle status request"""
    emit('status_update', mission_control.get_fleet_status())

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Create required directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    # Start optimized monitoring
    mission_control.start_monitoring()
    
    print("🚀 NZ7DEV Mission Control GUI - OPTIMIZED EDITION")
    print("📡 Navigate to http://localhost:5000")
    print("🎯 High-performance mission control interface ready!")
    print("⚡ Features: Async operations, caching, connection pooling, batch processing")
    
    # Detect if running as a service
    is_service = (os.environ.get('INVOCATION_ID') is not None or 
                  os.environ.get('FLASK_ENV') == 'production' or
                  'systemd' in os.environ.get('_', ''))
    
    # Clear problematic Werkzeug environment variables
    for env_var in ['WERKZEUG_SERVER_FD', 'WERKZEUG_RUN_MAIN']:
        os.environ.pop(env_var, None)
    
    try:
        if is_service:
            # Production mode - use simpler approach
            logger.info("Starting in production service mode")
            from werkzeug.serving import run_simple
            
            # Use run_simple directly to avoid Flask's startup complexity
            run_simple(
                hostname='0.0.0.0',
                port=5000,
                application=app,
                threaded=True,
                use_reloader=False,
                use_debugger=False
            )
        else:
            # Development mode with SocketIO features
            logger.info("Starting in development mode")
            socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        mission_control.stop_monitoring() 