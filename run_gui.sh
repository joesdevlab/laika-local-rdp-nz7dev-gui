#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════════
# 🚀 NZ7DEV MISSION CONTROL GUI LAUNCHER - PROFESSIONAL EDITION
# ═══════════════════════════════════════════════════════════════════════════════════
# Professional launcher for the web-based Mission Control interface
# Enhanced with Visual Workspace Manager and Performance Optimizations
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

# Professional Mission Control ASCII
echo -e "${MC_BLUE}"
cat << 'EOF'
╔═══════════════════════════════════════════════════════════════════════════════════╗
║  🚀 NZ7DEV MISSION CONTROL GUI - PROFESSIONAL EDITION 🚀                         ║
║                                                                                   ║
║  ██████╗ ██████╗  ██████╗                                                         ║
║  ██╔══██╗██╔══██╗██╔═══██╗                                                        ║
║  ██████╔╝██████╔╝██║   ██║                                                        ║
║  ██╔═══╝ ██╔══██╗██║   ██║                                                        ║
║  ██║     ██║  ██║╚██████╔╝                                                        ║
║  ╚═╝     ╚═╝  ╚═╝ ╚═════╝                                                         ║
║                                                                                   ║
║              Web-based Mission Control Interface                                 ║
║                   PROFESSIONAL EDITION v2.0                                     ║
║                                                                                   ║
║  ⚡ Visual Workspace Manager  🎯 Advanced RDP Management                         ║
║  📊 Real-time Monitoring     🖥️  Hyprland Integration                            ║
╚═══════════════════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${MC_NC}"

echo -e "${MC_WHITE}[MISSION CONTROL PRO]${MC_NC} Initializing professional launch sequence..."

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Define optimized environment
export PATH="/usr/local/sbin:/usr/local/bin:/usr/bin:/usr/sbin:/bin:/sbin"
export PYTHONPATH="$SCRIPT_DIR"
export PYTHONOPTIMIZE=2
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# Professional Python configuration
PYTHON_CMD="/usr/bin/python3"
PYTHON_OPTS="-O -u"  # Optimize bytecode, unbuffered output

# Verify professional edition files
echo -e "${MC_BLUE}[VERIFICATION]${MC_NC} Verifying professional edition installation..."

