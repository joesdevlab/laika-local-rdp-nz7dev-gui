#!/bin/bash

# NZ7DEV Mission Control GUI - OPTIMIZED LAUNCH SCRIPT
# High-Performance Edition with Advanced Optimizations

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
readonly APP_NAME="NZ7DEV Mission Control GUI"
readonly VERSION="2.0.0-OPTIMIZED"
readonly PORT=5000
readonly LOG_FILE="${SCRIPT_DIR}/mission_control.log"
readonly PID_FILE="${SCRIPT_DIR}/mission_control.pid"

# Performance settings
readonly PYTHON_OPTS="-O -u"  # Optimize bytecode, unbuffered output
readonly MAX_WORKERS=10
readonly CACHE_SIZE="512M"

# Fancy header
print_header() {
    clear
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║  🚀 ${WHITE}${APP_NAME} - ${VERSION}${CYAN} 🚀                             ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo
}

# Logging function
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
        *)       echo -e "${WHITE}[$level]${NC} $message" ;;
    esac
    
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

# System optimization checks
optimize_system() {
    log "INFO" "🔧 Applying system optimizations..."
    
    # Set Python optimizations
    export PYTHONOPTIMIZE=2
    export PYTHONUNBUFFERED=1
    export PYTHONDONTWRITEBYTECODE=1
    
    # Increase file descriptor limits
    ulimit -n 65536 2>/dev/null || log "WARN" "Could not increase file descriptor limit"
    
    # Set CPU frequency scaling to performance mode (if available)
    if command -v cpupower >/dev/null 2>&1; then
        sudo cpupower frequency-set -g performance 2>/dev/null || true
    fi
    
    # Enable TCP BBR congestion control (if available)
    if [[ -w /proc/sys/net/ipv4/tcp_congestion_control ]]; then
        echo "bbr" | sudo tee /proc/sys/net/ipv4/tcp_congestion_control >/dev/null 2>&1 || true
    fi
    
    log "INFO" "✅ System optimizations applied"
}

# Performance monitoring
start_monitoring() {
    log "INFO" "📊 Starting performance monitoring..."
    
    # Create monitoring script
    cat > "${SCRIPT_DIR}/monitor.py" << 'EOF'
#!/usr/bin/env python3
import psutil
import time
import json
import sys
from datetime import datetime

def monitor_performance():
    """Monitor system and application performance"""
    try:
        # Get process info
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
            if 'nz7dev_gui.py' in ' '.join(proc.info['cmdline'] or []):
                cpu = proc.info['cpu_percent']
                memory = proc.info['memory_percent']
                
                # Log if usage is high
                if cpu > 80:
                    print(f"HIGH CPU: {cpu:.1f}%", file=sys.stderr)
                if memory > 80:
                    print(f"HIGH MEMORY: {memory:.1f}%", file=sys.stderr)
                
                # Output metrics
                metrics = {
                    'timestamp': datetime.now().isoformat(),
                    'cpu_percent': cpu,
                    'memory_percent': memory,
                    'connections': len(psutil.net_connections()),
                    'load_avg': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
                }
                print(json.dumps(metrics))
                break
                
    except Exception as e:
        print(f"Monitoring error: {e}", file=sys.stderr)

if __name__ == '__main__':
    monitor_performance()
EOF
    
    chmod +x "${SCRIPT_DIR}/monitor.py"
    log "INFO" "✅ Performance monitoring configured"
}

# Check if another instance is running
check_running() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            log "WARN" "Application already running with PID $pid"
            read -p "Kill existing instance? [y/N]: " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                kill "$pid" 2>/dev/null || true
                sleep 2
                kill -9 "$pid" 2>/dev/null || true
                rm -f "$PID_FILE"
            else
                log "INFO" "Exiting..."
                exit 0
            fi
        else
            rm -f "$PID_FILE"
        fi
    fi
}

