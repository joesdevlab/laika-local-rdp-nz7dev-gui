#!/bin/bash

# NZ7DEV RDP Manager Service Control Script

SERVICE_NAME="nz7dev-rdp-manager.service"

case "$1" in
    start)
        echo "Starting NZ7DEV RDP Manager..."
        systemctl --user start $SERVICE_NAME
        ;;
    stop)
        echo "Stopping NZ7DEV RDP Manager..."
        systemctl --user stop $SERVICE_NAME
        ;;
    restart)
        echo "Restarting NZ7DEV RDP Manager..."
        systemctl --user restart $SERVICE_NAME
        ;;
    status)
        systemctl --user status $SERVICE_NAME
        ;;
    enable)
        echo "Enabling NZ7DEV RDP Manager to start automatically..."
        systemctl --user enable $SERVICE_NAME
        ;;
    disable)
        echo "Disabling NZ7DEV RDP Manager auto-start..."
        systemctl --user disable $SERVICE_NAME
        ;;
    logs)
        echo "Showing logs (press Ctrl+C to exit)..."
        journalctl --user -u $SERVICE_NAME -f
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|enable|disable|logs}"
        echo
        echo "  start    - Start the service"
        echo "  stop     - Stop the service"
        echo "  restart  - Restart the service"
        echo "  status   - Show service status"
        echo "  enable   - Enable auto-start at login"
        echo "  disable  - Disable auto-start"
        echo "  logs     - Show live logs"
        echo
        echo "The web interface will be available at: http://localhost:5001"
        exit 1
        ;;
esac