required_files=(
    "nz7dev_gui.py"
    "templates/index.html"
    "static/css/styles.css"
    "nz7dev"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [[ -f "$file" ]]; then
        echo -e "${MC_GREEN}  ✓${MC_NC} Found: $file"
    else
        echo -e "${MC_RED}  ✗${MC_NC} Missing: $file"
        missing_files+=("$file")
    fi
done

if [[ ${#missing_files[@]} -gt 0 ]]; then
    echo -e "${MC_RED}[ERROR]${MC_NC} Missing required professional edition files!"
    echo -e "${MC_YELLOW}[INFO]${MC_NC} Please ensure all files are properly installed"
    exit 1
fi

# Check nz7dev script
if [[ ! -f "./nz7dev" ]]; then
    echo -e "${MC_RED}[ERROR]${MC_NC} nz7dev script not found in current directory!"
    exit 1
fi

# Make scripts executable
chmod +x ./nz7dev *.sh 2>/dev/null || true

# Create required directories
echo -e "${MC_BLUE}[SETUP]${MC_NC} Creating required directories..."
mkdir -p logs static/css static/js templates
echo -e "${MC_GREEN}  ✓${MC_NC} Directories created"

# Check Python installation and version
echo -e "${MC_BLUE}[PYTHON]${MC_NC} Verifying Python environment..."
if ! command -v $PYTHON_CMD &>/dev/null; then
    echo -e "${MC_RED}[ERROR]${MC_NC} Python 3 is required but not found at $PYTHON_CMD!"
    exit 1
fi

python_version=$($PYTHON_CMD --version 2>&1 | grep -oP '\d+\.\d+\.\d+')
echo -e "${MC_GREEN}[SUCCESS]${MC_NC} Using Python $python_version at $PYTHON_CMD"

# Check and install professional edition dependencies
echo -e "${MC_BLUE}[DEPENDENCIES]${MC_NC} Verifying professional edition packages..."

# Core Python modules for professional edition
professional_modules=(
    "flask:Flask web framework"
    "flask_socketio:Flask-SocketIO for real-time communication"
    "psutil:System and process utilities"
    "yaml:YAML configuration parser"
    "threading:Threading support (built-in)"
    "concurrent.futures:Concurrent execution (built-in)"
    "dataclasses:Data classes (built-in)"
    "functools:Function tools (built-in)"
)

missing_modules=()
for module_info in "${professional_modules[@]}"; do
    module="${module_info%:*}"
    description="${module_info#*:}"
    
    if $PYTHON_CMD -c "import $module" 2>/dev/null; then
        echo -e "${MC_GREEN}  ✓${MC_NC} $module - $description"
    else
        echo -e "${MC_RED}  ✗${MC_NC} $module - $description"
        missing_modules+=("$module")
    fi
done

# Install missing packages if any
if [ ${#missing_modules[@]} -gt 0 ]; then
    echo -e "${MC_YELLOW}[INSTALL]${MC_NC} Installing missing professional edition packages..."
    
    # Map Python modules to Arch packages
    declare -A package_map=(
        ["flask"]="python-flask"
        ["flask_socketio"]="python-flask-socketio"
        ["psutil"]="python-psutil"
        ["yaml"]="python-yaml"
    )
    
    packages_to_install=()
    for module in "${missing_modules[@]}"; do
        if [[ -n "${package_map[$module]:-}" ]]; then
            packages_to_install+=("${package_map[$module]}")
        fi
    done
    
    # Try pacman first (Arch Linux)
    if command -v pacman >/dev/null 2>&1 && [[ ${#packages_to_install[@]} -gt 0 ]]; then
        echo -e "${MC_BLUE}[PACMAN]${MC_NC} Installing via system package manager..."
        sudo pacman -S --needed --noconfirm "${packages_to_install[@]}" 2>/dev/null || {
            echo -e "${MC_YELLOW}[FALLBACK]${MC_NC} System package installation failed, trying pip..."
        }
    fi
    
    # Fallback to pip with system packages override
    if ! $PYTHON_CMD -c "import flask, flask_socketio, psutil, yaml" 2>/dev/null; then
        echo -e "${MC_YELLOW}[PIP]${MC_NC} Installing via pip with --break-system-packages..."
        $PYTHON_CMD -m pip install --break-system-packages --upgrade \
            flask flask-socketio psutil pyyaml eventlet gevent-websocket 2>/dev/null || {
            echo -e "${MC_RED}[ERROR]${MC_NC} Failed to install Python packages"
            echo -e "${MC_YELLOW}[MANUAL]${MC_NC} Please install manually:"
            echo "  sudo pacman -S python-flask python-flask-socketio python-psutil python-yaml"
            exit 1
        }
    fi
fi

echo -e "${MC_GREEN}[SUCCESS]${MC_NC} All professional edition packages available"

# Check system dependencies for professional features
echo -e "${MC_BLUE}[SYSTEM]${MC_NC} Verifying system dependencies..."

system_deps=(
    "hyprctl:Hyprland window manager (for workspace management)"
    "xfreerdp:FreeRDP client (for RDP connections)"
    "lsof:Network port monitoring"
)

missing_system_deps=()
for dep_info in "${system_deps[@]}"; do
    cmd="${dep_info%:*}"
    description="${dep_info#*:}"
    
    if command -v "$cmd" >/dev/null 2>&1; then
        echo -e "${MC_GREEN}  ✓${MC_NC} $cmd - $description"
    else
        echo -e "${MC_YELLOW}  ⚠${MC_NC} $cmd - $description (optional)"
        missing_system_deps+=("$cmd")
    fi
done

if [[ ${#missing_system_deps[@]} -gt 0 ]]; then
    echo -e "${MC_YELLOW}[INFO]${MC_NC} Some optional features may not work without:"
    printf "  %s\n" "${missing_system_deps[@]}"
fi

# Cleanup existing processes
echo -e "${MC_BLUE}[CLEANUP]${MC_NC} Stopping existing processes..."
pkill -f "nz7dev_gui.py" 2>/dev/null || true
lsof -ti:5000 | xargs -r kill -9 2>/dev/null || true
echo -e "${MC_GREEN}  ✓${MC_NC} Cleanup completed"

# Display professional edition information
echo
echo -e "${MC_GREEN}╔═══════════════════════════════════════════════════════════════════════════════════╗${MC_NC}"
echo -e "${MC_GREEN}║  🚀 MISSION CONTROL PROFESSIONAL EDITION READY FOR LAUNCH 🚀                     ║${MC_NC}"
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
echo -e "  🎯 Visual Workspace Manager - Drag & drop VM placement across workspaces"
echo -e "  📐 Advanced Size Presets - Full, half-left/right, quarter, third, custom sizes"
echo -e "  🗂️  Scratchpad Integration - Floating windows with grid layout support"
echo -e "  📊 Real-time Monitoring - Live workspace state and connection tracking"
echo -e "  ⚡ Performance Optimized - Caching, concurrent operations, smart updates"
echo -e "  🎨 Modern UI Design - Professional dark theme with smooth animations"
echo

echo -e "${MC_WHITE}[ENHANCED CONTROLS]${MC_NC}"
echo -e "  ⌨️  Quick Deploy: Ctrl+Enter in IP field"
echo -e "  🎯 Fleet Presets: Alt+1-6 for ALPHA through FOXTROT"
echo -e "  🚀 Fleet Commands: Morning routine, Ludicrous speed, Emergency stop"
echo -e "  🪟 Workspace Management: Visual assignment, batch operations"
echo -e "  📈 Live Logs: Real-time system monitoring and debugging"
echo

echo -e "${MC_WHITE}[NEW IN v2.0 PROFESSIONAL]${MC_NC}"
echo -e "  • Visual workspace grid with real-time status indicators"
echo -e "  • Drag-and-drop VM assignment with size preset selection"
echo -e "  • Scratchpad workspace support with toggle visibility"
echo -e "  • Auto-geometry detection with waybar compensation"
echo -e "  • Enhanced RDP management with background cleanup"
echo -e "  • Advanced caching and performance optimizations"
echo -e "  • Professional error handling and user feedback"
echo

echo -e "${MC_CYAN}[HYPRLAND INTEGRATION]${MC_NC}"
if command -v hyprctl >/dev/null 2>&1; then
    echo -e "  ✅ Hyprland detected - Full workspace management available"
    echo -e "  🖥️  Window positioning, workspace assignment, scratchpad support"
else
    echo -e "  ⚠️  Hyprland not detected - Limited workspace features"
fi

echo
echo -e "${MC_YELLOW}[READY]${MC_NC} Press Ctrl+C to stop the professional GUI server"
echo -e "${MC_GREEN}[LAUNCH]${MC_NC} Starting Mission Control Professional Edition..."
echo

# Set optimized environment variables
export FLASK_ENV=production
export FLASK_DEBUG=0
export SECRET_KEY="nz7dev-mission-control-pro-2024-visual-workspace"

# Display and window manager environment
export DISPLAY="${DISPLAY:-:1}"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-1}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"

# Launch the Professional Edition with optimized environment
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
    XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" \
    $PYTHON_CMD $PYTHON_OPTS nz7dev_gui.py 