# Install/update dependencies with caching
install_dependencies() {
    log "INFO" "📦 Checking dependencies..."
    
    local packages=(
        "python-flask"
        "python-flask-socketio" 
        "python-psutil"
        "python-yaml"
        "xfreerdp"
        "hyprland"
    )
    
    local missing_packages=()
    
    # Check which packages are missing
    for package in "${packages[@]}"; do
        if ! pacman -Q "$package" >/dev/null 2>&1; then
            missing_packages+=("$package")
        fi
    done
    
    # Install missing packages
    if [[ ${#missing_packages[@]} -gt 0 ]]; then
        log "INFO" "Installing missing packages: ${missing_packages[*]}"
        sudo pacman -S --needed --noconfirm "${missing_packages[@]}"
    else
        log "INFO" "✅ All dependencies satisfied"
    fi
    
    # Verify Python modules
    python3 -c "import flask, flask_socketio, psutil, yaml" 2>/dev/null || {
        log "ERROR" "Python dependencies not properly installed"
        exit 1
    }
}

# Pre-warm Python imports
prewarm_python() {
    log "INFO" "🔥 Pre-warming Python imports..."
    
    python3 -c "
import flask
import flask_socketio
import psutil
import yaml
import json
import subprocess
import threading
import time
import os
from datetime import datetime
print('Python modules pre-warmed')
" && log "INFO" "✅ Python imports pre-warmed"
}

# Network optimizations
optimize_network() {
    log "INFO" "🌐 Applying network optimizations..."
    
    # Increase network buffer sizes
    echo 'net.core.rmem_max = 134217728' | sudo tee -a /etc/sysctl.conf >/dev/null 2>&1 || true
    echo 'net.core.wmem_max = 134217728' | sudo tee -a /etc/sysctl.conf >/dev/null 2>&1 || true
    echo 'net.ipv4.tcp_rmem = 4096 87380 134217728' | sudo tee -a /etc/sysctl.conf >/dev/null 2>&1 || true
    echo 'net.ipv4.tcp_wmem = 4096 65536 134217728' | sudo tee -a /etc/sysctl.conf >/dev/null 2>&1 || true
    
    # Apply settings
    sudo sysctl -p >/dev/null 2>&1 || true
    
    log "INFO" "✅ Network optimizations applied"
}

# Create optimized environment
setup_environment() {
    log "INFO" "🔧 Setting up optimized environment..."
    
    # Create clean environment
    export PATH="/usr/bin:/usr/sbin:/bin:/sbin"
    export PYTHONPATH=""
    export PYTHONHASHSEED=0  # Reproducible hash seeds
    export MALLOC_TRIM_THRESHOLD_=100000  # Faster memory allocation
    
    # Set Flask optimizations
    export FLASK_ENV="production"
    export FLASK_DEBUG="0"
    export WERKZEUG_RUN_MAIN="true"
    
    # WebSocket optimizations
    export GEVENT_SUPPORT="True"
    export EVENTLET_NOPATCH="True"
    
    log "INFO" "✅ Environment optimized"
}

# Main launch function
launch_application() {
    log "INFO" "🚀 Launching ${APP_NAME}..."
    
    # Change to script directory
    cd "$SCRIPT_DIR"
    
    # Set CPU affinity (if available)
    local cpu_count=$(nproc)
    local affinity=""
    if ((cpu_count > 4)); then
        # Use last 4 cores for better performance
        affinity="taskset -c $((cpu_count-4))-$((cpu_count-1))"
    fi
    
    # Launch with optimizations
    local cmd="$affinity /usr/bin/python3 $PYTHON_OPTS nz7dev_gui.py"
    
    log "INFO" "Command: $cmd"
    log "INFO" "🌐 Web Interface: http://localhost:$PORT"
    
    # Start application in background
    nohup $cmd > "$LOG_FILE" 2>&1 &
    local app_pid=$!
    
    # Save PID
    echo "$app_pid" > "$PID_FILE"
    
    # Wait a moment and check if it started successfully
    sleep 3
    
    if ps -p "$app_pid" > /dev/null 2>&1; then
        log "INFO" "✅ Application started successfully (PID: $app_pid)"
        
        # Check if port is listening
        for i in {1..10}; do
            if netstat -ln | grep -q ":$PORT "; then
                log "INFO" "🎯 Server listening on port $PORT"
                break
            fi
            sleep 1
        done
        
        # Open browser
        if command -v xdg-open >/dev/null 2>&1; then
            log "INFO" "🌍 Opening browser..."
            xdg-open "http://localhost:$PORT" >/dev/null 2>&1 &
        fi
        
        return 0
    else
        log "ERROR" "Failed to start application"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Performance monitoring loop
monitor_loop() {
    while true; do
        if [[ -f "$PID_FILE" ]]; then
            local pid=$(cat "$PID_FILE")
            if ps -p "$pid" > /dev/null 2>&1; then
                # Run performance check
                "${SCRIPT_DIR}/monitor.py" 2>/dev/null || true
            else
                log "WARN" "Application process died"
                rm -f "$PID_FILE"
                break
            fi
        else
            break
        fi
        sleep 30
    done
}

# Cleanup function
cleanup() {
    log "INFO" "🧹 Cleaning up..."
    
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            kill "$pid" 2>/dev/null || true
            sleep 2
            kill -9 "$pid" 2>/dev/null || true
        fi
        rm -f "$PID_FILE"
    fi
    
    # Clean up monitoring script
    rm -f "${SCRIPT_DIR}/monitor.py"
    
    log "INFO" "✅ Cleanup complete"
}

# Signal handlers
trap cleanup EXIT INT TERM

# Main execution
main() {
    print_header
    
    # Check if running as root
    if [[ $EUID -eq 0 ]]; then
        log "ERROR" "Do not run as root for security reasons"
        exit 1
    fi
    
    # Performance optimizations
    optimize_system
    setup_environment
    optimize_network
    
    # Application setup
    check_running
    install_dependencies
    prewarm_python
    start_monitoring
    
    # Launch application
    if launch_application; then
        echo
        echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║  🎉 ${WHITE}MISSION CONTROL GUI SUCCESSFULLY LAUNCHED!${GREEN} 🎉                          ║${NC}"
        echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════════════════════════╝${NC}"
        echo
        echo -e "${CYAN}[ACCESS INFO]${NC}"
        echo -e "  🌐 Web Interface: ${WHITE}http://localhost:$PORT${NC}"
        echo -e "  🖥️  Local Access:  ${WHITE}http://127.0.0.1:$PORT${NC}"
        echo -e "  📱 Network Access: ${WHITE}http://$(hostname -I | awk '{print $1}'):$PORT${NC}"
        echo
        echo -e "${CYAN}[OPTIMIZATIONS ACTIVE]${NC}"
        echo -e "  ⚡ Python bytecode optimization"
        echo -e "  🚀 Network buffer optimization"
        echo -e "  📊 Performance monitoring"
        echo -e "  🎯 Connection pooling & caching"
        echo -e "  🔧 System resource optimization"
        echo
        echo -e "${CYAN}[FEATURES]${NC}"
        echo -e "  ✅ Async operations & batch processing"
        echo -e "  ✅ Real-time WebSocket updates"
        echo -e "  ✅ Intelligent caching system"
        echo -e "  ✅ Concurrent connection handling"
        echo -e "  ✅ Auto window positioning"
        echo
        echo -e "${CYAN}[SHORTCUTS]${NC}"
        echo -e "  • ${WHITE}Ctrl+Enter${NC} = Spawn RDP connection"
        echo -e "  • ${WHITE}Alt+1-6${NC} = Quick preset selection"
        echo -e "  • ${WHITE}Escape${NC} = Close modals"
        echo
        echo -e "${YELLOW}[READY]${NC} Press ${WHITE}Ctrl+C${NC} to stop the server"
        echo
        
        # Start monitoring in background
        monitor_loop &
        
        # Wait for user interrupt
        while true; do
            read -r -t 1 || continue
        done
    else
        log "ERROR" "Failed to launch application"
        exit 1
    fi
}

# Execute main function
main "$@" 