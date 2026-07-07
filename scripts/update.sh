#!/bin/bash
# scripts/update.sh
# AlphaEdge V13.0.5 – Update Script
# Created: July 7, 2026

# ============================================
# CONFIGURATION
# ============================================

set -e

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
    echo "║     ALPHAEDGE V13.0.5 – UPDATE SCRIPT                    ║"
    echo "║                                                           ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "${GREEN}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

stop_bot() {
    print_step "Stopping bot..."
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            kill "$PID"
            sleep 2
            
            # Force kill if still running
            if ps -p "$PID" > /dev/null 2>&1; then
                kill -9 "$PID"
            fi
            
            rm -f "$PID_FILE"
            print_success "Bot stopped"
        else
            rm -f "$PID_FILE"
            print_warning "Bot was not running"
        fi
    else
        print_warning "Bot not running"
    fi
}

backup_current() {
    print_step "Creating backup before update..."
    
    cd "$PROJECT_ROOT"
    
    DATE=$(date +"%Y%m%d_%H%M%S")
    BACKUP_DIR="$PROJECT_ROOT/backups/pre_update_$DATE"
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup config
    if [ -d "config" ]; then
        cp -r config/ "$BACKUP_DIR/config/"
        print_success "Config backed up"
    fi
    
    # Backup data
    if [ -d "data" ]; then
        cp -r data/ "$BACKUP_DIR/data/"
        print_success "Data backed up"
    fi
    
    # Backup requirements
    if [ -f "requirements.txt" ]; then
        cp requirements.txt "$BACKUP_DIR/requirements.txt"
        print_success "Requirements backed up"
    fi
    
    print_success "Backup created at: $BACKUP_DIR"
}

pull_updates() {
    print_step "Pulling updates from GitHub..."
    
    cd "$PROJECT_ROOT"
    
    # Check if git repository
    if [ ! -d ".git" ]; then
        print_error "Not a git repository"
        exit 1
    fi
    
    # Fetch updates
    git fetch origin
    
    # Check for updates
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse origin/main)
    
    if [ "$LOCAL" = "$REMOTE" ]; then
        print_warning "Already up to date"
        return 0
    fi
    
    # Pull updates
    git pull origin main
    
    print_success "Updates pulled"
}

update_dependencies() {
    print_step "Updating dependencies..."
    
    cd "$PROJECT_ROOT"
    
    if [ -f "requirements.txt" ]; then
        # Backup old requirements
        cp requirements.txt requirements.txt.bak
        
        # Update pip
        pip install --upgrade pip
        
        # Install dependencies
        pip install -r requirements.txt --upgrade
        
        print_success "Dependencies updated"
    else
        print_warning "No requirements.txt found"
    fi
}

update_config() {
    print_step "Checking config files..."
    
    cd "$PROJECT_ROOT"
    
    # Check if new config files need to be merged
    if [ -d "config" ]; then
        # Check for new config files
        for file in config/*.yaml; do
            if [ -f "$file" ]; then
                # Check if file has been modified since last update
                if ! grep -q "# V13.0.5" "$file" 2>/dev/null; then
                    print_warning "Config file may need manual update: $file"
                fi
            fi
        done
    fi
}

run_migrations() {
    print_step "Running migrations..."
    
    cd "$PROJECT_ROOT"
    
    # Run Python migrations if any
    if [ -f "scripts/migrate.py" ]; then
        python3 scripts/migrate.py
        print_success "Migrations run"
    else
        print_success "No migrations needed"
    fi
}

start_bot() {
    print_step "Starting bot..."
    
    cd "$PROJECT_ROOT"
    
    # Activate virtual environment
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Start bot
    python3 main.py &
    
    # Save PID
    echo $! > "$PID_FILE"
    
    print_success "Bot started (PID: $(cat $PID_FILE))"
}

show_summary() {
    echo ""
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗"
    echo -e "║                                                           ║"
    echo -e "║     ✅ UPDATE COMPLETE!                                   ║"
    echo -e "║                                                           ║"
    echo -e "║     AlphaEdge V13.0.5 updated successfully               ║"
    echo -e "║                                                           ║"
    echo -e "║     Backup:  $BACKUP_DIR                                 ║"
    echo -e "║     PID:     $(cat "$PID_FILE" 2>/dev/null || echo 'N/A')       ║"
    echo -e "║                                                           ║"
    echo -e "║     Verify:  ./scripts/monitor.sh                       ║"
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
    echo -e "${YELLOW}This will update AlphaEdge V13.0.5${NC}"
    echo ""
    echo -e "${YELLOW}WARNING: Bot will be stopped during update${NC}"
    echo ""
    
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Update cancelled"
        exit 1
    fi
    
    stop_bot
    backup_current
    pull_updates
    update_dependencies
    update_config
    run_migrations
    start_bot
    show_summary
}

main "$@"
