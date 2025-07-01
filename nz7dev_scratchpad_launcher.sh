#!/usr/bin/env bash
# NZ7DEV Scratchpad Launcher - All 6 RDP sessions tiled across scratchpad on workspace 2

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

echo_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
echo_success() { echo -e "${GREEN}[OK]${NC} $1"; }
echo_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# VM Configuration: name:ip:user:pass:os (geometry will be calculated for ultrawide tiling)
VM_LIST=(
    "vm20:192.168.1.20:nz7dev:lemonlime:win10"
    "vm21:192.168.1.21:nz7dev:lemonlime:win11"
    "vm23:192.168.1.23:User:lemonlime:win10"
    "vm24:192.168.1.24:nz7dev:lemonlime:win10"
    "vm25:192.168.1.25:User:lemonlime:win10"
    "vm26:192.168.1.26:User:lemonlime:win10"
)

# Ultrawide 3440x1440 tiling configuration with waybar
# 6 windows in 3x2 grid: account for 34px waybar at top
readonly ULTRAWIDE_WIDTH=3440
readonly ULTRAWIDE_HEIGHT=1440
readonly WAYBAR_HEIGHT=40
readonly USABLE_HEIGHT=$((ULTRAWIDE_HEIGHT - WAYBAR_HEIGHT))  # 1400px usable
readonly TILE_COLS=3
readonly TILE_ROWS=2
readonly WINDOW_WIDTH=$((ULTRAWIDE_WIDTH / TILE_COLS))        # 1146px (exact third)
readonly WINDOW_HEIGHT=$((USABLE_HEIGHT / TILE_ROWS))         # 700px (half of usable height)
readonly WINDOW_GEOMETRY="${WINDOW_WIDTH}x${WINDOW_HEIGHT}"

echo_info "Ultrawide tiling with waybar: ${TILE_COLS}x${TILE_ROWS} grid, each window: ${WINDOW_GEOMETRY} (34px waybar offset)"

test_connectivity() {
    local ip=$1
    local os_type=$2
    
    # Standard ping test
    if timeout 3 ping -c 1 "$ip" &>/dev/null; then
        return 0
    fi
    
    # For Windows 11, try RDP port test
    if [[ "$os_type" == "win11" ]]; then
        if command -v nc &>/dev/null && timeout 3 nc -z "$ip" 3389 &>/dev/null; then
            return 0
        fi
    fi
    
    return 1
}

launch_rdp() {
    local name=$1
    local ip=$2
    local user=$3
    local pass=$4
    local os_type=$5
    
    # Use calculated ultrawide geometry for all windows
    local geometry="$WINDOW_GEOMETRY"
    
    echo_info "  → Using ultrawide tiling geometry: $geometry"
    
    # Basic RDP arguments
    local args=(
        "/u:$user"
        "/p:$pass"
        "/v:$ip"
        "/size:$geometry"
        "/auto-reconnect"
        "+fonts"
        "+clipboard"
        "+heartbeat"
        "/cert:ignore"
        "/log-level:ERROR"
    )
    
    # OS-specific settings
    if [[ "$os_type" == "win11" ]]; then
        args+=(
            "/gfx:AVC444"
            "/rfx"
            "+aero"
            "+window-drag"
            "+menu-anims"
        )
    else
        args+=(
            "/gfx:RFX"
        )
    fi
    
    # Launch with systemd
    systemd-run --user \
        --unit="nz7dev-$name" \
        --collect \
        /usr/bin/xfreerdp "${args[@]}" &>/dev/null &
    
    return $?
}

