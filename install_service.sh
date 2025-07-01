#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════════
# 🚀 NZ7DEV MISSION CONTROL GUI SERVICE INSTALLER - PROFESSIONAL EDITION
# ═══════════════════════════════════════════════════════════════════════════════════
# Install and manage the GUI as a systemd user service
# Enhanced for Visual Workspace Manager and Professional Features
# ═══════════════════════════════════════════════════════════════════════════════════

set -euo pipefail

# Colors for output
readonly MC_BLUE='\033[0;34m'
readonly MC_GREEN='\033[0;32m'
readonly MC_YELLOW='\033[1;33m'
readonly MC_RED='\033[0;31m'
readonly MC_WHITE='\033[1;37m'
readonly MC_CYAN='\033[0;36m'
readonly MC_PURPLE='\033[0;35m'
readonly MC_NC='\033[0m'

readonly SERVICE_NAME="nz7dev-gui"
readonly SERVICE_FILE="${SERVICE_NAME}.service"
readonly USER_SERVICE_DIR="$HOME/.config/systemd/user"
readonly CURRENT_DIR="$(pwd)"
readonly VERSION="2.0.0-PROFESSIONAL"

# Mission Control Professional Banner
echo -e "${MC_BLUE}"
cat << 'EOF'
╔═══════════════════════════════════════════════════════════════════════════════════╗
║  🚀 NZ7DEV MISSION CONTROL - PROFESSIONAL EDITION SERVICE INSTALLER 🚀           ║
║                                                                                   ║
║  ⚡ Visual Workspace Manager                                                      ║
║  🎯 Advanced RDP Management                                                       ║
║  📊 Real-time Performance Monitoring                                             ║
║  🖥️  Hyprland Integration                                                         ║
║                                                                                   ║
║  Version 2.0.0 - Production-Ready Professional Edition                           ║
╚═══════════════════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${MC_NC}"

show_help() {
    echo -e "${MC_WHITE}USAGE:${MC_NC}"
    echo "  $0 install     - Install and start the professional service"
    echo "  $0 upgrade     - Upgrade existing service to professional edition"
    echo "  $0 start       - Start the service"
    echo "  $0 stop        - Stop the service"
    echo "  $0 restart     - Restart the service"
    echo "  $0 status      - Show detailed service status"
    echo "  $0 logs        - Show service logs"
    echo "  $0 logs-live   - Follow service logs in real-time"
    echo "  $0 enable      - Enable auto-start on login"
    echo "  $0 disable     - Disable auto-start"
    echo "  $0 uninstall   - Remove the service completely"
    echo "  $0 url         - Show GUI access URLs"
    echo "  $0 health      - Perform health check"
    echo "  $0 monitor     - Real-time performance monitoring"
    echo ""
    echo -e "${MC_YELLOW}PROFESSIONAL FEATURES:${MC_NC}"
    echo "  • Visual Workspace Manager with drag-and-drop VM placement"
    echo "  • Advanced size presets (full, half, quarter, third, custom)"
    echo "  • Scratchpad integration with Hyprland"
    echo "  • Real-time workspace state monitoring"
    echo "  • Enhanced RDP connection management"
    echo "  • Performance optimizations and caching"
    echo "  • Professional UI with modern design system"
    echo ""
    echo -e "${MC_CYAN}EXAMPLES:${NC}"
    echo "  $0 install     # Fresh install with all optimizations"
    echo "  $0 upgrade     # Upgrade from basic to professional edition"
    echo "  $0 monitor     # Monitor performance metrics"
    echo "  $0 logs-live   # Watch logs in real-time"
}

