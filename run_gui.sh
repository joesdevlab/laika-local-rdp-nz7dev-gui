#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════════
# 🚀 NZ7DEV MISSION CONTROL GUI LAUNCHER - CLEAN VERSION
# ═══════════════════════════════════════════════════════════════════════════════════
# Easy launcher for the web-based Mission Control interface
# Updated to avoid Cursor environment interference
# ═══════════════════════════════════════════════════════════════════════════════════

set -euo pipefail

# Colors for output
readonly MC_BLUE='\033[0;34m'
readonly MC_GREEN='\033[0;32m'
readonly MC_YELLOW='\033[1;33m'
readonly MC_RED='\033[0;31m'
readonly MC_WHITE='\033[1;37m'
readonly MC_NC='\033[0m'

# Mission Control ASCII
echo -e "${MC_BLUE}"
cat << 'EOF'
╔═══════════════════════════════════════════════════════════════════════════════════╗
║  🚀 NZ7DEV MISSION CONTROL GUI LAUNCHER 🚀                                        ║
║                                                                                   ║
║  ██████╗ ██╗   ██╗██╗                                                             ║
║  ██╔══██╗██║   ██║██║                                                             ║
║  ██████╔╝██║   ██║██║                                                             ║
║  ██╔══██╗██║   ██║██║                                                             ║
║  ██████╔╝╚██████╔╝██║                                                             ║
║  ╚═════╝  ╚═════╝ ╚═╝                                                             ║
║                                                                                   ║
║                    Web-based Mission Control Interface                           ║
║                           CLEAN LAUNCH MODE                                      ║
╚═══════════════════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${MC_NC}"

echo -e "${MC_WHITE}[MISSION CONTROL]${MC_NC} Preparing clean GUI launch sequence..."

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Define clean environment (bypass Cursor's Python interference)
export PATH="/usr/local/sbin:/usr/local/bin:/usr/bin:/usr/sbin:/bin:/sbin"
export PYTHONPATH=""

# Use system python directly
PYTHON_CMD="/usr/bin/python3"

# Check if nz7dev script exists
if [[ ! -f "./nz7dev" ]]; then
    echo -e "${MC_RED}[ERROR]${MC_NC} nz7dev script not found in current directory!"
    echo -e "${MC_YELLOW}[INFO]${MC_NC} Please ensure you're running this from the same directory as the nz7dev script"
    exit 1
fi

# Make nz7dev executable
chmod +x ./nz7dev

# Remove problematic virtual environment if it exists
if [[ -d "venv" ]]; then
    echo -e "${MC_YELLOW}[CLEANUP]${MC_NC} Removing problematic virtual environment (Cursor interference)..."
    rm -rf venv
fi

# Check Python installation
if ! command -v $PYTHON_CMD &>/dev/null; then
    echo -e "${MC_RED}[ERROR]${MC_NC} Python 3 is required but not found at $PYTHON_CMD!"
    echo -e "${MC_YELLOW}[INFO]${MC_NC} Please install Python 3: sudo pacman -S python"
    exit 1
fi

echo -e "${MC_GREEN}[SUCCESS]${MC_NC} Using clean system Python: $PYTHON_CMD"

# Check and install required packages
echo -e "${MC_BLUE}[SETUP]${MC_NC} Verifying Python packages..."

missing_packages=()
for package in "flask" "flask_socketio" "psutil" "yaml"; do
    if ! $PYTHON_CMD -c "import $package" 2>/dev/null; then
        missing_packages+=("$package")
    fi
done

# Install missing packages if any
if [ ${#missing_packages[@]} -gt 0 ]; then
    echo -e "${MC_YELLOW}[INSTALL]${MC_NC} Installing missing packages: ${missing_packages[*]}"
    
    # Try pacman first (Arch Linux)
    if command -v pacman >/dev/null 2>&1; then
        for package in "${missing_packages[@]}"; do
            case $package in
                "flask") 
                    echo -e "${MC_BLUE}[PACMAN]${MC_NC} Installing python-flask..."
                    sudo pacman -S --noconfirm python-flask 2>/dev/null || echo "  - Flask install failed, will try pip fallback"
                    ;;
                "flask_socketio") 
                    echo -e "${MC_BLUE}[PACMAN]${MC_NC} Installing python-flask-socketio..."
                    sudo pacman -S --noconfirm python-flask-socketio 2>/dev/null || echo "  - Flask-SocketIO install failed, will try pip fallback"
                    ;;
                "psutil") 
                    echo -e "${MC_BLUE}[PACMAN]${MC_NC} Installing python-psutil..."
                    sudo pacman -S --noconfirm python-psutil 2>/dev/null || echo "  - psutil install failed, will try pip fallback"
                    ;;
                "yaml") 
                    echo -e "${MC_BLUE}[PACMAN]${MC_NC} Installing python-yaml..."
                    sudo pacman -S --noconfirm python-yaml 2>/dev/null || echo "  - PyYAML install failed, will try pip fallback"
                    ;;
            esac
        done
    fi
    
    # Fallback to pip with system packages override
    if ! $PYTHON_CMD -c "import flask, flask_socketio, psutil, yaml" 2>/dev/null; then
        echo -e "${MC_YELLOW}[FALLBACK]${MC_NC} Installing via pip with --break-system-packages..."
        $PYTHON_CMD -m pip install --break-system-packages flask flask-socketio psutil pyyaml eventlet 2>/dev/null || {
            echo -e "${MC_RED}[ERROR]${MC_NC} Failed to install packages"
            echo -e "${MC_YELLOW}[MANUAL]${MC_NC} Please install manually:"
            echo "  sudo pacman -S python-flask python-flask-socketio python-psutil python-yaml"
            echo "  or"
            echo "  $PYTHON_CMD -m pip install --break-system-packages flask flask-socketio psutil pyyaml"
            exit 1
        }
    fi
