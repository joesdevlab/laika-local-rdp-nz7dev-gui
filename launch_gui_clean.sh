#!/usr/bin/env bash
# Clean launcher for NZ7DEV Mission Control GUI
# Bypasses Cursor environment interference

set -euo pipefail

# Colors for output
readonly MC_BLUE='\033[0;34m'
readonly MC_GREEN='\033[0;32m'
readonly MC_YELLOW='\033[1;33m'
readonly MC_RED='\033[0;31m'
readonly MC_WHITE='\033[1;37m'
readonly MC_NC='\033[0m'

echo -e "${MC_BLUE}🚀 NZ7DEV Mission Control GUI - Clean Launcher${MC_NC}"
echo

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Define clean environment
export PATH="/usr/local/sbin:/usr/local/bin:/usr/bin:/usr/sbin:/bin:/sbin"
export PYTHONPATH=""
export DISPLAY="${DISPLAY:-}"

# Use system python directly
PYTHON_CMD="/usr/bin/python3"

# Check if required packages are available systemwide
echo -e "${MC_YELLOW}[INFO]${MC_NC} Checking system Python packages..."

if ! $PYTHON_CMD -c "import flask" 2>/dev/null; then
    echo -e "${MC_RED}[ERROR]${MC_NC} Flask not installed systemwide"
    echo -e "${MC_YELLOW}[INSTALL]${MC_NC} Installing Flask systemwide..."
    sudo pacman -S --noconfirm python-flask 2>/dev/null || {
        echo -e "${MC_RED}[ERROR]${MC_NC} Failed to install Flask via pacman"
        echo -e "${MC_YELLOW}[INFO]${MC_NC} You may need to install packages manually:"
        echo "  sudo pacman -S python-flask python-flask-socketio python-psutil python-yaml"
        exit 1
    }
fi

if ! $PYTHON_CMD -c "import flask_socketio" 2>/dev/null; then
    echo -e "${MC_YELLOW}[INSTALL]${MC_NC} Installing Flask-SocketIO..."
    sudo pacman -S --noconfirm python-flask-socketio 2>/dev/null || true
fi

if ! $PYTHON_CMD -c "import psutil" 2>/dev/null; then
    echo -e "${MC_YELLOW}[INSTALL]${MC_NC} Installing psutil..."
    sudo pacman -S --noconfirm python-psutil 2>/dev/null || true
fi

if ! $PYTHON_CMD -c "import yaml" 2>/dev/null; then
    echo -e "${MC_YELLOW}[INSTALL]${MC_NC} Installing PyYAML..."
    sudo pacman -S --noconfirm python-yaml 2>/dev/null || true
fi

# Final check
echo -e "${MC_YELLOW}[CHECK]${MC_NC} Verifying all packages..."
if ! $PYTHON_CMD -c "import flask, flask_socketio, psutil, yaml" 2>/dev/null; then
    echo -e "${MC_RED}[ERROR]${MC_NC} Missing packages. Installing via pip with --break-system-packages..."
    $PYTHON_CMD -m pip install --break-system-packages flask flask-socketio psutil pyyaml eventlet
fi

echo -e "${MC_GREEN}[SUCCESS]${MC_NC} All packages available"

# Kill any existing processes on port 5000
echo -e "${MC_YELLOW}[CLEANUP]${MC_NC} Cleaning up existing processes..."
pkill -f "nz7dev_gui.py" 2>/dev/null || true
lsof -ti:5000 | xargs -r kill -9 2>/dev/null || true

# Change to script directory
cd "$SCRIPT_DIR"

# Make nz7dev script executable
chmod +x ./nz7dev 2>/dev/null || true

echo -e "${MC_GREEN}╔═══════════════════════════════════════════════════════════════════════════════════╗${MC_NC}"
echo -e "${MC_GREEN}║  🚀 MISSION CONTROL GUI LAUNCHING 🚀                                             ║${MC_NC}"
echo -e "${MC_GREEN}╚═══════════════════════════════════════════════════════════════════════════════════╝${MC_NC}"
echo
echo -e "${MC_WHITE}[ACCESS INFO]${MC_NC}"
echo -e "  🌐 Web Interface: ${MC_BLUE}http://localhost:5000${MC_NC}"
echo -e "  🖥️  Local Access:  ${MC_BLUE}http://127.0.0.1:5000${MC_NC}"
echo -e "  📱 Network Access: ${MC_BLUE}http://$(hostname -I | awk '{print $1}' 2>/dev/null || echo 'localhost'):5000${MC_NC}"
echo
echo -e "${MC_WHITE}[FEATURES]${MC_NC}"
echo -e "  ✅ Quick RDP Spawner - Connect to any IP instantly"
echo -e "  ✅ Real-time connection monitoring"
echo -e "  ✅ Automatic window positioning"
echo -e "  ✅ Fleet management controls"
echo -e "  ✅ Live status updates"
echo
echo -e "${MC_WHITE}[SHORTCUTS]${MC_NC}"
echo -e "  • Ctrl+Enter in IP field = Quick spawn"
echo -e "  • Alt+1-6 = Quick preset selection"
echo -e "  • Escape = Close modals"
echo
echo -e "${MC_YELLOW}[READY]${MC_NC} Press Ctrl+C to stop the server"
echo -e "${MC_GREEN}[LAUNCH]${MC_NC} Starting NZ7DEV Mission Control GUI..."
echo

# Start the GUI with clean environment
exec env -i \
    PATH="/usr/local/sbin:/usr/local/bin:/usr/bin:/usr/sbin:/bin:/sbin" \
    HOME="$HOME" \
    USER="$USER" \
    DISPLAY="${DISPLAY:-}" \
    PWD="$SCRIPT_DIR" \
    $PYTHON_CMD nz7dev_gui.py 