position_scratchpad_windows() {
    echo_info "Positioning all windows in 3x2 ultrawide grid on scratchpad workspace 2..."
    
    # Switch to workspace 2 first
    hyprctl dispatch workspace 2 &>/dev/null
    sleep 0.5
    
    local positioned=0
    local window_count=0
    
    # Count available windows first
    for vm_data in "${VM_LIST[@]}"; do
        IFS=':' read -r name ip user pass os_type <<< "$vm_data"
        local window_title="FreeRDP: $ip"
        
        if hyprctl clients 2>/dev/null | grep -q "title: $window_title"; then
            ((window_count++))
        fi
    done
    
    echo_info "Found $window_count RDP windows to position in ${TILE_COLS}x${TILE_ROWS} ultrawide grid"
    
    # Calculate window positions for perfect 3x2 grid (accounting for 34px waybar)
    local positions=(
        "0,34"             # Top-left (below waybar)
        "1146,34"          # Top-center (1/3 width, below waybar)
        "2293,34"          # Top-right (2/3 width, below waybar)
        "0,734"            # Bottom-left (waybar + half usable height)
        "1146,734"         # Bottom-center
        "2293,734"         # Bottom-right
    )
    
    local pos_index=0
    
    # Position each window
    for vm_data in "${VM_LIST[@]}"; do
        IFS=':' read -r name ip user pass os_type <<< "$vm_data"
        local window_title="FreeRDP: $ip"
        
        echo -ne "${CYAN}Positioning $name in ultrawide grid...${NC} "
        
        # Check if window exists
        if hyprctl clients 2>/dev/null | grep -q "title: $window_title"; then
            
            # Focus the window
            if hyprctl dispatch focuswindow "title:$window_title" &>/dev/null; then
                sleep 0.3
                
                # Move to scratchpad first
                hyprctl dispatch movetoworkspace special &>/dev/null
                sleep 0.5
                
                # Get position for this window
                local position="${positions[$pos_index]}"
                local x_pos=$(echo "$position" | cut -d',' -f1)
                local y_pos=$(echo "$position" | cut -d',' -f2)
                
                # Move back to workspace 2 so it shows on the scratchpad overlay
                hyprctl dispatch workspace 2 &>/dev/null
                sleep 0.3
                
                # Toggle scratchpad to show the window on workspace 2
                hyprctl dispatch togglespecialworkspace &>/dev/null
                sleep 0.3
                
                # Focus the window again after togglespecialworkspace
                hyprctl dispatch focuswindow "title:$window_title" &>/dev/null
                sleep 0.2
                
                # Position the window precisely in the grid
                hyprctl dispatch moveactive "$x_pos" "$y_pos" &>/dev/null
                sleep 0.2
                
                # Resize to exact ultrawide tile size
                hyprctl dispatch resizeactive "exact $WINDOW_WIDTH $WINDOW_HEIGHT" &>/dev/null
                sleep 0.2
                
                local grid_pos="$((pos_index % TILE_COLS + 1)),$((pos_index / TILE_COLS + 1))"
                echo -e "${GREEN}→ Grid position $grid_pos (${x_pos},${y_pos})${NC}"
                ((positioned++))
                ((pos_index++))
            else
                echo -e "${YELLOW}Focus failed${NC}"
            fi
        else
            echo -e "${YELLOW}Window not found${NC}"
        fi
        
        sleep 0.4
    done
    
    # Final adjustment - ensure we're on workspace 2 with scratchpad visible
    hyprctl dispatch workspace 2 &>/dev/null
    sleep 0.3
    
    # If scratchpad is not visible, toggle it on
    local scratchpad_visible=$(hyprctl workspaces -j 2>/dev/null | grep -c '"special"' || echo "0")
    if [[ "$scratchpad_visible" -eq 0 ]]; then
        hyprctl dispatch togglespecialworkspace &>/dev/null
    fi
    
    echo_success "Positioned $positioned windows in perfect ${TILE_COLS}x${TILE_ROWS} grid below waybar"
    echo_info "Perfect tiling for 3440x1440 ultrawide with 34px waybar!"
    echo_info "Each window: ${WINDOW_GEOMETRY} positioned below waybar"
}

