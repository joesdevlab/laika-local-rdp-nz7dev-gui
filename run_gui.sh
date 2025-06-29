#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════════
# 🚀 NZ7DEV MISSION CONTROL GUI LAUNCHER
# ═══════════════════════════════════════════════════════════════════════════════════
# Easy launcher for the web-based Mission Control interface
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
╚═══════════════════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${MC_NC}"

echo -e "${MC_WHITE}[MISSION CONTROL]${MC_NC} Preparing GUI launch sequence..."

# Check if nz7dev script exists
if [[ ! -f "./nz7dev" ]]; then
    echo -e "${MC_RED}[ERROR]${MC_NC} nz7dev script not found in current directory!"
    echo -e "${MC_YELLOW}[INFO]${MC_NC} Please ensure you're running this from the same directory as the nz7dev script"
    exit 1
fi

# Make nz7dev executable
chmod +x ./nz7dev

# Check Python installation
if ! command -v python3 &>/dev/null; then
    echo -e "${MC_RED}[ERROR]${MC_NC} Python 3 is required but not installed!"
    echo -e "${MC_YELLOW}[INFO]${MC_NC} Please install Python 3: sudo pacman -S python"
    exit 1
fi

# Check pip installation
if ! command -v pip3 &>/dev/null; then
    echo -e "${MC_YELLOW}[WARNING]${MC_NC} pip3 not found, attempting to install..."
    sudo pacman -S python-pip || {
        echo -e "${MC_RED}[ERROR]${MC_NC} Failed to install pip"
        exit 1
    }
fi

echo -e "${MC_GREEN}[SUCCESS]${MC_NC} Python 3 and pip3 detected"

# Create virtual environment if it doesn't exist
if [[ ! -d "venv" ]]; then
    echo -e "${MC_BLUE}[SETUP]${MC_NC} Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${MC_BLUE}[SETUP]${MC_NC} Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo -e "${MC_BLUE}[SETUP]${MC_NC} Installing/updating Python dependencies..."
pip install -r requirements.txt

# Check if templates directory exists
if [[ ! -d "templates" ]]; then
    echo -e "${MC_RED}[ERROR]${MC_NC} templates directory not found!"
    echo -e "${MC_YELLOW}[INFO]${MC_NC} Please ensure all GUI files are properly installed"
    exit 1
fi

# Display startup information
echo
echo -e "${MC_GREEN}╔═══════════════════════════════════════════════════════════════════════════════════╗${MC_NC}"
echo -e "${MC_GREEN}║  🚀 MISSION CONTROL GUI READY FOR LAUNCH 🚀                                      ║${MC_NC}"
echo -e "${MC_GREEN}╚═══════════════════════════════════════════════════════════════════════════════════╝${MC_NC}"
echo
echo -e "${MC_WHITE}[LAUNCH INFO]${MC_NC}"
echo -e "  🌐 Web Interface: ${MC_BLUE}http://localhost:5000${MC_NC}"
echo -e "  🖥️  Local Access:  ${MC_BLUE}http://127.0.0.1:5000${MC_NC}"
echo -e "  📱 Network Access: ${MC_BLUE}http://$(hostname -I | awk '{print $1}'):5000${MC_NC}"
echo
echo -e "${MC_WHITE}[FEATURES]${MC_NC}"
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
echo -e "${MC_GREEN}[LAUNCH]${MC_NC} Starting Mission Control GUI..."
echo

# Launch the GUI
python3 nz7dev_gui.py 