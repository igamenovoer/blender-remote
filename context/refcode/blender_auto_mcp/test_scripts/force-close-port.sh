#!/bin/bash
# Shell script to forcefully close processes using a specified port
# This script requires sudo privileges

set -e

# Default values
FORCE=false
PORT=""

# Function to show usage
show_usage() {
    echo "Usage: $0 <port> [--force]"
    echo ""
    echo "Arguments:"
    echo "  <port>     Port number to check and close (1-65535)"
    echo "  --force    Actually terminate the processes (without this, only shows what would be done)"
    echo ""
    echo "Examples:"
    echo "  $0 10080              # Show processes using port 10080"
    echo "  $0 10080 --force      # Terminate processes using port 10080"
    echo "  sudo $0 9876 --force  # Terminate processes using port 9876 with sudo"
    echo ""
    echo "Note: This script may require sudo privileges to terminate processes owned by other users."
}

# Function to check if running with sufficient privileges
check_privileges() {
    if [[ $EUID -ne 0 ]] && [[ "$FORCE" == true ]]; then
        echo "⚠️  Warning: Not running as root. You may need sudo privileges to terminate processes owned by other users."
        echo "   If you encounter permission errors, try: sudo $0 $PORT --force"
        echo ""
    fi
}

# Function to validate port number
validate_port() {
    if ! [[ "$PORT" =~ ^[0-9]+$ ]] || [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
        echo "❌ Error: Port number must be between 1 and 65535"
        exit 1
    fi
}

# Function to find processes using the port
find_processes_using_port() {
    local port=$1
    local results=()
    
    # Try different methods to find processes using the port
    
    # Method 1: lsof (if available)
    if command -v lsof >/dev/null 2>&1; then
        echo "🔍 Scanning for processes using port $port (using lsof)..."
        local lsof_output
        lsof_output=$(lsof -i :$port 2>/dev/null || true)
        
        if [[ -n "$lsof_output" ]]; then
            echo "📋 lsof output:"
            echo "$lsof_output"
            echo ""
            
            # Extract PIDs from lsof output (skip header line)
            local pids
            pids=$(echo "$lsof_output" | awk 'NR>1 {print $2}' | sort -u)
            
            for pid in $pids; do
                if [[ "$pid" =~ ^[0-9]+$ ]]; then
                    results+=("$pid")
                fi
            done
        fi
    fi
    
    # Method 2: netstat + ps (fallback)
    if [[ ${#results[@]} -eq 0 ]] && command -v netstat >/dev/null 2>&1; then
        echo "🔍 Scanning for processes using port $port (using netstat)..."
        local netstat_output
        netstat_output=$(netstat -tlnp 2>/dev/null | grep ":$port " || true)
        
        if [[ -n "$netstat_output" ]]; then
            echo "📋 netstat output:"
            echo "$netstat_output"
            echo ""
            
            # Extract PIDs from netstat output
            local pids
            pids=$(echo "$netstat_output" | sed -n 's/.*LISTEN[[:space:]]*\([0-9]*\)\/.*/\1/p' | sort -u)
            
            for pid in $pids; do
                if [[ "$pid" =~ ^[0-9]+$ ]]; then
                    results+=("$pid")
                fi
            done
        fi
    fi
    
    # Method 3: ss (systemd systems)
    if [[ ${#results[@]} -eq 0 ]] && command -v ss >/dev/null 2>&1; then
        echo "🔍 Scanning for processes using port $port (using ss)..."
        local ss_output
        ss_output=$(ss -tlnp src :$port 2>/dev/null || true)
        
        if [[ -n "$ss_output" ]]; then
            echo "📋 ss output:"
            echo "$ss_output"
            echo ""
            
            # Extract PIDs from ss output
            local pids
            pids=$(echo "$ss_output" | grep -o 'pid=[0-9]*' | cut -d= -f2 | sort -u)
            
            for pid in $pids; do
                if [[ "$pid" =~ ^[0-9]+$ ]]; then
                    results+=("$pid")
                fi
            done
        fi
    fi
    
    # Return results
    printf '%s\n' "${results[@]}"
}

# Function to get process info
get_process_info() {
    local pid=$1
    local cmd=""
    local user=""
    
    if [[ -f "/proc/$pid/cmdline" ]]; then
        cmd=$(cat /proc/$pid/cmdline 2>/dev/null | tr '\0' ' ' | sed 's/[[:space:]]*$//')
        if [[ -z "$cmd" ]]; then
            cmd=$(cat /proc/$pid/comm 2>/dev/null || echo "unknown")
        fi
    elif command -v ps >/dev/null 2>&1; then
        cmd=$(ps -p $pid -o comm= 2>/dev/null || echo "unknown")
    else
        cmd="unknown"
    fi
    
    if command -v ps >/dev/null 2>&1; then
        user=$(ps -p $pid -o user= 2>/dev/null | tr -d ' ' || echo "unknown")
    else
        user="unknown"
    fi
    
    echo "user:$user cmd:$cmd"
}

# Function to terminate process
terminate_process() {
    local pid=$1
    local info=$2
    
    echo "  🔥 Attempting to terminate PID $pid..."
    
    # Try SIGTERM first (graceful)
    if kill -TERM "$pid" 2>/dev/null; then
        echo "  ✅ Sent SIGTERM to PID $pid"
        
        # Wait a bit and check if process is still running
        sleep 2
        if kill -0 "$pid" 2>/dev/null; then
            echo "  ⚠️  Process $pid still running, sending SIGKILL..."
            if kill -KILL "$pid" 2>/dev/null; then
                echo "  ✅ Sent SIGKILL to PID $pid"
            else
                echo "  ❌ Failed to send SIGKILL to PID $pid (permission denied?)"
                return 1
            fi
        else
            echo "  ✅ Process $pid terminated gracefully"
        fi
    else
        echo "  ❌ Failed to terminate PID $pid (permission denied or process not found)"
        return 1
    fi
    
    return 0
}

# Parse command line arguments
if [[ $# -eq 0 ]]; then
    show_usage
    exit 1
fi

PORT="$1"
shift

while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo "❌ Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate arguments
validate_port
check_privileges

echo "🚀 Force Close Port Script"
echo "Port: $PORT"
echo "Force mode: $FORCE"
echo ""

# Find processes using the port
mapfile -t pids < <(find_processes_using_port "$PORT")

if [[ ${#pids[@]} -eq 0 ]]; then
    echo "✅ No processes found using port $PORT"
    exit 0
fi

echo "🔍 Found ${#pids[@]} process(es) using port $PORT:"
echo ""

# Show process information
declare -A process_info
for pid in "${pids[@]}"; do
    if kill -0 "$pid" 2>/dev/null; then
        info=$(get_process_info "$pid")
        process_info["$pid"]="$info"
        
        user=$(echo "$info" | cut -d' ' -f1 | cut -d: -f2)
        cmd=$(echo "$info" | cut -d' ' -f2- | cut -d: -f2)
        
        echo "  📋 PID: $pid"
        echo "      User: $user"
        echo "      Command: $cmd"
        echo ""
    else
        echo "  📋 PID: $pid (process no longer exists)"
        echo ""
    fi
done

if [[ "$FORCE" == true ]]; then
    echo "🔥 Terminating processes..."
    echo ""
    
    success_count=0
    for pid in "${pids[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            if terminate_process "$pid" "${process_info[$pid]}"; then
                ((success_count++))
            fi
            echo ""
        else
            echo "  ℹ️  PID $pid already terminated"
            echo ""
        fi
    done
    
    echo "📊 Summary: Successfully terminated $success_count out of ${#pids[@]} processes"
    echo ""
    
    # Verify port is now free
    echo "🔍 Verifying port $PORT is now free..."
    sleep 2
    
    mapfile -t remaining_pids < <(find_processes_using_port "$PORT")
    if [[ ${#remaining_pids[@]} -eq 0 ]]; then
        echo "✅ Port $PORT is now free!"
    else
        echo "⚠️  Warning: Port $PORT may still be in use by ${#remaining_pids[@]} process(es)"
    fi
else
    echo "ℹ️  Dry run mode - no processes were terminated."
    echo ""
    echo "To actually terminate these processes, run:"
    echo "  $0 $PORT --force"
    echo ""
    echo "⚠️  WARNING: This will forcefully terminate processes and may cause data loss!"
fi

echo ""
echo "✅ Script completed."