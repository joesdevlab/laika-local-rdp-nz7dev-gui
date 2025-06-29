#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════════
# 🚀 NZ7DEV MISSION CONTROL GUI SERVICE INSTALLER
# ═══════════════════════════════════════════════════════════════════════════════════
# Install and manage the GUI as a systemd user service
# ═══════════════════════════════════════════════════════════════════════════════════

set -euo pipefail

# Colors for output
readonly MC_BLUE='\033[0;34m'
readonly MC_GREEN='\033[0;32m'
readonly MC_YELLOW='\033[1;33m'
readonly MC_RED='\033[0;31m'
readonly MC_WHITE='\033[1;37m'
readonly MC_NC='\033[0m'

readonly SERVICE_NAME="nz7dev-gui"
readonly SERVICE_FILE="${SERVICE_NAME}.service"
readonly USER_SERVICE_DIR="$HOME/.config/systemd/user"
readonly CURRENT_DIR="$(pwd)"

# Mission Control Banner
echo -e "${MC_BLUE}"
cat << 'EOF'
╔═══════════════════════════════════════════════════════════════════════════════════╗
║  🚀 NZ7DEV GUI SERVICE INSTALLER 🚀                                               ║
║                                                                                   ║
║  Install GUI as a system service for always-on availability                      ║
╚═══════════════════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${MC_NC}"

show_help() {
    echo -e "${MC_WHITE}USAGE:${MC_NC}"
    echo "  $0 install    - Install and start the service"
    echo "  $0 start      - Start the service"
    echo "  $0 stop       - Stop the service"
    echo "  $0 restart    - Restart the service"
    echo "  $0 status     - Show service status"
    echo "  $0 logs       - Show service logs"
    echo "  $0 enable     - Enable auto-start on login"
    echo "  $0 disable    - Disable auto-start"
    echo "  $0 uninstall  - Remove the service completely"
    echo "  $0 url        - Show GUI URL"
    echo ""
    echo -e "${MC_YELLOW}EXAMPLES:${MC_NC}"
    echo "  $0 install    # Install service and auto-start GUI"
    echo "  $0 logs       # View real-time logs"
    echo "  $0 url        # Get the web interface URL"
}

install_service() {
    echo -e "${MC_WHITE}[INSTALL]${MC_NC} Installing NZ7DEV GUI service..."
    
    # Create systemd user directory
    mkdir -p "$USER_SERVICE_DIR"
    
    # Update service file with current directory
    if [[ -f "$SERVICE_FILE" ]]; then
        # Replace the working directory in the service file
        sed "s|WorkingDirectory=.*|WorkingDirectory=$CURRENT_DIR|g" "$SERVICE_FILE" > "$USER_SERVICE_DIR/$SERVICE_FILE"
        sed -i "s|cd /mnt/WD/dev/laika-local-rdp-nz7dev-gui|cd $CURRENT_DIR|g" "$USER_SERVICE_DIR/$SERVICE_FILE"
        sed -i "s|Environment=PYTHONPATH=.*|Environment=PYTHONPATH=$CURRENT_DIR|g" "$USER_SERVICE_DIR/$SERVICE_FILE"
    else
        echo -e "${MC_RED}[ERROR]${MC_NC} Service file $SERVICE_FILE not found!"
        return 1
    fi
    
    # Reload systemd
    systemctl --user daemon-reload
    
    # Enable and start service
    systemctl --user enable "$SERVICE_NAME"
    systemctl --user start "$SERVICE_NAME"
    
    echo -e "${MC_GREEN}[SUCCESS]${MC_NC} Service installed and started!"
    sleep 2
    show_status
    show_url
}

start_service() {
    echo -e "${MC_WHITE}[START]${MC_NC} Starting NZ7DEV GUI service..."
    systemctl --user start "$SERVICE_NAME"
    echo -e "${MC_GREEN}[SUCCESS]${MC_NC} Service started!"
    sleep 1
    show_status
}

