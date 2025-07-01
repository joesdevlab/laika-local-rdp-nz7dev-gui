#!/usr/bin/env bash
# Professional Clean Launcher for NZ7DEV Mission Control GUI
# Minimal launcher for the professional edition with clean environment

set -euo pipefail

# Colors for output
readonly MC_BLUE='\033[0;34m'
readonly MC_GREEN='\033[0;32m'
readonly MC_YELLOW='\033[1;33m'
readonly MC_RED='\033[0;31m'
readonly MC_WHITE='\033[1;37m'
readonly MC_PURPLE='\033[0;35m'
readonly MC_NC='\033[0m'

echo -e "${MC_BLUE}🚀 NZ7DEV Mission Control GUI - Professional Edition Clean Launcher${MC_NC}"
echo

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Define clean environment for professional edition
export PATH="/usr/local/sbin:/usr/local/bin:/usr/bin:/usr/sbin:/bin:/sbin"
export PYTHONPATH="$SCRIPT_DIR"
export PYTHONOPTIMIZE=2
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1
export DISPLAY="${DISPLAY:-:1}"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-1}"

# Professional Python configuration
PYTHON_CMD="/usr/bin/python3"

# Check required professional edition files
echo -e "${MC_YELLOW}[VERIFICATION]${MC_NC} Checking professional edition files..."

required_files=(
    "nz7dev_gui.py:Main application"
    "templates/index.html:Web interface"
    "static/css/styles.css:Professional styles"
    "nz7dev:Fleet control script"
)

missing_files=()
for file_info in "${required_files[@]}"; do
    file="${file_info%:*}"
    desc="${file_info#*:}"
    
    if [[ -f "$file" ]]; then
        echo -e "${MC_GREEN}  ✓${MC_NC} $file - $desc"
    else
        echo -e "${MC_RED}  ✗${MC_NC} $file - $desc"
        missing_files+=("$file")
    fi
done

