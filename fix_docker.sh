#!/bin/bash

# Script pour réparer les permissions Docker
# Log file: fix_docker.log

LOG_FILE="/home/samir/Bureau/Projet_encheres/fix_docker.log"
USER=$(whoami)

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Clear previous log
> "$LOG_FILE"

log "=========================================="
log "🔧 Docker Permission Fix Script"
log "=========================================="
log "User: $USER"
log ""

# Check if docker group exists
log "Step 1: Checking if docker group exists..."
if getent group docker > /dev/null 2>&1; then
    log "✅ Docker group exists"
else
    log "❌ Docker group does not exist"
    log "Creating docker group..."
    sudo groupadd docker 2>&1 | tee -a "$LOG_FILE"
    if [ $? -eq 0 ]; then
        log "✅ Docker group created successfully"
    else
        log "❌ Failed to create docker group"
        exit 1
    fi
fi

# Check if user is in docker group
log ""
log "Step 2: Checking if user $USER is in docker group..."
if groups $USER | grep -q docker; then
    log "✅ User $USER is already in docker group"
else
    log "⚠️  User $USER is NOT in docker group"
    log "Adding user $USER to docker group..."
    sudo usermod -aG docker $USER 2>&1 | tee -a "$LOG_FILE"
    if [ $? -eq 0 ]; then
        log "✅ User $USER added to docker group successfully"
    else
        log "❌ Failed to add user to docker group"
        exit 1
    fi
fi

# Fix docker socket permissions
log ""
log "Step 3: Fixing docker socket permissions..."
if [ -e /var/run/docker.sock ]; then
    log "Docker socket exists at /var/run/docker.sock"
    log "Current permissions:"
    ls -l /var/run/docker.sock 2>&1 | tee -a "$LOG_FILE"

    log "Changing ownership and permissions..."
    sudo chown root:docker /var/run/docker.sock 2>&1 | tee -a "$LOG_FILE"
    sudo chmod 660 /var/run/docker.sock 2>&1 | tee -a "$LOG_FILE"

    log "New permissions:"
    ls -l /var/run/docker.sock 2>&1 | tee -a "$LOG_FILE"
    log "✅ Docker socket permissions fixed"
else
    log "⚠️  Docker socket not found at /var/run/docker.sock"
fi

# Check Docker service status
log ""
log "Step 4: Checking Docker service status..."
sudo systemctl status docker --no-pager 2>&1 | tee -a "$LOG_FILE"

if sudo systemctl is-active --quiet docker; then
    log "✅ Docker service is running"
else
    log "⚠️  Docker service is not running"
    log "Starting Docker service..."
    sudo systemctl start docker 2>&1 | tee -a "$LOG_FILE"
    sleep 3

    if sudo systemctl is-active --quiet docker; then
        log "✅ Docker service started successfully"
    else
        log "❌ Failed to start Docker service"
        exit 1
    fi
fi

# Enable Docker to start on boot
log ""
log "Step 5: Enabling Docker to start on boot..."
sudo systemctl enable docker 2>&1 | tee -a "$LOG_FILE"
if [ $? -eq 0 ]; then
    log "✅ Docker enabled on boot"
else
    log "⚠️  Could not enable Docker on boot"
fi

# Restart Docker service
log ""
log "Step 6: Restarting Docker service for changes to take effect..."
sudo systemctl restart docker 2>&1 | tee -a "$LOG_FILE"
sleep 3

if sudo systemctl is-active --quiet docker; then
    log "✅ Docker service restarted successfully"
else
    log "❌ Docker service failed to restart"
    exit 1
fi

# Test Docker without sudo
log ""
log "Step 7: Testing Docker access without sudo..."
log "Running: docker --version"
docker --version 2>&1 | tee -a "$LOG_FILE"

if [ $? -eq 0 ]; then
    log "✅ Docker command works!"
else
    log "⚠️  Docker command failed - you may need to log out and back in"
    log "   Or run: newgrp docker"
fi

log ""
log "Step 8: Testing docker ps..."
docker ps 2>&1 | tee -a "$LOG_FILE"

if [ $? -eq 0 ]; then
    log "✅ Docker ps works! Permissions are fixed!"
else
    log "⚠️  Docker ps failed"
    log "   This is normal if you haven't logged out yet"
    log "   Run: newgrp docker"
    log "   Or log out and log back in"
fi

# Docker Compose check
log ""
log "Step 9: Checking Docker Compose..."
docker-compose --version 2>&1 | tee -a "$LOG_FILE"
if [ $? -eq 0 ]; then
    log "✅ Docker Compose is installed"
else
    log "⚠️  Docker Compose not found"
fi

# Summary
log ""
log "=========================================="
log "📊 SUMMARY"
log "=========================================="
log "User: $USER"
log "Groups: $(groups $USER)"
log "Docker service: $(sudo systemctl is-active docker)"
log "Docker socket: $(ls -l /var/run/docker.sock 2>/dev/null | awk '{print $1, $3, $4}')"
log ""
log "=========================================="
log "✅ Docker fix script completed!"
log "=========================================="
log ""
log "NEXT STEPS:"
log "1. Run: newgrp docker"
log "   (This applies group changes without logging out)"
log ""
log "2. OR log out and log back in to apply changes"
log ""
log "3. Then run: bash start.sh"
log ""
log "Log saved to: $LOG_FILE"
log "=========================================="

echo ""
echo "📝 Full log saved to: $LOG_FILE"
echo ""
echo "Would you like to apply group changes now? (This will open a new shell)"
echo "Run: newgrp docker"
echo ""