stop_service() {
    echo -e "${MC_WHITE}[STOP]${MC_NC} Stopping NZ7DEV GUI service..."
    systemctl --user stop "$SERVICE_NAME"
    echo -e "${MC_GREEN}[SUCCESS]${MC_NC} Service stopped!"
}

restart_service() {
    echo -e "${MC_WHITE}[RESTART]${MC_NC} Restarting NZ7DEV GUI service..."
    systemctl --user restart "$SERVICE_NAME"
    echo -e "${MC_GREEN}[SUCCESS]${MC_NC} Service restarted!"
    sleep 1
    show_status
}

show_status() {
    echo -e "${MC_WHITE}[STATUS]${MC_NC} Service status:"
    systemctl --user --no-pager status "$SERVICE_NAME" || true
}

show_logs() {
    echo -e "${MC_WHITE}[LOGS]${MC_NC} Service logs (Ctrl+C to exit):"
    journalctl --user -u "$SERVICE_NAME" -f --no-pager
}

enable_service() {
    echo -e "${MC_WHITE}[ENABLE]${MC_NC} Enabling auto-start on login..."
    systemctl --user enable "$SERVICE_NAME"
    echo -e "${MC_GREEN}[SUCCESS]${MC_NC} Service will auto-start on login!"
}

disable_service() {
    echo -e "${MC_WHITE}[DISABLE]${MC_NC} Disabling auto-start..."
    systemctl --user disable "$SERVICE_NAME"
    echo -e "${MC_GREEN}[SUCCESS]${MC_NC} Service will not auto-start!"
}

uninstall_service() {
    echo -e "${MC_YELLOW}[UNINSTALL]${MC_NC} Removing NZ7DEV GUI service..."
    
    # Stop and disable service
    systemctl --user stop "$SERVICE_NAME" 2>/dev/null || true
    systemctl --user disable "$SERVICE_NAME" 2>/dev/null || true
    
    # Remove service file
    rm -f "$USER_SERVICE_DIR/$SERVICE_FILE"
    
    # Reload systemd
    systemctl --user daemon-reload
    systemctl --user reset-failed
    
    echo -e "${MC_GREEN}[SUCCESS]${MC_NC} Service uninstalled!"
}

show_url() {
    local ip_address
    # Use alternative method to get IP address since hostname command is not available
    ip_address=$(ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+' 2>/dev/null || echo "localhost")
    
    echo -e "${MC_WHITE}[ACCESS]${MC_NC} GUI is available at:"
    echo -e "  🌐 Local:   ${MC_BLUE}http://localhost:5000${MC_NC}"
    echo -e "  🖥️  IP:      ${MC_BLUE}http://127.0.0.1:5000${MC_NC}"
    if [[ "$ip_address" != "localhost" ]]; then
        echo -e "  📱 Network: ${MC_BLUE}http://$ip_address:5000${MC_NC}"
    else
        echo -e "  📱 Network: ${MC_YELLOW}(IP detection failed)${MC_NC}"
    fi
}

check_dependencies() {
    # Check if service file exists
    if [[ ! -f "$SERVICE_FILE" ]]; then
        echo -e "${MC_RED}[ERROR]${MC_NC} Service file $SERVICE_FILE not found!"
        echo -e "${MC_YELLOW}[INFO]${MC_NC} Make sure you're in the correct directory"
        return 1
    fi
    
    # Check if GUI files exist
    if [[ ! -f "nz7dev_gui.py" ]]; then
        echo -e "${MC_RED}[ERROR]${MC_NC} nz7dev_gui.py not found!"
        echo -e "${MC_YELLOW}[INFO]${MC_NC} Make sure all GUI files are present"
        return 1
    fi
    
    return 0
}

# Main execution
case "${1:-help}" in
    "install")
        check_dependencies && install_service
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
    "help"|"--help"|"-h"|"")
        show_help
        ;;
    *)
        echo -e "${MC_RED}[ERROR]${MC_NC} Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac 