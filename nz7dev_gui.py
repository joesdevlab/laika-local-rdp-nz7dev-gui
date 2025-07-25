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
from colorama import Fore, Style

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
    """Optimized Hyprland window management with workspace resolution detection"""
    
    def __init__(self):
        self._clients_cache = None
        self._cache_time = None
        self._cache_duration = timedelta(seconds=2)  # Cache clients for 2 seconds
        self._monitors_cache = None
        self._monitors_cache_time = None
        self._monitors_cache_duration = timedelta(seconds=30)  # Cache monitors for 30 seconds
    
    @lru_cache(maxsize=16)
    def _get_cached_monitors(self, timestamp: float) -> str:
        """Cache hyprctl monitors output"""
        try:
            result = subprocess.run(
                ['hyprctl', 'monitors', '-j'],
                capture_output=True,
                text=True,
                timeout=3
            )
            return result.stdout if result.returncode == 0 else ""
        except subprocess.TimeoutExpired:
            logger.warning("hyprctl monitors timed out")
            return ""
    
    def get_monitors(self) -> List[Dict[str, Any]]:
        """Get Hyprland monitors with caching"""
        now = datetime.now()
        
        if (self._monitors_cache is None or 
            self._monitors_cache_time is None or 
            now - self._monitors_cache_time > self._monitors_cache_duration):
            
            timestamp = time.time()
            monitors_json = self._get_cached_monitors(timestamp)
            
            try:
                self._monitors_cache = json.loads(monitors_json) if monitors_json else []
                self._monitors_cache_time = now
            except json.JSONDecodeError:
                logger.error("Failed to parse hyprctl monitors JSON")
                self._monitors_cache = []
        
        return self._monitors_cache or []
    
    def get_workspace_resolution(self, workspace: int) -> Tuple[int, int]:
        """Get resolution for specific workspace with waybar compensation"""
        monitors = self.get_monitors()
        
        # Find monitor containing the workspace
        target_monitor = None
        for monitor in monitors:
            active_ws_id = monitor.get('activeWorkspace', {}).get('id', 0)
            if workspace == active_ws_id:
                target_monitor = monitor
                break
            
            # Check specialWorkspace for scratchpad workspaces
            special_ws = monitor.get('specialWorkspace', {})
            if special_ws and special_ws.get('id') == workspace:
                target_monitor = monitor
                break
        
        # If workspace not found on any monitor, use primary monitor
        if not target_monitor:
            target_monitor = next((m for m in monitors if m.get('focused', False)), 
                                 monitors[0] if monitors else None)
        
        if not target_monitor:
            logger.warning(f"No monitor found for workspace {workspace}, using default resolution")
            return (1920, 1040)  # Default with waybar compensation
        
        # Get monitor resolution
        width = target_monitor.get('width', 1920)
        height = target_monitor.get('height', 1080)
        
        # Subtract 40px for waybar at top
        effective_height = max(height - 40, 600)  # Ensure minimum height
        
        logger.info(f"Workspace {workspace} resolution: {width}x{effective_height} (monitor: {width}x{height} - 40px waybar)")
        return (width, effective_height)
    
    def get_all_workspace_resolutions(self) -> Dict[int, Tuple[int, int]]:
        """Get resolutions for all workspaces 1-10"""
        resolutions = {}
        monitors = self.get_monitors()
        
        if not monitors:
            # Fallback resolutions if no monitors detected
            default_res = (1920, 1040)
            return {i: default_res for i in range(1, 11)}
        
        # Map workspaces to monitors based on Hyprland configuration
        # This is a simplified mapping - in practice, workspace distribution 
        # depends on Hyprland config, but we'll use intelligent defaults
        
        total_monitors = len(monitors)
        workspaces_per_monitor = 10 // total_monitors if total_monitors > 0 else 10
        
        for workspace in range(1, 11):
            # Determine which monitor this workspace would typically be on
            monitor_index = min((workspace - 1) // workspaces_per_monitor, total_monitors - 1)
            monitor = monitors[monitor_index] if monitor_index < len(monitors) else monitors[0]
            
            width = monitor.get('width', 1920)
            height = monitor.get('height', 1080)
            effective_height = max(height - 40, 600)  # Waybar compensation
            
            resolutions[workspace] = (width, effective_height)
        
        return resolutions
    
    def get_optimal_geometry_for_workspace(self, workspace: int, position: str = 'center') -> str:
        """Get optimal geometry string for workspace with position consideration"""
        width, height = self.get_workspace_resolution(workspace)
        
        # Adjust size based on position for better window management
        if position == 'left' or position == 'right':
            # For side positions, use approximately half width
            width = int(width * 0.48)  # Leave some margin
        elif position == 'center':
            # For center, use most of the screen but leave margins
            width = int(width * 0.9)
            height = int(height * 0.9)
        
        return f"{width}x{height}"

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
        """Position window with improved commands and timing"""
        try:
            width, height = map(int, geometry.split('x'))
            
            # Wait for window to be ready
            max_retries = 10
            for attempt in range(max_retries):
                if self.check_window_exists(window_title):
                    break
                time.sleep(0.5)
            else:
                logger.warning(f"Window {window_title} not found after {max_retries} attempts")
                return False
            
            # Calculate position based on workspace resolution
            try:
                ws_width, ws_height = self.get_workspace_resolution(workspace)
                
                if position == 'center':
                    x = max(0, (ws_width - width) // 2)
                    y = max(40, (ws_height - height) // 2 + 40)  # Account for waybar
                elif position == 'left':
                    x = 50
                    y = 90  # Below waybar with margin
                elif position == 'right':
                    x = max(50, ws_width - width - 50)
                    y = 90
                else:
                    x, y = 100, 100  # Default fallback
                    
                logger.info(f"Calculated position for {window_title}: {x},{y} (workspace {workspace}, {position})")
                
            except Exception as e:
                logger.warning(f"Failed to calculate optimal position: {e}, using defaults")
                x, y = 100, 100
            
            # Execute positioning commands individually with delays for reliability
            commands = [
                f'movetoworkspacesilent {workspace},title:"{window_title}"',
                f'resizewindowpixel exact {width} {height},title:"{window_title}"',
                f'movewindowpixel exact {x} {y},title:"{window_title}"'
            ]
            
            success = True
            for i, cmd in enumerate(commands):
                try:
                    result = subprocess.run(['hyprctl', 'dispatch'] + cmd.split(' ', 1), 
                                          capture_output=True, timeout=3)
                    if result.returncode != 0:
                        logger.warning(f"Positioning command {i+1} failed for {window_title}: {result.stderr.decode()}")
                        success = False
                    else:
                        logger.debug(f"Positioning step {i+1}/3 successful for {window_title}")
                    
                    # Small delay between commands for reliability
                    if i < len(commands) - 1:
                        time.sleep(0.3)
                        
                except subprocess.TimeoutExpired:
                    logger.warning(f"Positioning command {i+1} timed out for {window_title}")
                    success = False
                except Exception as e:
                    logger.error(f"Error in positioning command {i+1} for {window_title}: {e}")
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to position window {window_title}: {e}")
            return False

    def get_workspace_state(self) -> Dict[str, Any]:
        """Get current state of all workspaces including VM assignments"""
        try:
            clients = self.get_clients()
            workspaces_info = self.get_workspaces_info()
            monitors = self.get_monitors()
            
            workspace_state = {
                'workspaces': {},
                'scratchpad': {
                    'windows': [],
                    'visible': False
                },
                'monitors': []
            }
            
            # Process monitors
            for monitor in monitors:
                workspace_state['monitors'].append({
                    'name': monitor.get('name', 'Unknown'),
                    'width': monitor.get('width', 1920),
                    'height': monitor.get('height', 1080),
                    'scale': monitor.get('scale', 1.0),
                    'focused': monitor.get('focused', False),
                    'active_workspace': monitor.get('activeWorkspace', {}).get('id', 1)
                })
            
            # Initialize workspaces 1-10
            for ws_id in range(1, 11):
                workspace_state['workspaces'][str(ws_id)] = {
                    'id': ws_id,
                    'windows': [],
                    'active': False,
                    'resolution': self.get_workspace_resolution(ws_id)
                }
            
            # Process clients and assign to workspaces
            for client in clients:
                title = client.get('title', '')
                workspace_info = client.get('workspace', {})
                workspace_name = workspace_info.get('name', '')
                workspace_id = workspace_info.get('id', 0)
                
                # Extract VM info from RDP window titles
                vm_info = None
                if title.startswith('FreeRDP: '):
                    ip_address = title.replace('FreeRDP: ', '')
                    vm_info = {
                        'ip': ip_address,
                        'type': 'rdp',
                        'title': title,
                        'position': {
                            'x': client.get('at', [0, 0])[0],
                            'y': client.get('at', [0, 0])[1] if len(client.get('at', [])) > 1 else 0
                        },
                        'size': {
                            'width': client.get('size', [0, 0])[0],
                            'height': client.get('size', [0, 0])[1] if len(client.get('size', [])) > 1 else 0
                        },
                        'floating': client.get('floating', False),
                        'fullscreen': client.get('fullscreen', False)
                    }
                
                # Assign to workspace or scratchpad
                if workspace_name == 'special':
                    workspace_state['scratchpad']['windows'].append({
                        'title': title,
                        'vm_info': vm_info,
                        'client_data': client
                    })
                elif workspace_id > 0 and workspace_id <= 10:
                    workspace_state['workspaces'][str(workspace_id)]['windows'].append({
                        'title': title,
                        'vm_info': vm_info,
                        'client_data': client
                    })
            
            # Check if scratchpad is visible
            for workspace in workspaces_info:
                if workspace.get('name') == 'special':
                    workspace_state['scratchpad']['visible'] = True
                    break
            
            # Mark active workspace
            active_workspace = self.get_active_workspace()
            if active_workspace and str(active_workspace) in workspace_state['workspaces']:
                workspace_state['workspaces'][str(active_workspace)]['active'] = True
            
            return workspace_state
            
        except Exception as e:
            logger.error(f"Failed to get workspace state: {e}")
            return {
                'workspaces': {},
                'scratchpad': {'windows': [], 'visible': False},
                'monitors': []
            }
    
    def get_workspaces_info(self) -> List[Dict[str, Any]]:
        """Get information about all workspaces"""
        try:
            result = subprocess.run(
                ['hyprctl', 'workspaces', '-j'],
                capture_output=True,
                text=True,
                timeout=3
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
            return []
        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
            logger.warning(f"Failed to get workspaces info: {e}")
            return []
    
    def get_active_workspace(self) -> int:
        """Get currently active workspace ID"""
        try:
            result = subprocess.run(
                ['hyprctl', 'activeworkspace', '-j'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return data.get('id', 1)
            return 1
        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
            logger.warning(f"Failed to get active workspace: {e}")
            return 1
    
    def assign_to_scratchpad(self, window_title: str, size_preset: str, position: str, geometry: str) -> bool:
        """Assign window to scratchpad with specific size and position"""
        try:
            width, height = map(int, geometry.split('x'))
            
            # Wait for window to be ready
            max_retries = 5
            for attempt in range(max_retries):
                if self.check_window_exists(window_title):
                    break
                time.sleep(0.3)
            else:
                logger.warning(f"Window {window_title} not found for scratchpad assignment")
                return False
            
            # Commands for scratchpad assignment
            commands = [
                f'movetoworkspacesilent special,title:"{window_title}"',
                f'resizewindowpixel exact {width} {height},title:"{window_title}"'
            ]
            
            # Calculate position for scratchpad based on preset and position
            if size_preset == 'quarter':
                # Quarter windows get specific grid positions
                positions = {
                    'center': (960, 540),
                    'left': (480, 540), 
                    'right': (1440, 540),
                    'top-left': (480, 270),
                    'top-right': (1440, 270),
                    'bottom-left': (480, 810),
                    'bottom-right': (1440, 810)
                }
                x, y = positions.get(position, positions['center'])
            elif size_preset.startswith('half'):
                # Half windows
                if size_preset == 'half-left':
                    x, y = (width // 4, 70)
                elif size_preset == 'half-right':
                    x, y = (1920 - width // 4 - width, 70)
                else:
                    x, y = ((1920 - width) // 2, 70)
            else:
                # Full or other sizes - center them
                x, y = ((1920 - width) // 2, (1080 - height) // 2)
            
            commands.append(f'movewindowpixel exact {x} {y},title:"{window_title}"')
            
            # Execute commands
            success = True
            for i, cmd in enumerate(commands):
                try:
                    result = subprocess.run(['hyprctl', 'dispatch'] + cmd.split(' ', 1), 
                                          capture_output=True, timeout=3)
                    if result.returncode != 0:
                        logger.warning(f"Scratchpad command {i+1} failed for {window_title}: {result.stderr.decode()}")
                        success = False
                    
                    # Small delay between commands
                    if i < len(commands) - 1:
                        time.sleep(0.2)
                        
                except subprocess.TimeoutExpired:
                    logger.warning(f"Scratchpad command {i+1} timed out for {window_title}")
                    success = False
                except Exception as e:
                    logger.error(f"Error in scratchpad command {i+1} for {window_title}: {e}")
                    success = False
            
            logger.info(f"Assigned {window_title} to scratchpad with {size_preset} size at position {x},{y}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to assign {window_title} to scratchpad: {e}")
            return False
    
    def invalidate_workspace_cache(self):
        """Invalidate workspace-related caches"""
        self._clients_cache = None
        self._cache_time = None
        self._monitors_cache = None
        self._monitors_cache_time = None
        # Clear LRU caches
        self._get_cached_clients.cache_clear()
        self._get_cached_monitors.cache_clear()

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
        """Spawn RDP connection with optimization and workspace-aware geometry"""
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
            
            # Auto-detect workspace geometry if requested
            if geometry.startswith('auto'):
                try:
                    # Handle auto-ws# format (e.g., "auto-ws4")
                    if geometry.startswith('auto-ws'):
                        # Extract workspace number from geometry string
                        ws_match = geometry.replace('auto-ws', '')
                        if ws_match.isdigit():
                            detected_workspace = int(ws_match)
                            auto_geometry = self.hyprland.get_optimal_geometry_for_workspace(detected_workspace, position)
                            logger.info(f"Auto-detected geometry for workspace {detected_workspace}: {auto_geometry} (requested: {geometry})")
                            geometry = auto_geometry
                        else:
                            # Fallback to current workspace
                            auto_geometry = self.hyprland.get_optimal_geometry_for_workspace(workspace, position)
                            logger.info(f"Auto-detected geometry for workspace {workspace}: {auto_geometry}")
                            geometry = auto_geometry
                    else:
                        # Handle generic "auto" - use current workspace
                        auto_geometry = self.hyprland.get_optimal_geometry_for_workspace(workspace, position)
                        logger.info(f"Auto-detected geometry for workspace {workspace}: {auto_geometry}")
                        geometry = auto_geometry
                        
                except Exception as e:
                    logger.warning(f"Failed to auto-detect geometry, using default: {e}")
                    geometry = '1920x1080'
            
            logger.info(f"Spawning RDP connection to {ip} ({geometry}, workspace {workspace}) with user {username}")
            
            # Build optimized FreeRDP command for version 2.11.7
            cmd = [
                'xfreerdp',
                f'/v:{ip}',
                f'/u:{username}',
                f'/p:{password}',
                '/cert:ignore',        # Fixed from /cert-ignore
                '+compression',        # Fixed from /compression  
                '+gfx-progressive',    # Fixed from /gfx:progressive
                f'/timeout:{10000}',   # Connection timeout
                '/log-level:WARN',     # Reduce log verbosity but capture errors
            ]
            
            # Add geometry or fullscreen - fixed for FreeRDP 2.11.7
            if fullscreen:
                cmd.append('/f')
            else:
                # Parse geometry and use /w: and /h: parameters
                try:
                    width, height = geometry.split('x')
                    cmd.extend([f'/w:{width}', f'/h:{height}'])
                except ValueError:
                    # Fallback if geometry parsing fails
                    cmd.extend(['/w:1920', '/h:1080'])
            
            # Add optional features
            if params.get('drive_redirection', False):
                cmd.append('/drive:home,/home')
            
            if params.get('clipboard', True):
                cmd.append('+clipboard')
            
            if params.get('sound', False):
                cmd.append('/sound:sys:pulse')
            
            # Start connection with better error handling and X11 environment
            try:
                # Prepare environment with X11 display access
                rdp_env = os.environ.copy()
                rdp_env['DISPLAY'] = ':1'  # Ensure correct display is used
                if 'XAUTHORITY' not in rdp_env:
                    rdp_env['XAUTHORITY'] = f'/home/{os.getenv("USER", "nz7")}/.Xauthority'
                rdp_env['XDG_RUNTIME_DIR'] = f'/run/user/{os.getuid()}'
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=rdp_env,  # Pass environment with correct DISPLAY
                    preexec_fn=os.setsid  # Create new process group for better cleanup
                )
                logger.info(f"RDP process started for {ip} (PID: {process.pid}) with DISPLAY={rdp_env.get('DISPLAY')}")
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
                    # Wait briefly for connection to establish or fail - increased timeout
                    time.sleep(3)  # Increased from 2 to 3 seconds
                    poll_result = process.poll()
                    
                    if poll_result is not None:
                        # Process has exited, get detailed error information
                        try:
                            stdout, stderr = process.communicate(timeout=10)  # Increased timeout
                            stdout_str = stdout.decode('utf-8', errors='ignore') if stdout else ""
                            stderr_str = stderr.decode('utf-8', errors='ignore') if stderr else ""
                            
                            logger.info(f"RDP process for {ip} exited with code {poll_result}")
                            if stdout_str.strip():
                                logger.info(f"RDP stdout for {ip}: {stdout_str.strip()[:500]}")
                            if stderr_str.strip():
                                logger.info(f"RDP stderr for {ip}: {stderr_str.strip()[:500]}")
                            
                            if poll_result != 0:
                                # Connection failed - parse detailed error
                                error_msg = "Connection failed"
                                if stderr_str:
                                    if 'LOGON_FAILURE' in stderr_str or 'Authentication failed' in stderr_str:
                                        error_msg = f"Authentication failed - check username/password for {ip}"
                                    elif 'CONNECTION_REFUSED' in stderr_str or 'Connection refused' in stderr_str:
                                        error_msg = f"Connection refused by {ip} - RDP service may not be running"
                                    elif 'NETWORK_ERROR' in stderr_str or 'Network' in stderr_str:
                                        error_msg = f"Network error connecting to {ip}"
                                    elif 'CONNECT_CANCELLED' in stderr_str:
                                        error_msg = f"Connection cancelled - may be due to certificate or policy issues on {ip}"
                                    elif 'timeout' in stderr_str.lower():
                                        error_msg = f"Connection timeout to {ip}"
                                    else:
                                        # Include more of the error for debugging
                                        error_msg = f"RDP connection to {ip} failed: {stderr_str.strip()[:300]}"
                                
                                logger.error(f"RDP connection to {ip} failed: {error_msg}")
                            else:
                                logger.info(f"RDP connection to {ip} established successfully")
                        except subprocess.TimeoutExpired:
                            logger.warning(f"Timeout getting process output for {ip}")
                            logger.error(f"RDP connection to {ip} failed: Process communication timeout")
                    else:
                        # Process is still running - this is good!
                        logger.info(f"RDP connection to {ip} is running successfully")
                    
                    # Position window if process is still running
                    if process.poll() is None:
                        time.sleep(2)  # Wait for window to appear
                        window_title = f"FreeRDP: {ip}"
                        success = self.hyprland.position_window(window_title, workspace, position, geometry)
                        if success:
                            logger.info(f"Window positioned successfully for {ip}")
                        else:
                            # Try alternate window title formats
                            alternate_titles = [
                                f"{ip} - FreeRDP",
                                f"RDP - {ip}",
                                f"FreeRDP ({ip})",
                                f"192.168.1.{ip.split('.')[-1]} - FreeRDP"  # Try last octet format
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
        valid_commands = ['up', 'down', 'morning', 'fastup', 'windows', 'scratchpad']
        if not command or command not in valid_commands:
            logger.warning(f"Invalid fleet command attempted: {command}")
            return {'success': False, 'error': 'Invalid command'}
        
        try:
            logger.info(f"Executing fleet command: {command} (timeout: 60s)")
            
            # Add environment variable to prevent GUI service interference
            env = os.environ.copy()
            env['NZ7DEV_GUI_PROTECTED'] = '1'  # Signal to script to protect GUI service
            
            # Handle scratchpad command specially
            if command == 'scratchpad':
                script_path = './nz7dev_scratchpad_launcher.sh'
                cmd = [script_path, 'launch']
            else:
                script_path = self.config_manager.script_path
                cmd = [script_path, command]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=90,  # Increased timeout for scratchpad operations
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
            logger.error(f"Fleet command '{command}' timed out after 90 seconds")
            return {'success': False, 'error': 'Command timed out after 90 seconds'}
        except FileNotFoundError:
            logger.error(f"Script not found: {script_path if command != 'scratchpad' else './nz7dev_scratchpad_launcher.sh'}")
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

@app.route('/api/rdp/connection/ip/<ip>/kill', methods=['POST'])
def api_kill_connection_by_ip(ip):
    """Kill RDP connection by IP address"""
    if not ip:
        abort(400)
    
    # Find connection by IP
    connections = mission_control.rdp_manager.get_active_connections()
    connection_id = None
    
    for conn_id, conn_info in connections.items():
        if conn_info['ip'] == ip:
            connection_id = conn_id
            break
    
    if not connection_id:
        return jsonify({'success': False, 'error': f'No active connection found for {ip}'}), 404
    
    result = mission_control.rdp_manager.kill_connection(connection_id)
    return jsonify(result), 200 if result['success'] else 500

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

@app.route('/api/fleet/status')
def api_get_fleet_status():
    """Get fleet status for Available VMs display"""
    try:
        fleet_data = mission_control.get_fleet_status()
        
        # Transform data to match expected format for Available VMs
        fleet_list = []
        for vm_name, vm_info in fleet_data.items():
            fleet_list.append({
                'name': vm_name,
                'callsign': vm_info['callsign'],
                'ip': vm_info['ip'],
                'status': 'ONLINE' if vm_info['online'] else 'OFFLINE',
                'connected': vm_info.get('rdp_connected', False),
                'geometry': vm_info['geometry'],
                'workspace': vm_info['workspace'],
                'position': vm_info['position'],
                'enabled': vm_info['enabled']
            })
        
        return jsonify({
            'success': True,
            'fleet': fleet_list
        })
    except Exception as e:
        logger.error(f"Failed to get fleet status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/workspace/resolutions')
def api_workspace_resolutions():
    """Get workspace resolutions for auto-geometry detection"""
    try:
        workspace_resolutions = mission_control.hyprland_manager.get_all_workspace_resolutions()
        
        formatted_resolutions = {}
        for workspace, (width, height) in workspace_resolutions.items():
            formatted_resolutions[f'workspace_{workspace}'] = {
                'width': width,
                'height': height,
                'display_name': f'Auto-detect (WS{workspace}: {width}×{height})'
            }
        
        return jsonify({
            'success': True,
            'workspaces': formatted_resolutions,
            'default_geometry': '1920x1080'
        })
    except Exception as e:
        logger.error(f"Failed to get workspace resolutions: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'fallback_resolution': '1920x1040'
        }), 500

@app.route('/api/workspaces/test')
def workspace_test():
    """Simple test for workspace API"""
    return jsonify({'status': 'workspace API working', 'success': True})

@app.route('/api/workspaces/state')
def get_workspace_state():
    """Get current workspace state including VM assignments and layout"""
    try:
        workspace_state = mission_control.hyprland_manager.get_workspace_state()
        return jsonify({
            'success': True,
            'workspaces': workspace_state
        })
    except Exception as e:
        logger.error(f"Failed to get workspace state: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/workspaces/assign', methods=['POST'])
@validate_json('vm_ip', 'workspace', 'size_preset')
def assign_vm_to_workspace(data):
    """Assign VM to specific workspace with size and position presets"""
    try:
        vm_ip = data['vm_ip']
        workspace = data['workspace']
        size_preset = data['size_preset']  # 'full', 'half-left', 'half-right', 'quarter', 'custom'
        position = data.get('position', 'center')
        custom_geometry = data.get('custom_geometry', None)
        use_scratchpad = data.get('use_scratchpad', False)
        
        # Validate workspace
        if not use_scratchpad and (workspace < 1 or workspace > 10):
            return jsonify({
                'success': False,
                'error': 'Workspace must be between 1 and 10'
            }), 400
            
        # Calculate geometry based on preset
        geometry = calculate_geometry_from_preset(workspace, size_preset, custom_geometry)
        
        # Find window title
        window_title = f"FreeRDP: {vm_ip}"
        
        # Check if window exists
        if not mission_control.hyprland_manager.check_window_exists(window_title):
            return jsonify({
                'success': False,
                'error': f'VM window {vm_ip} not found. Please ensure the RDP session is active.'
            }), 404
        
        # Assign to workspace or scratchpad
        if use_scratchpad:
            success = mission_control.hyprland_manager.assign_to_scratchpad(window_title, size_preset, position, geometry)
        else:
            success = mission_control.hyprland_manager.position_window(window_title, workspace, position, geometry)
        
        if success:
            # Update workspace state cache
            mission_control.hyprland_manager.invalidate_workspace_cache()
            
            return jsonify({
                'success': True,
                'message': f'VM {vm_ip} assigned to {"scratchpad" if use_scratchpad else f"workspace {workspace}"} with {size_preset} size'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to assign VM to workspace'
            }), 500
            
    except Exception as e:
        logger.error(f"Failed to assign VM to workspace: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/workspaces/batch-assign', methods=['POST'])
@validate_json('assignments')
def batch_assign_vms(data):
    """Batch assign multiple VMs to workspaces"""
    try:
        assignments = data['assignments']
        results = []
        
        for assignment in assignments:
            vm_ip = assignment['vm_ip']
            workspace = assignment.get('workspace', 1)
            size_preset = assignment.get('size_preset', 'full')
            position = assignment.get('position', 'center')
            use_scratchpad = assignment.get('use_scratchpad', False)
            custom_geometry = assignment.get('custom_geometry', None)
            
            try:
                geometry = calculate_geometry_from_preset(workspace, size_preset, custom_geometry)
                window_title = f"FreeRDP: {vm_ip}"
                
                if mission_control.hyprland_manager.check_window_exists(window_title):
                    if use_scratchpad:
                        success = mission_control.hyprland_manager.assign_to_scratchpad(window_title, size_preset, position, geometry)
                    else:
                        success = mission_control.hyprland_manager.position_window(window_title, workspace, position, geometry)
                    
                    results.append({
                        'vm_ip': vm_ip,
                        'success': success,
                        'target': 'scratchpad' if use_scratchpad else f'workspace {workspace}'
                    })
                else:
                    results.append({
                        'vm_ip': vm_ip,
                        'success': False,
                        'error': 'Window not found'
                    })
                    
                # Small delay between assignments for stability
                time.sleep(0.2)
                
            except Exception as e:
                results.append({
                    'vm_ip': vm_ip,
                    'success': False,
                    'error': str(e)
                })
        
        # Invalidate cache after batch operations
        mission_control.hyprland_manager.invalidate_workspace_cache()
        
        successful = sum(1 for r in results if r['success'])
        total = len(results)
        
        return jsonify({
            'success': True,
            'results': results,
            'summary': f'{successful}/{total} VMs assigned successfully'
        })
        
    except Exception as e:
        logger.error(f"Failed to batch assign VMs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def calculate_geometry_from_preset(workspace: int, size_preset: str, custom_geometry: str = None) -> str:
    """Calculate window geometry based on size preset and workspace"""
    try:
        ws_width, ws_height = mission_control.hyprland_manager.get_workspace_resolution(workspace)
        
        # Define size presets
        presets = {
            'full': (int(ws_width * 0.95), int(ws_height * 0.95)),
            'half-left': (int(ws_width * 0.48), int(ws_height * 0.95)),
            'half-right': (int(ws_width * 0.48), int(ws_height * 0.95)),
            'half-top': (int(ws_width * 0.95), int(ws_height * 0.47)),
            'half-bottom': (int(ws_width * 0.95), int(ws_height * 0.47)),
            'quarter': (int(ws_width * 0.48), int(ws_height * 0.47)),
            'third': (int(ws_width * 0.31), int(ws_height * 0.95)),
            'two-thirds': (int(ws_width * 0.63), int(ws_height * 0.95)),
        }
        
        if size_preset == 'custom' and custom_geometry:
            # Parse custom geometry (e.g., "1920x1080")
            try:
                width, height = map(int, custom_geometry.split('x'))
                return f"{width}x{height}"
            except (ValueError, IndexError):
                logger.warning(f"Invalid custom geometry: {custom_geometry}, using full preset")
                size_preset = 'full'
        
        if size_preset in presets:
            width, height = presets[size_preset]
            return f"{width}x{height}"
        else:
            logger.warning(f"Unknown size preset: {size_preset}, using full")
            width, height = presets['full']
            return f"{width}x{height}"
            
    except Exception as e:
        logger.error(f"Failed to calculate geometry for preset {size_preset}: {e}")
        return "1920x1080"  # Fallback

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
    
    print(f'\n🚀 {Fore.GREEN}NZ7DEV Mission Control GUI{Style.RESET_ALL} starting...')
    print(f'📡 Navigate to {Fore.CYAN}http://localhost:5000{Style.RESET_ALL}')
    print(f'🎯 Mission Control interface ready!\n')
    print("⚡ Features: Visual workspace manager, drag-and-drop VM placement, size presets")
    
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        mission_control.stop_monitoring() 