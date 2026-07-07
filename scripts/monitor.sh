#!/bin/bash
# scripts/monitor.sh
# AlphaEdge V13.0.5 – Monitoring Script
# Created: July 7, 2026

# ============================================
# CONFIGURATION
# ============================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs"
PID_FILE="$LOG_DIR/bot.pid"

# ============================================
# FUNCTIONS
# ============================================

print_header() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║                                                           ║"
    echo "║     ALPHAEDGE V13.0.5 – MONITORING SCRIPT                ║"
    echo "║                                                           ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

check_process() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Bot is RUNNING${NC} (PID: $PID)"
            return 0
        else
            echo -e "${RED}✗ Bot is STOPPED${NC} (PID file exists but process not found)"
            return 1
        fi
    else
        echo -e "${RED}✗ Bot is STOPPED${NC} (No PID file)"
        return 1
    fi
}

check_cpu() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        CPU=$(ps -p "$PID" -o %cpu= 2>/dev/null | tr -d ' ')
        if [ -n "$CPU" ]; then
            echo -e "  CPU: ${YELLOW}${CPU}%${NC}"
        else
            echo -e "  CPU: ${RED}N/A${NC}"
        fi
    fi
}

check_memory() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        MEM=$(ps -p "$PID" -o %mem= 2>/dev/null | tr -d ' ')
        if [ -n "$MEM" ]; then
            echo -e "  Memory: ${YELLOW}${MEM}%${NC}"
        else
            echo -e "  Memory: ${RED}N/A${NC}"
        fi
    fi
}

check_uptime() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        UPTIME=$(ps -p "$PID" -o etime= 2>/dev/null | tr -d ' ')
        if [ -n "$UPTIME" ]; then
            echo -e "  Uptime: ${GREEN}${UPTIME}${NC}"
        else
            echo -e "  Uptime: ${RED}N/A${NC}"
        fi
    fi
}

check_logs() {
    echo ""
    echo -e "${BLUE}Recent Logs:${NC}"
    echo -e "${YELLOW}----------------------------------------${NC}"
    
    if [ -f "$LOG_DIR/bot.log" ]; then
        tail -n 5 "$LOG_DIR/bot.log" | while read line; do
            if echo "$line" | grep -qi "error"; then
                echo -e "${RED}$line${NC}"
            elif echo "$line" | grep -qi "warning"; then
                echo -e "${YELLOW}$line${NC}"
            elif echo "$line" | grep -qi "success\|complete\|done"; then
                echo -e "${GREEN}$line${NC}"
            else
                echo "$line"
            fi
        done
    else
        echo -e "${RED}No log file found${NC}"
    fi
    
    echo -e "${YELLOW}----------------------------------------${NC}"
}

check_disk() {
    echo ""
    echo -e "${BLUE}Disk Usage:${NC}"
    df -h "$PROJECT_ROOT" | tail -1 | while read line; do
        echo "  $line"
    done
}

check_network() {
    echo ""
    echo -e "${BLUE}Network Status:${NC}"
    
    # Check RPC endpoints
    echo "  Checking RPC endpoints..."
    
    # Solana (Jito)
    if curl -s -o /dev/null -w "%{http_code}" https://mainnet.block-engine.jito.network/ --connect-timeout 2 | grep -q "200\|301\|302"; then
        echo -e "  ${GREEN}✓ Jito RPC: Online${NC}"
    else
        echo -e "  ${RED}✗ Jito RPC: Offline${NC}"
    fi
    
    # Helius
    if curl -s -o /dev/null -w "%{http_code}" https://rpc.helius.xyz/ --connect-timeout 2 | grep -q "200\|301\|302"; then
        echo -e "  ${GREEN}✓ Helius RPC: Online${NC}"
    else
        echo -e "  ${RED}✗ Helius RPC: Offline${NC}"
    fi
}

check_wallet() {
    echo ""
    echo -e "${BLUE}Gas Reserves:${NC}"
    
    # Read from config
    if [ -f "$PROJECT_ROOT/config/gas_config.yaml" ]; then
        grep -E "SOL:|ETH:|BNB:" "$PROJECT_ROOT/config/gas_config.yaml" | head -3 | while read line; do
            echo "  $line"
        done
    else
        echo -e "  ${RED}Gas config not found${NC}"
    fi
}

