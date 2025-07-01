#!/bin/bash

# NZ7DEV Mission Control GUI - PROFESSIONAL EDITION OPTIMIZED LAUNCHER
# High-Performance Edition with Advanced Optimizations and Visual Workspace Manager

set -euo pipefail

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly WHITE='\033[1;37m'
readonly NC='\033[0m' # No Color

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly APP_NAME="NZ7DEV Mission Control GUI Professional Edition"
readonly VERSION="2.0.0-PROFESSIONAL-OPTIMIZED"
readonly PORT=5000
readonly LOG_FILE="${SCRIPT_DIR}/mission_control.log"
readonly PID_FILE="${SCRIPT_DIR}/mission_control.pid"

# Performance settings for professional edition
readonly PYTHON_OPTS="-O -u"  # Optimize bytecode, unbuffered output
readonly MAX_WORKERS=20
readonly CACHE_SIZE="1024M"
readonly PYTHON_CMD="/usr/bin/python3"

# Professional header
print_header() {
    clear
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║  🚀 ${WHITE}${APP_NAME} - ${VERSION}${CYAN} 🚀     ║${NC}"
    echo -e "${CYAN}║                                                                                   ║${NC}"
    echo -e "${CYAN}║  ⚡ Visual Workspace Manager  🎯 Advanced RDP Management                         ║${NC}"
    echo -e "${CYAN}║  📊 Real-time Monitoring     🖥️  Hyprland Integration                            ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo
}

# Enhanced logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case "$level" in
        "INFO")  echo -e "${GREEN}[INFO]${NC} $message" ;;
        "WARN")  echo -e "${YELLOW}[WARN]${NC} $message" ;;
        "ERROR") echo -e "${RED}[ERROR]${NC} $message" ;;
        "DEBUG") echo -e "${PURPLE}[DEBUG]${NC} $message" ;;
        "SUCCESS") echo -e "${GREEN}[SUCCESS]${NC} $message" ;;
        *)       echo -e "${WHITE}[$level]${NC} $message" ;;
    esac
    
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

# Professional system optimization
optimize_system() {
    log "INFO" "🔧 Applying professional edition optimizations..."
    
    # Enhanced Python optimizations
    export PYTHONOPTIMIZE=2
    export PYTHONUNBUFFERED=1
    export PYTHONDONTWRITEBYTECODE=1
    export PYTHONHASHSEED=0
    
    # Professional Flask settings
    export FLASK_ENV=production
    export FLASK_DEBUG=0
    export SECRET_KEY="nz7dev-mission-control-pro-2024-visual-workspace-manager"
    
    # Memory and performance settings
    export MALLOC_ARENA_MAX=4
    export MALLOC_MMAP_THRESHOLD_=131072
    export MALLOC_TRIM_THRESHOLD_=131072
    
    # Display environment for workspace manager
    export DISPLAY="${DISPLAY:-:1}"
    export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-1}"
    export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
    
    # Increase file descriptor limits for high-performance
    ulimit -n 65536 2>/dev/null || log "WARN" "Could not increase file descriptor limit"
    
    # Set high priority if possible
    renice -n -10 $$ 2>/dev/null || log "DEBUG" "Could not set higher priority"
    
    log "SUCCESS" "Professional optimizations applied"
}

