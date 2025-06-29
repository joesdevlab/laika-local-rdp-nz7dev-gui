#!/usr/bin/env python3
"""
NZ7DEV Mission Control GUI
A modern web-based interface for managing RDP connections and window positioning
"""

import os
import json
import subprocess
import threading
import time
import yaml
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import psutil

app = Flask(__name__)
app.config['SECRET_KEY'] = 'nz7dev-mission-control-2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration
SCRIPT_PATH = './nz7dev'
CONFIG_DIR = os.path.expanduser('~/.nz7dev/config')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'mission.yaml')

# VM Fleet Configuration
FLEET_CONFIG = {
    'vm20': {
        'callsign': 'ALPHA',
        'ip': '192.168.1.20',
        'credentials': 'nz7dev:lemonlime',
        'geometry': '957x1042',
        'workspace': 4,
        'position': 'left',
        'scratchpad': False,
        'enabled': True
    },
    'vm21': {
        'callsign': 'BRAVO', 
        'ip': '192.168.1.21',
        'credentials': 'nz7dev:lemonlime',
        'geometry': '1717x1402',
        'workspace': 2,
        'position': 'left',
        'scratchpad': True,
        'enabled': True
    },
    'vm23': {
        'callsign': 'CHARLIE',
        'ip': '192.168.1.23',
        'credentials': 'User:lemonlime',
        'geometry': '1915x1042',
        'workspace': 1,
        'position': 'center',
        'scratchpad': False,
        'enabled': True
    },
    'vm24': {
        'callsign': 'DELTA',
        'ip': '192.168.1.24',
        'credentials': 'nz7dev:lemonlime',
        'geometry': '957x1042',
        'workspace': 4,
        'position': 'right',
        'scratchpad': False,
        'enabled': True
    },
    'vm25': {
        'callsign': 'ECHO',
        'ip': '192.168.1.25',
        'credentials': 'User:lemonlime',
        'geometry': '1717x1402',
        'workspace': 2,
        'position': 'right',
        'scratchpad': True,
        'enabled': True
    },
    'vm26': {
        'callsign': 'FOXTROT',
        'ip': '192.168.1.26',
        'credentials': 'User:lemonlime',
        'geometry': '1915x1042',
        'workspace': 3,
        'position': 'center',
        'scratchpad': False,
        'enabled': True
    }
}

class MissionControl:
    def __init__(self):
        self.status_thread = None
        self.running = False
        
    def start_monitoring(self):
        """Start background monitoring thread"""
        if not self.running:
            self.running = True
            self.status_thread = threading.Thread(target=self._monitor_status)
            self.status_thread.daemon = True
            self.status_thread.start()
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.running = False
        
    def _monitor_status(self):
        """Background thread to monitor system status"""
        while self.running:
            try:
                status = self.get_fleet_status()
                socketio.emit('status_update', status)
                time.sleep(5)  # Update every 5 seconds
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(10)
    
    def ping_target(self, ip, timeout=2):
        """Test connectivity to target"""
        try:
            result = subprocess.run(
                ['ping', '-c', '1', '-W', str(timeout), ip],
                capture_output=True, 
                text=True,
                timeout=timeout + 1
            )
            return result.returncode == 0
        except:
            return False
    
    def check_rdp_service(self, vm_name):
        """Check if RDP service is running for VM"""
        try:
            service_name = f"nz7dev-{vm_name}.service"
            result = subprocess.run(
                ['systemctl', '--user', 'is-active', service_name],
                capture_output=True,
                text=True
            )
            return result.stdout.strip() == 'active'
        except:
            return False
    
    def check_window_status(self, ip):
        """Check if RDP window exists"""
        try:
            window_title = f"FreeRDP: {ip}"
            result = subprocess.run(
                ['hyprctl', 'clients'],
                capture_output=True,
                text=True
            )
            return window_title in result.stdout
        except:
            return False
    
    def get_fleet_status(self):
        """Get comprehensive status of all fleet members"""
        status = {}
        
        for vm_name, config in FLEET_CONFIG.items():
            ip = config['ip']
            
            vm_status = {
                'name': vm_name,
                'callsign': config['callsign'],
                'ip': ip,
                'geometry': config['geometry'],
                'workspace': config['workspace'],
                'position': config['position'],
                'scratchpad': config['scratchpad'],
                'enabled': config['enabled'],
                'online': self.ping_target(ip),
                'rdp_connected': self.check_rdp_service(vm_name),
                'window_active': self.check_window_status(ip),
                'last_updated': datetime.now().isoformat()
            }
            
            status[vm_name] = vm_status
            
        return status
    
    def start_rdp_connection(self, vm_name):
        """Start RDP connection for specific VM"""
        if vm_name not in FLEET_CONFIG:
            return {'success': False, 'error': 'VM not found'}
        
        config = FLEET_CONFIG[vm_name]
        if not config['enabled']:
            return {'success': False, 'error': 'VM disabled'}
        
        try:
            # Use the establish_rdp_connection function from the script
            result = subprocess.run([
                SCRIPT_PATH,
                'connect',  # We'll need to add this command to the script
                vm_name
            ], capture_output=True, text=True)
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def stop_rdp_connection(self, vm_name):
        """Stop RDP connection for specific VM"""
        try:
            service_name = f"nz7dev-{vm_name}.service"
            result = subprocess.run([
                'systemctl', '--user', 'stop', service_name
            ], capture_output=True, text=True)
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def update_vm_config(self, vm_name, updates):
        """Update VM configuration"""
        if vm_name not in FLEET_CONFIG:
            return {'success': False, 'error': 'VM not found'}
        
        # Update in-memory config
        for key, value in updates.items():
            if key in FLEET_CONFIG[vm_name]:
                FLEET_CONFIG[vm_name][key] = value
        
        # Save to YAML config file
        self.save_config()
        
        return {'success': True, 'config': FLEET_CONFIG[vm_name]}
    
    def save_config(self):
        """Save current configuration to YAML file"""
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            
            # Convert our config to the format expected by the bash script
            yaml_config = {
                'mission_control': {
                    'callsign': 'HOUSTON',
                    'commander': 'auto',
                    'log_level': 'INFO'
                },
                'development_fleet': {}
            }
            
            for vm_name, config in FLEET_CONFIG.items():
                yaml_config['development_fleet'][vm_name] = {
                    'callsign': config['callsign'],
                    'ip_address': config['ip'],
                    'connection_type': 'rdp',
                    'credentials': config['credentials'],
                    'display_geometry': config['geometry'],
                    'workspace': config['workspace'],
                    'position': config['position'],
                    'scratchpad': config['scratchpad'],
                    'auto_connect': config['enabled']
                }
            
            with open(CONFIG_FILE, 'w') as f:
                yaml.dump(yaml_config, f, default_flow_style=False)
                
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def execute_script_command(self, command):
        """Execute nz7dev script command"""
        try:
            result = subprocess.run([SCRIPT_PATH, command], 
                                  capture_output=True, text=True)
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

