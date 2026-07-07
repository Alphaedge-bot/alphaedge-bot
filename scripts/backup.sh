#!/bin/bash
# scripts/backup.sh
# AlphaEdge V13.0.5 – Backup Script
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
BACKUP_DIR="$PROJECT_ROOT/backups"
DATA_DIR="$PROJECT_ROOT/data"
LOGS_DIR="$PROJECT_ROOT/logs"

# Date format
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="alphaedge_backup_$DATE"

# ============================================
# FUNCTIONS
# ============================================

print_header() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║                                                           ║"
    echo "║     ALPHAEDGE V13.0.5 – BACKUP SCRIPT                    ║"
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

create_backup_dir() {
    print_step "Creating backup directory..."
    
    if [ ! -d "$BACKUP_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
        print_success "Backup directory created"
    else
        print_success "Backup directory exists"
    fi
}

backup_config() {
    print_step "Backing up configuration..."
    
    cd "$PROJECT_ROOT"
    
    if [ -d "config" ]; then
        tar -czf "$BACKUP_DIR/${BACKUP_NAME}_config.tar.gz" config/
        print_success "Config backed up"
    else
        print_warning "Config directory not found"
        return 1
    fi
}

backup_data() {
    print_step "Backing up data..."
    
    cd "$PROJECT_ROOT"
    
    if [ -d "$DATA_DIR" ] && [ "$(ls -A $DATA_DIR 2>/dev/null)" ]; then
        tar -czf "$BACKUP_DIR/${BACKUP_NAME}_data.tar.gz" data/
        print_success "Data backed up"
    else
        print_warning "No data to backup"
    fi
}

backup_logs() {
    print_step "Backing up logs..."
    
    cd "$PROJECT_ROOT"
    
    if [ -d "$LOGS_DIR" ] && [ "$(ls -A $LOGS_DIR 2>/dev/null)" ]; then
        tar -czf "$BACKUP_DIR/${BACKUP_NAME}_logs.tar.gz" logs/
        print_success "Logs backed up"
    else
        print_warning "No logs to backup"
    fi
}

backup_state() {
    print_step "Backing up state..."
    
    cd "$PROJECT_ROOT"
    
    # Check for state file
    if [ -f "$DATA_DIR/state.json" ]; then
        cp "$DATA_DIR/state.json" "$BACKUP_DIR/${BACKUP_NAME}_state.json"
        print_success "State backed up"
    else
        print_warning "No state file found"
    fi
}

create_manifest() {
    print_step "Creating backup manifest..."
    
    cat > "$BACKUP_DIR/${BACKUP_NAME}_manifest.txt" << EOF
AlphaEdge Backup Manifest
=========================
Date: $DATE
Backup Name: $BACKUP_NAME

Contents:
- Config files
- Data files
- Logs (if present)
- State (if present)

Checksums:
$(cd "$BACKUP_DIR" && sha256sum ${BACKUP_NAME}_* 2>/dev/null)
EOF
    
    print_success "Manifest created"
}

compress_backup() {
    print_step "Compressing backup..."
    
    cd "$BACKUP_DIR"
    
    # Create single archive of all backup files
    tar -czf "${BACKUP_NAME}.tar.gz" ${BACKUP_NAME}_* 2>/dev/null || true
    
    # Remove individual files
    rm -f ${BACKUP_NAME}_config.tar.gz \
          ${BACKUP_NAME}_data.tar.gz \
          ${BACKUP_NAME}_logs.tar.gz \
          ${BACKUP_NAME}_state.json \
          ${BACKUP_NAME}_manifest.txt
    
    print_success "Backup compressed: ${BACKUP_NAME}.tar.gz"
}

cleanup_old_backups() {
    print_step "Cleaning up old backups..."
    
    cd "$BACKUP_DIR"
    
    # Keep last 30 backups
    ls -t *.tar.gz 2>/dev/null | tail -n +31 | xargs -r rm -f
    
    print_success "Old backups cleaned (kept last 30)"
}

show_summary() {
    echo ""
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗"
    echo -e "║                                                           ║"
    echo -e "║     ✅ BACKUP COMPLETE!                                   ║"
    echo -e "║                                                           ║"
    echo -e "║     Backup:  $BACKUP_NAME.tar.gz                          ║"
    echo -e "║     Size:    $(du -h "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" 2>/dev/null | cut -f1)           ║"
    echo -e "║     Path:    $BACKUP_DIR                                 ║"
    echo -e "║                                                           ║"
    echo -e "╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# ============================================
# MAIN EXECUTION
# ============================================

main() {
    print_header
    
    create_backup_dir
    backup_config
    backup_data
    backup_logs
    backup_state
    create_manifest
    compress_backup
    cleanup_old_backups
    show_summary
}

main "$@"