if [[ ${#missing_files[@]} -gt 0 ]]; then
    echo -e "${MC_RED}[ERROR]${MC_NC} Missing required professional edition files!"
    exit 1
fi

# Check system Python packages for professional edition
echo -e "${MC_YELLOW}[DEPENDENCIES]${MC_NC} Checking professional edition packages..."

professional_modules=(
    "flask:Flask web framework"
    "flask_socketio:Real-time communication"
    "psutil:System monitoring" 
    "yaml:Configuration parser"
)

missing_modules=()
for module_info in "${professional_modules[@]}"; do
    module="${module_info%:*}"
    desc="${module_info#*:}"
    
    if $PYTHON_CMD -c "import $module" 2>/dev/null; then
        echo -e "${MC_GREEN}  ✓${MC_NC} $module - $desc"
    else
        echo -e "${MC_RED}  ✗${MC_NC} $module - $desc"
        missing_modules+=("$module")
    fi
done

# Auto-install missing packages for professional edition
if [[ ${#missing_modules[@]} -gt 0 ]]; then
    echo -e "${MC_YELLOW}[INSTALL]${MC_NC} Installing professional edition packages..."
    
    # Try system package manager first
    if command -v pacman >/dev/null 2>&1; then
        declare -A pkg_map=(
            ["flask"]="python-flask"
            ["flask_socketio"]="python-flask-socketio"
            ["psutil"]="python-psutil" 
            ["yaml"]="python-yaml"
        )
        
        packages_to_install=()
        for module in "${missing_modules[@]}"; do
            [[ -n "${pkg_map[$module]:-}" ]] && packages_to_install+=("${pkg_map[$module]}")
        done
        
        if [[ ${#packages_to_install[@]} -gt 0 ]]; then
            sudo pacman -S --needed --noconfirm "${packages_to_install[@]}" 2>/dev/null || {
                echo -e "${MC_YELLOW}[FALLBACK]${MC_NC} Pacman failed, using pip..."
            }
        fi
    fi
    
    # Fallback to pip if needed
    if ! $PYTHON_CMD -c "import flask, flask_socketio, psutil, yaml" 2>/dev/null; then
        echo -e "${MC_YELLOW}[PIP]${MC_NC} Installing via pip with --break-system-packages..."
        $PYTHON_CMD -m pip install --break-system-packages --upgrade \
            flask flask-socketio psutil pyyaml eventlet gevent-websocket || {
            echo -e "${MC_RED}[ERROR]${MC_NC} Failed to install professional edition packages"
            exit 1
        }
    fi
fi

echo -e "${MC_GREEN}[SUCCESS]${MC_NC} All professional edition packages available"

# Check optional system dependencies
echo -e "${MC_YELLOW}[SYSTEM]${MC_NC} Checking system integration..."

optional_deps=(
    "hyprctl:Hyprland workspace manager"
    "xfreerdp:RDP client" 
    "lsof:Network monitoring"
)

for dep_info in "${optional_deps[@]}"; do
    cmd="${dep_info%:*}"
    desc="${dep_info#*:}"
    
    if command -v "$cmd" >/dev/null 2>&1; then
        echo -e "${MC_GREEN}  ✓${MC_NC} $cmd - $desc"
    else
        echo -e "${MC_YELLOW}  ⚠${MC_NC} $cmd - $desc (optional)"
    fi
done

# Kill any existing processes
echo -e "${MC_YELLOW}[CLEANUP]${MC_NC} Cleaning up existing processes..."
pkill -f "nz7dev_gui.py" 2>/dev/null || true
lsof -ti:5000 | xargs -r kill -9 2>/dev/null || true

# Change to script directory and set permissions
cd "$SCRIPT_DIR"
chmod +x ./nz7dev *.sh 2>/dev/null || true

# Create required directories
mkdir -p logs static/css static/js templates

echo -e "${MC_GREEN}╔═══════════════════════════════════════════════════════════════════════════════════╗${MC_NC}"
echo -e "${MC_GREEN}║  🚀 MISSION CONTROL PROFESSIONAL EDITION LAUNCHING 🚀                            ║${MC_NC}"
echo -e "${MC_GREEN}╚═══════════════════════════════════════════════════════════════════════════════════╝${MC_NC}"
echo
echo -e "${MC_WHITE}[ACCESS INFORMATION]${MC_NC}"
local_ip=$(ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+' 2>/dev/null || echo "localhost")
echo -e "  🌐 Local Interface:  ${MC_BLUE}http://localhost:5000${MC_NC}"
echo -e "  🖥️  Loopback Access:  ${MC_BLUE}http://127.0.0.1:5000${MC_NC}"
if [[ "$local_ip" != "localhost" ]]; then
    echo -e "  📱 Network Access:   ${MC_BLUE}http://$local_ip:5000${MC_NC}"
fi
echo

echo -e "${MC_PURPLE}[PROFESSIONAL FEATURES]${MC_NC}"
echo -e "  🎯 Visual Workspace Manager with drag & drop placement"
echo -e "  📐 Advanced size presets and custom resolutions"
echo -e "  🗂️  Scratchpad integration with Hyprland"
echo -e "  📊 Real-time monitoring and performance optimization"
echo -e "  🎨 Professional UI with modern design system"
echo

echo -e "${MC_WHITE}[QUICK CONTROLS]${MC_NC}"
echo -e "  • Ctrl+Enter = Quick RDP deploy"
echo -e "  • Alt+1-6 = Fleet presets (ALPHA-FOXTROT)"
echo -e "  • F5 = Refresh status"
echo -e "  • Escape = Close modals"
echo

echo -e "${MC_YELLOW}[READY]${MC_NC} Press Ctrl+C to stop the professional server"
echo -e "${MC_GREEN}[LAUNCH]${MC_NC} Starting NZ7DEV Mission Control Professional Edition..."
echo

# Set professional environment variables
export FLASK_ENV=production
export FLASK_DEBUG=0
export SECRET_KEY="nz7dev-mission-control-pro-2024-visual-workspace"

# Launch the Professional Edition with clean optimized environment
exec env \
    PATH="$PATH" \
    HOME="$HOME" \
    USER="$USER" \
    PYTHONPATH="$SCRIPT_DIR" \
    PYTHONOPTIMIZE=2 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_ENV=production \
    FLASK_DEBUG=0 \
    SECRET_KEY="nz7dev-mission-control-pro-2024-visual-workspace" \
    DISPLAY="$DISPLAY" \
    WAYLAND_DISPLAY="$WAYLAND_DISPLAY" \
    XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}" \
    $PYTHON_CMD -O -u nz7dev_gui.py 