check_dependencies() {
    echo -e "${MC_WHITE}[DEPS]${MC_NC} Checking professional edition dependencies..."
    
    local missing_deps=()
    local deps=(
        "systemctl:systemd"
        "python3:python"
        "hyprctl:hyprland"
        "xfreerdp:freerdp"
        "lsof:lsof"
    )
    
    for dep in "${deps[@]}"; do
        local cmd="${dep%:*}"
        local pkg="${dep#*:}"
        
        if ! command -v "$cmd" >/dev/null 2>&1; then
            missing_deps+=("$pkg")
            echo -e "${MC_RED}  ✗${MC_NC} Missing: $cmd ($pkg)"
        else
            echo -e "${MC_GREEN}  ✓${MC_NC} Found: $cmd"
        fi
    done
    
    # Check Python modules
    echo -e "${MC_WHITE}[PYTHON]${MC_NC} Checking Python dependencies..."
    local python_modules=("flask" "flask_socketio" "psutil" "yaml")
    
    for module in "${python_modules[@]}"; do
        if python3 -c "import $module" 2>/dev/null; then
            echo -e "${MC_GREEN}  ✓${MC_NC} Python module: $module"
        else
            echo -e "${MC_RED}  ✗${MC_NC} Missing Python module: $module"
            missing_deps+=("python-$module")
        fi
    done
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        echo -e "${MC_YELLOW}[INSTALL]${MC_NC} Installing missing dependencies..."
        echo "  Packages: ${missing_deps[*]}"
        
        # Try to install via pacman (Arch Linux)
        if command -v pacman >/dev/null 2>&1; then
            sudo pacman -S --needed --noconfirm "${missing_deps[@]}" || {
                echo -e "${MC_RED}[ERROR]${MC_NC} Failed to install some dependencies"
                echo -e "${MC_YELLOW}[MANUAL]${MC_NC} Please install manually:"
                printf "  sudo pacman -S %s\n" "${missing_deps[@]}"
                return 1
            }
        else
            echo -e "${MC_RED}[ERROR]${MC_NC} Automatic dependency installation not available"
            echo -e "${MC_YELLOW}[MANUAL]${MC_NC} Please install these packages manually:"
            printf "  %s\n" "${missing_deps[@]}"
            return 1
        fi
    fi
    
    echo -e "${MC_GREEN}[SUCCESS]${MC_NC} All dependencies satisfied"
    return 0
}

install_service() {
    echo -e "${MC_WHITE}[INSTALL]${MC_NC} Installing NZ7DEV Mission Control Professional Edition..."
    
    # Check dependencies first
    check_dependencies || return 1
    
    # Verify required files
    local required_files=("$SERVICE_FILE" "nz7dev_gui.py" "templates/index.html" "static/css/styles.css")
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            echo -e "${MC_RED}[ERROR]${MC_NC} Required file not found: $file"
            echo -e "${MC_YELLOW}[INFO]${MC_NC} Please ensure all professional edition files are present"
            return 1
        fi
    done
    
    # Create systemd user directory
    mkdir -p "$USER_SERVICE_DIR"
    
    # Create logs directory
    mkdir -p "${CURRENT_DIR}/logs"
    
    # Update service file with current directory
    echo -e "${MC_BLUE}[CONFIG]${MC_NC} Configuring service for current directory..."
    if [[ -f "$SERVICE_FILE" ]]; then
        # Replace paths in service file
        sed "s|WorkingDirectory=.*|WorkingDirectory=$CURRENT_DIR|g" "$SERVICE_FILE" > "$USER_SERVICE_DIR/$SERVICE_FILE"
        sed -i "s|cd /mnt/WD/dev/laika-local-rdp-nz7dev-gui|cd $CURRENT_DIR|g" "$USER_SERVICE_DIR/$SERVICE_FILE"
        sed -i "s|Environment=PYTHONPATH=.*|Environment=PYTHONPATH=$CURRENT_DIR|g" "$USER_SERVICE_DIR/$SERVICE_FILE"
        sed -i "s|/mnt/WD/dev/laika-local-rdp-nz7dev-gui/|$CURRENT_DIR/|g" "$USER_SERVICE_DIR/$SERVICE_FILE"
        
        # Update user-specific paths
        local current_user=$(whoami)
        local current_uid=$(id -u)
        sed -i "s|User=nz7|User=$current_user|g" "$USER_SERVICE_DIR/$SERVICE_FILE"
        sed -i "s|Group=nz7|Group=$current_user|g" "$USER_SERVICE_DIR/$SERVICE_FILE"
        sed -i "s|/home/nz7|$HOME|g" "$USER_SERVICE_DIR/$SERVICE_FILE"
        sed -i "s|/run/user/1000|/run/user/$current_uid|g" "$USER_SERVICE_DIR/$SERVICE_FILE"
        
        echo -e "${MC_GREEN}  ✓${MC_NC} Service file configured for $current_user"
    else
        echo -e "${MC_RED}[ERROR]${MC_NC} Service file $SERVICE_FILE not found!"
        return 1
    fi
    
    # Set proper permissions
    chmod +x nz7dev *.sh 2>/dev/null || true
    
    # Reload systemd
    echo -e "${MC_BLUE}[SYSTEMD]${MC_NC} Reloading systemd daemon..."
    systemctl --user daemon-reload
    
    # Enable and start service
    echo -e "${MC_BLUE}[START]${MC_NC} Enabling and starting service..."
    systemctl --user enable "$SERVICE_NAME"
    systemctl --user start "$SERVICE_NAME"
    
    echo -e "${MC_GREEN}[SUCCESS]${MC_NC} Professional Edition service installed and started!"
    sleep 3
    show_status
    show_url
    show_features
}