show_health_status() {
    echo ""
    echo -e "${BLUE}Health Check:${NC}"
    
    HEALTH_SCORE=0
    
    # Check process
    if check_process > /dev/null 2>&1; then
        HEALTH_SCORE=$((HEALTH_SCORE + 30))
        echo -e "  ${GREEN}✓ Process: Running${NC}"
    else
        echo -e "  ${RED}✗ Process: Stopped${NC}"
    fi
    
    # Check logs (last 50 lines for errors)
    if [ -f "$LOG_DIR/bot.log" ]; then
        ERROR_COUNT=$(tail -n 50 "$LOG_DIR/bot.log" | grep -ci "error" || echo "0")
        if [ "$ERROR_COUNT" -lt 2 ]; then
            HEALTH_SCORE=$((HEALTH_SCORE + 30))
            echo -e "  ${GREEN}✓ Logs: Low errors ($ERROR_COUNT)${NC}"
        else
            HEALTH_SCORE=$((HEALTH_SCORE + 10))
            echo -e "  ${YELLOW}⚠ Logs: $ERROR_COUNT errors in last 50 lines${NC}"
        fi
    else
        echo -e "  ${RED}✗ Logs: Not found${NC}"
    fi
    
    # Check disk space
    DISK_USAGE=$(df -h "$PROJECT_ROOT" | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$DISK_USAGE" -lt 80 ]; then
        HEALTH_SCORE=$((HEALTH_SCORE + 20))
        echo -e "  ${GREEN}✓ Disk: ${DISK_USAGE}% used${NC}"
    else
        HEALTH_SCORE=$((HEALTH_SCORE + 5))
        echo -e "  ${YELLOW}⚠ Disk: ${DISK_USAGE}% used${NC}"
    fi
    
    # Check RPC
    if curl -s -o /dev/null -w "%{http_code}" https://mainnet.block-engine.jito.network/ --connect-timeout 2 | grep -q "200\|301\|302"; then
        HEALTH_SCORE=$((HEALTH_SCORE + 20))
        echo -e "  ${GREEN}✓ RPC: Online${NC}"
    else
        echo -e "  ${RED}✗ RPC: Offline${NC}"
    fi
    
    # Show health score
    echo ""
    echo -e "${BLUE}Health Score:${NC} ${YELLOW}${HEALTH_SCORE}/100${NC}"
    
    if [ "$HEALTH_SCORE" -ge 80 ]; then
        echo -e "  ${GREEN}Status: Healthy${NC}"
    elif [ "$HEALTH_SCORE" -ge 50 ]; then
        echo -e "  ${YELLOW}Status: Degraded${NC}"
    else
        echo -e "  ${RED}Status: Critical${NC}"
    fi
}

show_summary() {
    echo ""
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗"
    echo -e "║                                                           ║"
    
    if check_process > /dev/null 2>&1; then
        echo -e "║     ✅ ALPHAEDGE IS RUNNING                              ║"
    else
        echo -e "║     ⛔ ALPHAEDGE IS STOPPED                              ║"
    fi
    
    echo -e "║                                                           ║"
    echo -e "║     Time:    $(date)                          ║"
    echo -e "║     PID:     $(cat "$PID_FILE" 2>/dev/null || echo 'N/A')                              ║"
    echo -e "║                                                           ║"
    echo -e "║     Commands:                                             ║"
    echo -e "║     ./scripts/monitor.sh  - Check status                ║"
    echo -e "║     ./scripts/backup.sh   - Backup state                ║"
    echo -e "║     ./scripts/update.sh   - Update code                 ║"
    echo -e "║                                                           ║"
    echo -e "╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# ============================================
# MAIN EXECUTION
# ============================================

main() {
    print_header
    
    echo ""
    echo -e "${BLUE}System Status:${NC}"
    echo -e "${YELLOW}----------------------------------------${NC}"
    
    check_process
    check_cpu
    check_memory
    check_uptime
    
    check_logs
    check_disk
    check_network
    check_wallet
    show_health_status
    
    show_summary
}

main "$@"