# Global mission control instance
mission_control = MissionControl()

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    """Get current fleet status"""
    return jsonify(mission_control.get_fleet_status())

@app.route('/api/vm/<vm_name>/start', methods=['POST'])
def api_start_vm(vm_name):
    """Start RDP connection for VM"""
    result = mission_control.start_rdp_connection(vm_name)
    return jsonify(result)

@app.route('/api/vm/<vm_name>/stop', methods=['POST'])
def api_stop_vm(vm_name):
    """Stop RDP connection for VM"""
    result = mission_control.stop_rdp_connection(vm_name)
    return jsonify(result)

@app.route('/api/vm/<vm_name>/config', methods=['POST'])
def api_update_vm_config(vm_name):
    """Update VM configuration"""
    updates = request.json
    result = mission_control.update_vm_config(vm_name, updates)
    return jsonify(result)

@app.route('/api/fleet/start', methods=['POST'])
def api_start_fleet():
    """Start entire fleet"""
    result = mission_control.execute_script_command('up')
    return jsonify(result)

@app.route('/api/fleet/stop', methods=['POST'])
def api_stop_fleet():
    """Stop entire fleet"""
    result = mission_control.execute_script_command('down')
    return jsonify(result)

@app.route('/api/fleet/morning', methods=['POST'])
def api_morning_routine():
    """Execute morning routine"""
    result = mission_control.execute_script_command('morning')
    return jsonify(result)

@app.route('/api/fleet/fastup', methods=['POST'])
def api_fastup():
    """Execute LUDICROUS SPEED launch"""
    result = mission_control.execute_script_command('fastup')
    return jsonify(result)

@app.route('/api/windows/position', methods=['POST'])
def api_position_windows():
    """Position all windows"""
    result = mission_control.execute_script_command('windows')
    return jsonify(result)

@app.route('/api/config')
def api_get_config():
    """Get current configuration"""
    return jsonify(FLEET_CONFIG)

@app.route('/api/config', methods=['POST'])
def api_save_config():
    """Save configuration"""
    success = mission_control.save_config()
    return jsonify({'success': success})

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print('Client connected')
    # Send initial status
    emit('status_update', mission_control.get_fleet_status())

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print('Client disconnected')

@socketio.on('request_status')
def handle_request_status():
    """Handle status request"""
    emit('status_update', mission_control.get_fleet_status())

if __name__ == '__main__':
    # Start background monitoring
    mission_control.start_monitoring()
    
    # Create templates directory
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    print("🚀 NZ7DEV Mission Control GUI starting...")
    print("📡 Navigate to http://localhost:5000")
    print("🎯 Mission Control interface ready!")
    
    # Check if running as a systemd service
    is_service = os.environ.get('INVOCATION_ID') is not None
    debug_mode = not is_service  # Disable debug mode when running as service
    
    try:
        if is_service:
            # Running as service - allow unsafe werkzeug for development server
            socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
        else:
            # Running manually - use debug mode
            socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    finally:
        mission_control.stop_monitoring() 