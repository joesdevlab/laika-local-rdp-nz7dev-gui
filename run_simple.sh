#!/bin/bash

# NZ7DEV Remote Manager - Complete Edition Launcher
# Comprehensive RDP/VNC/SSH session manager with machine detection

echo "🚀 Starting NZ7DEV Remote Manager - Complete Edition"
echo "📋 Features:"
echo "   • Dynamic machine detection (Windows/Ubuntu/Linux)"
echo "   • RDP via xfreerdp (Windows desktop) - Custom resolution presets"
echo "   • VNC via Remmina (Ubuntu desktop) - Auto resolution"
echo "   • SSH via Kitty terminal (Linux/Ubuntu server)"
echo "   • Standard credentials (nz7dev/lemon)"
echo "   • Resolution presets management (RDP only)"
echo "   • Reference machines for demonstration"
echo "   • Dark mode interface"
echo ""

# Check if xfreerdp is installed
if ! command -v xfreerdp &> /dev/null; then
    echo "❌ xfreerdp is not installed!"
    echo "Install it with:"
    echo "  Ubuntu/Debian: sudo apt install freerdp2-x11"
    echo "  Arch Linux: sudo pacman -S freerdp"
    echo ""
fi

# Check if Remmina is installed
if ! command -v remmina &> /dev/null; then
    echo "❌ Remmina is not installed!"
    echo "Install it with:"
    echo "  Ubuntu/Debian: sudo apt install remmina"
    echo "  Arch Linux: sudo pacman -S remmina"
    echo ""
fi

# Check if Kitty terminal is installed
if ! command -v kitty &> /dev/null; then
    echo "❌ Kitty terminal is not installed!"
    echo "Install it with:"
    echo "  Ubuntu/Debian: sudo apt install kitty"
    echo "  Arch Linux: sudo pacman -S kitty"
    echo "  or visit: https://sw.kovidgoyal.net/kitty/"
    echo ""
fi

# Check for missing dependencies
missing_deps=false
if ! command -v xfreerdp &> /dev/null; then
    missing_deps=true
fi
if ! command -v remmina &> /dev/null; then
    missing_deps=true
fi
if ! command -v kitty &> /dev/null; then
    missing_deps=true
fi

if [ "$missing_deps" = true ]; then
    echo "Please install missing dependencies before continuing."
    echo "You can still use the application with available clients."
fi

# Check if Python dependencies are installed
if ! python3 -c "import flask" &> /dev/null; then
    echo "❌ Flask not installed!"
    echo "Install dependencies with: pip install -r requirements_simple.txt"
    exit 1
fi

# Launch the application
echo "🌐 Starting web interface on http://localhost:5001"
echo "🔍 Network scan will begin automatically"
echo "🎨 Dark mode interface enabled"
echo "📡 Scanning for RDP (3389), VNC (5900), SSH (22) services"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python3 nz7dev_rdp_simple.py 