upgrade_service() {
    echo -e "${MC_WHITE}[UPGRADE]${MC_NC} Upgrading to Professional Edition..."
    
    # Stop existing service
    systemctl --user stop "$SERVICE_NAME" 2>/dev/null || true
    
    # Install new version
    install_service
    
    echo -e "${MC_GREEN}[UPGRADED]${MC_NC} Successfully upgraded to Professional Edition!"
}

start_service() {
    echo -e "${MC_WHITE}[START]${MC_NC} Starting NZ7DEV Mission Control Professional Edition..."
    systemctl --user start "$SERVICE_NAME"
    echo -e "${MC_GREEN}[SUCCESS]${MC_NC} Professional Edition started!"
    sleep 2
    show_status
}

stop_service() {
    echo -e "${MC_WHITE}[STOP]${MC_NC} Stopping NZ7DEV Mission Control..."
    systemctl --user stop "$SERVICE_NAME"
    echo -e "${MC_GREEN}[SUCCESS]${MC_NC} Service stopped!"
}

restart_service() {
    echo -e "${MC_WHITE}[RESTART]${MC_NC} Restarting NZ7DEV Mission Control Professional Edition..."
    systemctl --user restart "$SERVICE_NAME"
    echo -e "${MC_GREEN}[SUCCESS]${MC_NC} Professional Edition restarted!"
    sleep 2
    show_status
}

show_status() {
    echo -e "${MC_WHITE}[STATUS]${MC_NC} Professional Edition service status:"
    echo
    systemctl --user --no-pager status "$SERVICE_NAME" || true
    echo
    
    # Additional status information
    if systemctl --user is-active "$SERVICE_NAME" >/dev/null 2>&1; then
        echo -e "${MC_GREEN}[RUNNING]${MC_NC} Service is active and running"
        
        # Check if port is accessible
        if curl -s "http://localhost:5000" >/dev/null 2>&1; then
            echo -e "${MC_GREEN}[NETWORK]${MC_NC} Web interface is accessible"
        else
            echo -e "${MC_YELLOW}[NETWORK]${MC_NC} Web interface not yet ready (starting up...)"
        fi
        
        # Show memory usage
        local memory_usage=$(systemctl --user show "$SERVICE_NAME" --property=MemoryCurrent --value 2>/dev/null || echo "0")
        if [[ "$memory_usage" != "0" ]] && [[ "$memory_usage" != "[not set]" ]]; then
            local memory_mb=$((memory_usage / 1024 / 1024))
            echo -e "${MC_CYAN}[MEMORY]${MC_NC} Current usage: ${memory_mb}MB"
        fi
    else
        echo -e "${MC_RED}[STOPPED]${MC_NC} Service is not running"
    fi
}