# Enhanced dependency check for professional edition
check_professional_dependencies() {
    log "INFO" "📦 Checking professional edition dependencies..."
    
    local missing_packages=()
    local system_packages=(
        "python3:Python 3 interpreter"
        "hyprctl:Hyprland window manager"
        "xfreerdp:FreeRDP client"
        "lsof:Network monitoring"
    )
    
    # Check system dependencies
    for package_info in "${system_packages[@]}"; do
        local cmd="${package_info%:*}"
        local desc="${package_info#*:}"
        
        if command -v "$cmd" >/dev/null 2>&1; then
            log "INFO" "✓ $cmd - $desc"
        else
            log "WARN" "✗ $cmd - $desc (may limit functionality)"
            [[ "$cmd" == "python3" ]] && missing_packages+=("python")
            [[ "$cmd" == "hyprctl" ]] && missing_packages+=("hyprland")
            [[ "$cmd" == "xfreerdp" ]] && missing_packages+=("freerdp")
            [[ "$cmd" == "lsof" ]] && missing_packages+=("lsof")
        fi
    done
    
    # Check Python modules for professional edition
    local python_modules=(
        "flask:Flask web framework"
        "flask_socketio:Real-time communication"
        "psutil:System monitoring"
        "yaml:Configuration parsing"
        "threading:Concurrent operations"
        "dataclasses:Professional data structures"
        "functools:Performance optimizations"
        "concurrent.futures:Advanced concurrency"
    )
    
    local missing_python=()
    for module_info in "${python_modules[@]}"; do
        local module="${module_info%:*}"
        local desc="${module_info#*:}"
        
        if $PYTHON_CMD -c "import $module" 2>/dev/null; then
            log "DEBUG" "✓ $module - $desc"
        else
            log "ERROR" "✗ $module - $desc"
            [[ "$module" == "flask" ]] && missing_python+=("python-flask")
            [[ "$module" == "flask_socketio" ]] && missing_python+=("python-flask-socketio") 
            [[ "$module" == "psutil" ]] && missing_python+=("python-psutil")
            [[ "$module" == "yaml" ]] && missing_python+=("python-yaml")
        fi
    done
    
    # Auto-install missing packages for Arch Linux
    if [[ ${#missing_python[@]} -gt 0 ]] && command -v pacman >/dev/null 2>&1; then
        log "INFO" "Installing missing Python packages via pacman..."
        sudo pacman -S --needed --noconfirm "${missing_python[@]}" || {
            log "WARN" "Pacman install failed, trying pip fallback..."
            $PYTHON_CMD -m pip install --break-system-packages flask flask-socketio psutil pyyaml eventlet
        }
    fi
    
    # Final verification
    if $PYTHON_CMD -c "import flask, flask_socketio, psutil, yaml" 2>/dev/null; then
        log "SUCCESS" "All professional edition dependencies satisfied"
        return 0
    else
        log "ERROR" "Critical dependencies missing for professional edition"
        return 1
    fi
}

# Check if another instance is running
check_running() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            log "WARN" "Professional edition already running with PID $pid"
            read -p "Kill existing instance? [y/N]: " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                kill "$pid" 2>/dev/null || true
                sleep 3
                kill -9 "$pid" 2>/dev/null || true
                rm -f "$PID_FILE"
                log "INFO" "Existing instance terminated"
            else
                log "INFO" "Exiting..."
                exit 0
            fi
        else
            rm -f "$PID_FILE"
        fi
    fi
}

# Enhanced cleanup with professional features
cleanup_environment() {
    log "INFO" "🧹 Cleaning up environment for professional launch..."
    
    # Kill any existing GUI processes
    pkill -f "nz7dev_gui.py" 2>/dev/null || true
    
    # Clean up port 5000
    lsof -ti:5000 | xargs -r kill -9 2>/dev/null || true
    
    # Remove stale PID files
    rm -f "$PID_FILE" 2>/dev/null || true
    
    # Create required directories
    mkdir -p logs static/css static/js templates
    
    # Set proper permissions
    chmod +x nz7dev *.sh 2>/dev/null || true
    
    log "SUCCESS" "Environment cleaned and ready"
}

# Professional performance monitoring
start_monitoring() {
    log "INFO" "📊 Starting professional performance monitoring..."
    
    # Create enhanced monitoring script
    cat > "${SCRIPT_DIR}/monitor_pro.py" << 'EOF'
#!/usr/bin/env python3
import psutil
import time
import json
import sys
import threading
from datetime import datetime

class ProfessionalMonitor:
    def __init__(self):
        self.metrics = {
            'cpu_percent': 0,
            'memory_percent': 0,
            'connections': 0,
            'threads': 0,
            'load_avg': 0,
            'startup_time': datetime.now().isoformat()
        }
    
    def monitor_performance(self):
        """Enhanced performance monitoring for professional edition"""
        try:
            # Find mission control process
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent', 'num_threads']):
                if 'nz7dev_gui.py' in ' '.join(proc.info['cmdline'] or []):
                    self.metrics.update({
                        'cpu_percent': proc.info['cpu_percent'],
                        'memory_percent': proc.info['memory_percent'],
                        'threads': proc.info['num_threads'],
                        'connections': len(psutil.net_connections()),
                        'load_avg': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Professional alerting
                    if self.metrics['cpu_percent'] > 85:
                        print(f"HIGH CPU: {self.metrics['cpu_percent']:.1f}%", file=sys.stderr)
                    if self.metrics['memory_percent'] > 85:
                        print(f"HIGH MEMORY: {self.metrics['memory_percent']:.1f}%", file=sys.stderr)
                    
                    print(json.dumps(self.metrics))
                    break
                    
        except Exception as e:
            print(f"Professional monitoring error: {e}", file=sys.stderr)

if __name__ == '__main__':
    monitor = ProfessionalMonitor()
    monitor.monitor_performance()
EOF
    
    chmod +x "${SCRIPT_DIR}/monitor_pro.py"
    log "SUCCESS" "Professional monitoring configured"
}

# Pre-warm Python for faster startup
prewarm_python() {
    log "INFO" "🔥 Pre-warming Python for professional edition..."
    
    $PYTHON_CMD -c "
import flask
import flask_socketio
import psutil
import yaml
import threading
import json
import time
import subprocess
import concurrent.futures
from datetime import datetime
from dataclasses import dataclass
from functools import lru_cache
print('Professional edition modules pre-loaded successfully')
" 2>/dev/null || log "WARN" "Pre-warming failed, continuing anyway"
    
    log "SUCCESS" "Python environment ready"
}

# Professional startup sequence
professional_startup() {
    print_header
    
    log "INFO" "Starting professional edition startup sequence..."
    
    # Change to script directory
    cd "$SCRIPT_DIR"
    
    # Check for existing instances
    check_running
    
    # Clean environment
    cleanup_environment
    
    # Check dependencies
    check_professional_dependencies || exit 1
    
    # Apply optimizations
    optimize_system
    
    # Start monitoring
    start_monitoring
    
    # Pre-warm Python
    prewarm_python
    
    # Display access information
    echo
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  🚀 MISSION CONTROL PROFESSIONAL EDITION READY FOR LAUNCH 🚀                     ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo
    
    local ip_address
    ip_address=$(ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+' 2>/dev/null || echo "localhost")
    
    echo -e "${WHITE}[ACCESS URLS]${NC}"
    echo -e "  🌐 Local:      ${BLUE}http://localhost:5000${NC}"
    echo -e "  🖥️  Loopback:   ${BLUE}http://127.0.0.1:5000${NC}"
    if [[ "$ip_address" != "localhost" ]]; then
        echo -e "  📱 Network:    ${BLUE}http://$ip_address:5000${NC}"
    fi
    echo
    
    echo -e "${PURPLE}[PROFESSIONAL FEATURES]${NC}"
    echo -e "  🎯 Visual Workspace Manager - Drag & drop VM placement"
    echo -e "  📐 Advanced Size Presets - Full, half, quarter, third, custom"
    echo -e "  🗂️  Scratchpad Integration - Floating window management" 
    echo -e "  📊 Real-time Monitoring - Live performance metrics"
    echo -e "  ⚡ Performance Optimized - Enhanced caching & concurrency"
    echo -e "  🎨 Professional UI - Modern dark theme with animations"
    echo
    
    echo -e "${CYAN}[HYPRLAND STATUS]${NC}"
    if command -v hyprctl >/dev/null 2>&1; then
        echo -e "  ✅ Hyprland detected - Full workspace management enabled"
        local workspaces=$(hyprctl workspaces -j 2>/dev/null | jq length 2>/dev/null || echo "N/A")
        echo -e "  🖥️  Active workspaces: $workspaces"
    else
        echo -e "  ⚠️  Hyprland not detected - Limited workspace features"
    fi
    
    echo
    echo -e "${YELLOW}[READY]${NC} Press Ctrl+C to stop the professional server"
    echo -e "${GREEN}[LAUNCH]${NC} Starting Mission Control Professional Edition..."
    echo
}

# Main execution
main() {
    # Run professional startup
    professional_startup
    
    # Store PID
    echo $$ > "$PID_FILE"
    
    # Launch with full optimizations
    exec $PYTHON_CMD $PYTHON_OPTS nz7dev_gui.py 2>&1 | tee -a "$LOG_FILE"
}

# Cleanup on exit
cleanup() {
    rm -f "$PID_FILE" 2>/dev/null || true
    log "INFO" "Professional edition shutdown complete"
}

trap cleanup EXIT

# Execute main function
main "$@" 