fi

echo -e "${MC_GREEN}[SUCCESS]${MC_NC} All Python packages available"

# Check if templates directory exists
if [[ ! -d "templates" ]]; then
    echo -e "${MC_RED}[ERROR]${MC_NC} templates directory not found!"
    echo -e "${MC_YELLOW}[INFO]${MC_NC} Please ensure all GUI files are properly installed"
    exit 1
fi

# Kill any existing processes
echo -e "${MC_BLUE}[CLEANUP]${MC_NC} Stopping existing processes..."
pkill -f "nz7dev_gui.py" 2>/dev/null || true
lsof -ti:5000 | xargs -r kill -9 2>/dev/null || true

# Display startup information
echo
echo -e "${MC_GREEN}╔═══════════════════════════════════════════════════════════════════════════════════╗${MC_NC}"
echo -e "${MC_GREEN}║  🚀 MISSION CONTROL GUI READY FOR LAUNCH 🚀                                      ║${MC_NC}"
echo -e "${MC_GREEN}╚═══════════════════════════════════════════════════════════════════════════════════╝${MC_NC}"
echo
echo -e "${MC_WHITE}[LAUNCH INFO]${MC_NC}"
echo -e "  🌐 Web Interface: ${MC_BLUE}http://localhost:5000${MC_NC}"
echo -e "  🖥️  Local Access:  ${MC_BLUE}http://127.0.0.1:5000${MC_NC}"
echo -e "  📱 Network Access: ${MC_BLUE}http://$(hostname -I | awk '{print $1}' 2>/dev/null || echo 'localhost'):5000${MC_NC}"
echo
echo -e "${MC_WHITE}[NEW FEATURES]${MC_NC}"
echo -e "  ⚡ Quick RDP Spawner - Connect to any IP instantly"
echo -e "  📊 Active Connection Monitoring - Real-time status"
echo -e "  🎯 One-Click Presets (ALPHA-FOXTROT)"
echo -e "  🖼️  Custom Window Positioning"
echo -e "  ⌨️  Keyboard Shortcuts (Ctrl+Enter, Alt+1-6)"
echo
echo -e "${MC_WHITE}[CLASSIC FEATURES]${MC_NC}"
echo -e "  ✅ Real-time RDP connection monitoring"
echo -e "  ✅ Individual VM control (start/stop/configure)"
echo -e "  ✅ Dynamic window positioning"
echo -e "  ✅ Workspace layout visualization"
echo -e "  ✅ Live status updates via WebSocket"
echo -e "  ✅ Complete mission control integration"
echo
echo -e "${MC_WHITE}[CONTROLS]${MC_NC}"
echo -e "  🌅 Morning Routine - Complete startup sequence"
echo -e "  🚀 Launch Fleet - Start RDP connections"
echo -e "  ⚡ LUDICROUS SPEED - Ultra-fast positioning"
echo -e "  🪟 Position Windows - Organize workspace"
echo -e "  🛑 Emergency Stop - Abort all operations"
echo
echo -e "${MC_YELLOW}[READY]${MC_NC} Press Ctrl+C to stop the GUI server"
echo -e "${MC_GREEN}[LAUNCH]${MC_NC} Starting Mission Control GUI with clean environment..."
echo

# Launch the GUI with completely clean environment
exec env -i \
    PATH="/usr/local/sbin:/usr/local/bin:/usr/bin:/usr/sbin:/bin:/sbin" \
    HOME="$HOME" \
    USER="$USER" \
    DISPLAY="${DISPLAY:-}" \
    TERM="${TERM:-xterm}" \
    PWD="$SCRIPT_DIR" \
    $PYTHON_CMD nz7dev_gui.py 