show_logs() {
    echo -e "${MC_WHITE}[LOGS]${MC_NC} Service logs (last 50 lines):"
    echo
    journalctl --user -u "$SERVICE_NAME" --no-pager -n 50
}

show_logs_live() {
    echo -e "${MC_WHITE}[LOGS]${MC_NC} Following service logs in real-time (Ctrl+C to exit):"
    echo
    journalctl --user -u "$SERVICE_NAME" -f --no-pager
}

enable_service() {
    echo -e "${MC_WHITE}[ENABLE]${MC_NC} Enabling auto-start on login..."
    systemctl --user enable "$SERVICE_NAME"
    
    # Enable lingering so service starts without login
    sudo loginctl enable-linger "$USER" 2>/dev/null || {
        echo -e "${MC_YELLOW}[WARN]${MC_NC} Could not enable lingering (service will start only after login)"
    }
    
    echo -e "${MC_GREEN}[SUCCESS]${MC_NC} Professional Edition will auto-start on login!"
}

disable_service() {
    echo -e "${MC_WHITE}[DISABLE]${MC_NC} Disabling auto-start..."
    systemctl --user disable "$SERVICE_NAME"
    echo -e "${MC_GREEN}[SUCCESS]${MC_NC} Auto-start disabled!"
}

uninstall_service() {
    echo -e "${MC_YELLOW}[UNINSTALL]${MC_NC} Removing NZ7DEV Mission Control service..."
    
    # Stop and disable service
    systemctl --user stop "$SERVICE_NAME" 2>/dev/null || true
    systemctl --user disable "$SERVICE_NAME" 2>/dev/null || true
    
    # Remove service file
    rm -f "$USER_SERVICE_DIR/$SERVICE_FILE"
    
    # Reload systemd
    systemctl --user daemon-reload
    systemctl --user reset-failed
    
    echo -e "${MC_GREEN}[SUCCESS]${MC_NC} Professional Edition service uninstalled!"
}