scratchpad_launch() {
    echo -e "${PURPLE}🚀 NZ7DEV SCRATCHPAD LAUNCHER 🚀${NC}"
    echo -e "${CYAN}All 6 RDP sessions → Scratchpad on Workspace 2${NC}"
    echo
    
    echo_info "Starting RDP connections..."
    
    local connected=0
    local total=${#VM_LIST[@]}
    
    # Launch all RDP connections
    for vm_data in "${VM_LIST[@]}"; do
        IFS=':' read -r name ip user pass os_type <<< "$vm_data"
        
        echo -ne "${BLUE}Testing $name ($ip) [$os_type]...${NC} "
        
        if test_connectivity "$ip" "$os_type"; then
            echo -e "${GREEN}ONLINE${NC}"
            
            if launch_rdp "$name" "$ip" "$user" "$pass" "$os_type"; then
                echo_success "Started RDP to $name (${WINDOW_GEOMETRY})"
                ((connected++))
            else
                echo_error "Failed to start RDP to $name"
            fi
        else
            echo -e "${RED}OFFLINE${NC}"
            echo_warn "Skipping $name (unreachable)"
        fi
        
        sleep 0.5
    done
    
    if [[ $connected -eq 0 ]]; then
        echo_error "No connections established"
        return 1
    fi
    
    echo
    echo_success "Started $connected/$total RDP connections"
    
    # Wait for windows to appear
    echo_info "Waiting 10 seconds for windows to appear..."
    for i in {10..1}; do
        echo -ne "\r${CYAN}Scratchpad positioning in ${i}s...${NC}"
        sleep 1
    done
    echo
    
    # Position all windows on scratchpad
    position_scratchpad_windows
    
    echo
    echo_success "✅ Scratchpad launch complete!"
    echo_info "💡 All RDP windows are on scratchpad workspace 2"
    echo_info "💡 Use SUPER+S or togglespecialworkspace to show/hide"
    echo_info "💡 Use mouse or SUPER+arrow keys to navigate between windows"
}

stop_all() {
    echo_info "Stopping all RDP connections..."
    
    # Stop systemd services
    systemctl --user stop 'nz7dev-*.service' 2>/dev/null || true
    
    # Kill remaining processes
    pkill -f "xfreerdp.*192\.168\.1\." 2>/dev/null || true
    sleep 2
    pkill -9 -f "xfreerdp.*192\.168\.1\." 2>/dev/null || true
    
    echo_success "All connections stopped"
}

show_status() {
    echo -e "${PURPLE}🚀 NZ7DEV SCRATCHPAD STATUS 🚀${NC}"
    echo
    
    echo_info "RDP Services:"
    systemctl --user list-units 'nz7dev-*.service' --no-legend 2>/dev/null | while read -r line; do
        if [[ "$line" == *".service"* ]]; then
            local service=$(echo "$line" | awk '{print $1}')
            local status=$(echo "$line" | awk '{print $3}')
            if [[ "$status" == "active" ]]; then
                echo -e "  ${GREEN}●${NC} $service"
            else
                echo -e "  ${RED}●${NC} $service ($status)"
            fi
        fi
    done
    
    echo
    echo_info "Connectivity:"
    for vm_data in "${VM_LIST[@]}"; do
        IFS=':' read -r name ip user pass os_type <<< "$vm_data"
        
        echo -ne "  $name ($ip): "
        if test_connectivity "$ip" "$os_type"; then
            echo -e "${GREEN}ONLINE${NC}"
        else
            echo -e "${RED}OFFLINE${NC}"
        fi
    done
    
    echo
    echo_info "Window Status on Ultrawide Scratchpad:"
    for vm_data in "${VM_LIST[@]}"; do
        IFS=':' read -r name ip user pass os_type <<< "$vm_data"
        local window_title="FreeRDP: $ip"
        
        echo -ne "  $name: "
        if command -v hyprctl >/dev/null 2>&1 && hyprctl clients 2>/dev/null | grep -q "title: $window_title"; then
            # Check if window is on special workspace
            local window_workspace=$(hyprctl clients -j 2>/dev/null | jq -r ".[] | select(.title == \"$window_title\") | .workspace.name" 2>/dev/null || echo "unknown")
            if [[ "$window_workspace" == "special" ]]; then
                echo -e "${GREEN}On Scratchpad (${WINDOW_GEOMETRY})${NC}"
            else
                echo -e "${YELLOW}Active (WS: $window_workspace)${NC}"
            fi
        else
            echo -e "${RED}No Window${NC}"
        fi
    done
    
    echo
    echo_info "Ultrawide Tiling Info:"
    echo -e "  ${BLUE}●${NC} Display: 3440x1440 ultrawide"
    echo -e "  ${BLUE}●${NC} Waybar: 34px at top"
    echo -e "  ${BLUE}●${NC} Usable area: 3440x1400"
    echo -e "  ${BLUE}●${NC} Grid: ${TILE_COLS}x${TILE_ROWS} (6 windows)"
    echo -e "  ${BLUE}●${NC} Window size: ${WINDOW_GEOMETRY}"
    local scratchpad_visible=$(hyprctl workspaces -j 2>/dev/null | grep -c '"special"' || echo "0")
    if [[ "$scratchpad_visible" -gt 0 ]]; then
        echo -e "  ${GREEN}●${NC} Scratchpad is currently visible"
    else
        echo -e "  ${YELLOW}●${NC} Scratchpad is currently hidden"
    fi
    echo -e "  ${BLUE}●${NC} Current workspace: $(hyprctl activeworkspace -j 2>/dev/null | jq -r '.id' 2>/dev/null || echo 'unknown')"
}

show_help() {
    cat << 'EOF'
🚀 NZ7DEV Scratchpad Launcher

DESCRIPTION:
    Launches all 6 RDP sessions and tiles them in a perfect 3x2 grid
    across the scratchpad on workspace 2, optimized for 3440x1440 ultrawide.

USAGE:
    nz7dev-scratchpad {launch|stop|status|help}

COMMANDS:
    launch    Start all RDP connections + position in 3x2 ultrawide grid
    stop      Stop all connections
    status    Show current status and ultrawide tiling info
    help      Show this help

ULTRAWIDE TILING (3440x1440 with waybar):
    Waybar: 34px at top
    Usable area: 3440x1400 (below waybar)
    Grid Layout: 3x2 (6 windows, edge-to-edge)
    Window Size: 1146x700 each
    
    ┌─────────────────────────────────────┐ ← waybar (34px)
    ┌─────────┬─────────┬─────────┐
    │   vm20  │   vm21  │   vm23  │  ← Top row (y: 40)
    ├─────────┼─────────┼─────────┤
    │   vm24  │   vm25  │   vm26  │  ← Bottom row (y: 740)
    └─────────┴─────────┴─────────┘
    x: 0      x: 1146   x: 2293

MACHINES (All → 3x2 Grid on Scratchpad):
    vm20 (192.168.1.20) - Windows 10 → Top-left
    vm21 (192.168.1.21) - Windows 11 → Top-center  
    vm23 (192.168.1.23) - Windows 10 → Top-right
    vm24 (192.168.1.24) - Windows 10 → Bottom-left
    vm25 (192.168.1.25) - Windows 10 → Bottom-center
    vm26 (192.168.1.26) - Windows 10 → Bottom-right

SCRATCHPAD CONTROLS:
    SUPER+S                    Toggle scratchpad visibility
    SUPER+Arrow Keys           Navigate between windows
    Mouse Click                Focus specific window
    
WORKFLOW:
    1. All RDP sessions launch
    2. All windows move to scratchpad
    3. Scratchpad shows on workspace 2
    4. Toggle scratchpad on/off as needed

EXAMPLES:
    nz7dev-scratchpad launch     # Start everything on scratchpad
    nz7dev-scratchpad status     # Check scratchpad status
    nz7dev-scratchpad stop       # Stop everything

💡 All windows will be tiled across the scratchpad overlay on workspace 2!

EOF
}

# Main command handler
case "${1:-help}" in
    launch|start|fastup|up)
        scratchpad_launch
        ;;
    stop|down|kill)
        stop_all
        ;;
    status|list)
        show_status
        ;;
    help|--help|-h|"")
        show_help
        ;;
    *)
        echo_error "Unknown command: $1"
        echo "Use 'nz7dev-scratchpad help' for available commands"
        exit 1
        ;;
esac