show_url() {
    local ip_address
    ip_address=$(ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+' 2>/dev/null || echo "localhost")
    
    echo -e "${MC_WHITE}[ACCESS]${MC_NC} Professional Edition GUI is available at:"
    echo -e "  🌐 Local:      ${MC_BLUE}http://localhost:5000${MC_NC}"
    echo -e "  🖥️  Loopback:   ${MC_BLUE}http://127.0.0.1:5000${MC_NC}"
    if [[ "$ip_address" != "localhost" ]]; then
        echo -e "  📱 Network:    ${MC_BLUE}http://$ip_address:5000${MC_NC}"
    fi
    echo
}

show_features() {
    echo -e "${MC_PURPLE}[FEATURES]${MC_NC} Professional Edition capabilities:"
    echo -e "  🎯 Visual Workspace Manager - Drag & drop VM placement"
    echo -e "  📐 Advanced Size Presets - Full, half, quarter, third, custom"
    echo -e "  🗂️  Scratchpad Integration - Floating window management"
    echo -e "  📊 Real-time Monitoring - Live workspace state updates"
    echo -e "  ⚡ Performance Optimized - Caching & concurrent operations"
    echo -e "  🎨 Modern UI Design - Professional dark theme"
    echo -e "  ⌨️  Keyboard Shortcuts - Ctrl+Enter, Alt+1-6"
    echo -e "  🔄 Auto-positioning - Smart window placement"
    echo
}

health_check() {
    echo -e "${MC_WHITE}[HEALTH]${MC_NC} Performing Professional Edition health check..."
    echo
    
    local issues=0
    
    # Check service status
    if systemctl --user is-active "$SERVICE_NAME" >/dev/null 2>&1; then
        echo -e "${MC_GREEN}  ✓${MC_NC} Service is running"
    else
        echo -e "${MC_RED}  ✗${MC_NC} Service is not running"
        ((issues++))
    fi
    
    # Check web interface
    if curl -s "http://localhost:5000" >/dev/null 2>&1; then
        echo -e "${MC_GREEN}  ✓${MC_NC} Web interface is accessible"
    else
        echo -e "${MC_RED}  ✗${MC_NC} Web interface is not accessible"
        ((issues++))
    fi
    
    # Check Hyprland integration
    if command -v hyprctl >/dev/null 2>&1 && hyprctl workspaces >/dev/null 2>&1; then
        echo -e "${MC_GREEN}  ✓${MC_NC} Hyprland integration working"
    else
        echo -e "${MC_YELLOW}  ⚠${MC_NC} Hyprland not accessible (workspace manager may not work)"
        ((issues++))
    fi
    
    # Check FreeRDP
    if command -v xfreerdp >/dev/null 2>&1; then
        echo -e "${MC_GREEN}  ✓${MC_NC} FreeRDP is available"
    else
        echo -e "${MC_RED}  ✗${MC_NC} FreeRDP not found"
        ((issues++))
    fi
    
    # Check log file
    if [[ -f "${CURRENT_DIR}/mission_control.log" ]]; then
        local log_size=$(stat -c%s "${CURRENT_DIR}/mission_control.log" 2>/dev/null || echo 0)
        local log_mb=$((log_size / 1024 / 1024))
        echo -e "${MC_GREEN}  ✓${MC_NC} Log file exists (${log_mb}MB)"
    else
        echo -e "${MC_YELLOW}  ⚠${MC_NC} Log file not found"
    fi
    
    echo
    if [[ $issues -eq 0 ]]; then
        echo -e "${MC_GREEN}[HEALTHY]${MC_NC} All systems operational!"
    else
        echo -e "${MC_YELLOW}[ISSUES]${MC_NC} Found $issues potential issues"
    fi
}

monitor_performance() {
    echo -e "${MC_WHITE}[MONITOR]${MC_NC} Real-time performance monitoring (Ctrl+C to exit):"
    echo -e "${MC_CYAN}Time     CPU%   Memory%  Connections  Load${MC_NC}"
    echo "================================================"
    
    while true; do
        if systemctl --user is-active "$SERVICE_NAME" >/dev/null 2>&1; then
            local timestamp=$(date '+%H:%M:%S')
            
            # Get process info
            local pid=$(systemctl --user show "$SERVICE_NAME" --property=MainPID --value 2>/dev/null)
            if [[ "$pid" != "0" ]] && [[ -n "$pid" ]]; then
                local cpu_usage=$(ps -p "$pid" -o %cpu --no-headers 2>/dev/null | xargs)
                local mem_usage=$(ps -p "$pid" -o %mem --no-headers 2>/dev/null | xargs)
                local connections=$(ss -t state established | wc -l)
                local load_avg=$(cut -d' ' -f1 /proc/loadavg)
                
                printf "%-8s %-6s %-8s %-11s %-4s\n" "$timestamp" "$cpu_usage%" "$mem_usage%" "$connections" "$load_avg"
            else
                echo -e "${MC_RED}$timestamp SERVICE NOT RUNNING${MC_NC}"
            fi
        else
            echo -e "${MC_RED}$(date '+%H:%M:%S') SERVICE STOPPED${MC_NC}"
        fi
        
        sleep 2
    done
}

# Main execution
case "${1:-help}" in
    "install")
        install_service
        ;;
    "upgrade")
        upgrade_service
        ;;
    "start")
        start_service
        ;;
    "stop")
        stop_service
        ;;
    "restart")
        restart_service
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs
        ;;
    "logs-live")
        show_logs_live
        ;;
    "enable")
        enable_service
        ;;
    "disable")
        disable_service
        ;;
    "uninstall")
        uninstall_service
        ;;
    "url")
        show_url
        ;;
    "health")
        health_check
        ;;
    "monitor")
        monitor_performance
        ;;
    "help"|*)
        show_help
        ;;
esac

exit 0 