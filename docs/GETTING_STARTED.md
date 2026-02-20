# Proxmox VM Deployer - Getting Started

Complete guide to start deploying VMs with the Proxmox VM Deployer.

## Quick Start

There are three ways to run the Proxmox VM Deployer:

### Option 1: Quick Start Script (Recommended for Development)

**Single command to start everything:**

```bash
./start.sh
```

This will:
- ✅ Start the backend API (port 8000)
- ✅ Start the frontend (port 3001)
- ✅ Check health and display URLs
- ✅ Create logs in `logs/` directory

**To stop:**
```bash
./stop.sh
```

Access the application:
- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

### Option 2: Docker Compose (Recommended for Production)

**Requirements**: Docker and Docker Compose installed

**Single command to start everything:**

```bash
docker-compose up -d
```

This will:
- ✅ Build Docker images for backend and frontend
- ✅ Start both services in containers
- ✅ Configure networking automatically
- ✅ Enable health checks and auto-restart

**Useful commands:**
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build

# View status
docker-compose ps
```

Access the application:
- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

### Option 3: Manual Start (Development)

Start each service manually in separate terminals.

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

---

### Configure Proxmox Connection

Edit `backend/.env` with your Proxmox credentials:

```env
PROXMOX_HOST=192.168.1.150
PROXMOX_USER=root@pam
PROXMOX_PASSWORD=your_password
DEFAULT_NODE=your_node_name
```

To find your node name:
```bash
ssh root@192.168.1.150
pvesh get /nodes
```

### 4. Deploy Your First VM

**Option A: Clone from Template** (Fastest)
1. Open http://localhost:3001
2. Check the green "Connected to Proxmox" banner
3. Click **"Clone from Template"** tab
4. Select a template from the dropdown
5. Enter a name for your VM
6. Adjust CPU and memory if needed
7. Click **"Clone 1 VM"**
8. Wait for the deployment to complete

**Option B: Create Windows VM from Scratch**
1. Open http://localhost:3001
2. Click **"Create New VM"** tab
3. Select **OS Type**: Windows
4. Select Windows installation ISO and VirtIO drivers ISO
5. Configure resources (4GB RAM, 4 cores, 80GB disk recommended)
6. Click **"Create 1 VM"**
7. Follow on-screen instructions to install VirtIO drivers during Windows setup

**Multi-VM Deployment**:
- Click **"+ Add Another VM"** to configure multiple VMs
- Settings are copied from previous VM (except name and ID)
- Single **"Clone/Create X VMs"** button deploys all at once

## Architecture Overview

```
┌─────────────────────────────────────────┐
│  React Frontend (Vite)                  │
│  Port 3001                              │
│  - Dark theme with Tailwind CSS         │
│  - Template cloning forms               │
│  - VM creation forms                    │
│  - Real-time status updates             │
└──────────────┬──────────────────────────┘
               │ HTTP/REST API
┌──────────────▼──────────────────────────┐
│  FastAPI Backend                        │
│  Port 8000                              │
│  - Proxmox API integration              │
│  - Template service                     │
│  - VM creation service                  │
│  - Validation service                   │
└──────────────┬──────────────────────────┘
               │ Proxmoxer Library
┌──────────────▼──────────────────────────┐
│  Proxmox VE Server                      │
│  192.168.1.150:8006                     │
│  - VM templates                         │
│  - Storage pools                        │
│  - Network configuration                │
└─────────────────────────────────────────┘
```

## Features

### Audit Logging

**What it does**: Automatically records all VM deployments and clones in structured logs

**Logged Information**:
- ✅ Timestamp (UTC)
- ✅ Username (Proxmox user)
- ✅ VM name and ID
- ✅ Complete configuration (CPU, memory, disk, network, storage, tags)
- ✅ ISO images used
- ✅ Template information (for clones)
- ✅ Operation status (success/failed)
- ✅ Error messages (if failed)
- ✅ Proxmox task IDs

**Log Format**: JSON Lines (one JSON object per line) for easy parsing

**Log Location**: `backend/logs/audit.log`

**Benefits**:
- 📊 Track all infrastructure changes
- 🔍 Audit trail for compliance (SOC 2, GDPR)
- 🐛 Debug deployment issues
- 📈 Capacity planning and reporting
- 💾 Easy database import (PostgreSQL, MongoDB)

**Usage Examples**:

```bash
# View statistics
python backend/scripts/parse_audit_log.py

# Export to CSV
python backend/scripts/parse_audit_log.py --export-csv deployments.csv

# Show failed operations
python backend/scripts/parse_audit_log.py --filter-status failed

# Show operations since date
python backend/scripts/parse_audit_log.py --since "2026-02-09T00:00:00Z"

# Parse with jq (command line)
jq 'select(.status == "success")' backend/logs/audit.log

# Count operations by type
jq -r '.operation' backend/logs/audit.log | sort | uniq -c
```

**Documentation**: See `backend/AUDIT_LOG_FORMAT.md` for complete format specification

### Batch Multi-VM Deployment

**What it does**: Deploy multiple VMs with a single click

**How to use**:
1. Configure first VM (template clone or new VM)
2. Click **"+ Add Another VM"** button
3. Settings are copied automatically (except name/ID)
4. Repeat for each VM you need
5. Click **"Clone/Create X VMs"** to deploy all at once

**Benefits**:
- Deploy 5-10 VMs in one operation
- Consistent configuration across VMs
- Time-saving for bulk deployments
- Individual customization per VM (name, tags, resources)

**Use cases**:
- Kubernetes cluster nodes (3+ VMs)
- Load-balanced web servers
- Development team environments
- Test/staging infrastructure

### Template Cloning (Priority Feature)

**What it does**: Creates a new VM by cloning an existing template

**Benefits**:
- Fast deployment (minutes vs hours)
- Pre-configured OS and applications
- Consistent configuration
- Full or linked clones supported

**Use cases**:
- Web servers with pre-installed stack
- Database servers with tuned configs
- Development environments
- Testing and staging

### VM Creation from Scratch

**What it does**: Creates a brand new empty VM

**Benefits**:
- Full control over configuration
- Custom OS installation
- Specific resource allocation

**Use cases**:
- Custom OS installations
- Unique configurations
- Learning and experimentation

### Windows VM Deployment (Best Practices)

**What it does**: Creates Windows VMs with optimal configuration following Proxmox recommendations

**Automatic Configuration**:
When you select "Windows" as OS Type, the system automatically configures:
- ✅ **BIOS**: OVMF (UEFI) with EFI disk - Required for Windows 11, recommended for Server 2022
- ✅ **Machine Type**: Q35 - Modern chipset with PCIe support
- ✅ **CPU Type**: host - Best performance with hardware passthrough
- ✅ **Storage**: VirtIO SCSI - High performance disk controller
- ✅ **Network**: VirtIO - Best network performance
- ✅ **Boot Order**: Windows ISO → Hard Disk

**Dual ISO Support**:
The system supports attaching both Windows installation ISO and VirtIO drivers ISO:
- **ide2**: Windows installation ISO (bootable)
- **ide0**: VirtIO drivers ISO (for driver installation during setup)

**Step-by-Step: Deploy Windows Server 2022**

1. **Prepare VirtIO Drivers** (One-time setup):
   ```bash
   # Download latest stable VirtIO drivers ISO
   # Current version: virtio-win-0.1.266.iso (updates regularly)
   wget https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/stable-virtio/virtio-win.iso

   # Upload to Proxmox storage
   # Via web UI: Datacenter → Storage → Upload
   # Or via CLI:
   scp virtio-win.iso root@192.168.1.150:/var/lib/vz/template/iso/
   ```

   **Note**: The web interface automatically prioritizes ISOs with "virtio" in the filename, showing them first in the dropdown for easy selection.

2. **Create Windows VM**:
   - Open http://localhost:3001
   - Click "Create New VM" tab
   - Select **OS Type**: Windows (triggers automatic best practices)
   - Select **ISO Image**: Your Windows Server 2022 ISO
   - Select **VirtIO Drivers ISO**: `virtio-win-*.iso` (appears first in dropdown)
   - Configure resources:
     - **Name**: `win-server-01`
     - **CPU Cores**: 4 (recommended minimum for Windows Server)
     - **Memory**: 4096 MB (4GB minimum, 8192 MB recommended)
     - **Disk Size**: 80 GB (60GB minimum for Windows Server 2022)
   - **Enable QEMU Guest Agent**: ✓ (recommended for better integration)
   - Click **"Create 1 VM"**

3. **Install Windows with VirtIO Drivers**:

   **During Installation** (Critical Steps):
   - Start the VM
   - Boot into Windows Setup
   - At "Where do you want to install Windows?" screen:
     - Click **"Load Driver"**
     - Click **"Browse"**
     - Navigate to second CD drive (usually D: or E:)
     - Go to: `viostor\2k22\amd64` (for Windows Server 2022)
       - Or `viostor\w11\amd64` (for Windows 11)
       - Or `viostor\w10\amd64` (for Windows 10)
     - Select the driver and click **"OK"**
     - Click **"Next"** to load VirtIO SCSI driver
   - Now the VirtIO disk appears and you can continue installation
   - Complete Windows installation normally

   **After Windows Installation**:
   - Log in to Windows
   - Open File Explorer → Navigate to VirtIO CD drive
   - Run `virtio-win-guest-tools.exe` (installs all remaining drivers)
   - This installs:
     - VirtIO Network driver (for network connectivity)
     - VirtIO Balloon driver (for memory management)
     - QEMU Guest Agent (for Proxmox integration)
     - VirtIO Serial driver
   - Reboot the VM
   - Verify network connectivity works
   - Verify Proxmox shows the VM's IP address (guest agent working)

4. **Post-Installation Optimization**:
   - Windows Update: Install latest updates
   - Enable Remote Desktop (if needed)
   - Configure Windows Firewall
   - Install additional software
   - Create a template (optional) for future deployments

**Hardware Configuration**:
```
efidisk0: EFI variables (1MB, auto-created)
ide0: VirtIO drivers ISO (non-bootable)
ide2: Windows installation ISO (bootable)
scsi0: Hard disk (VirtIO SCSI - 80GB)
net0: VirtIO network adapter
```

**Troubleshooting Windows Deployment**:

| Issue | Solution |
|-------|----------|
| Can't see disk during installation | Load VirtIO SCSI driver from drivers ISO |
| No network after installation | Install VirtIO network driver from drivers ISO |
| Proxmox doesn't show IP | Install QEMU Guest Agent from drivers ISO |
| VM won't boot | Ensure OVMF (UEFI) is selected, EFI disk is present |
| Boot drops to UEFI Shell | Verify Windows ISO is on ide2, boot order is correct |

**Why VirtIO Drivers?**
- **Performance**: Near-native disk and network performance (vs emulated hardware)
- **Stability**: Better compatibility with modern Windows versions
- **Features**: Enables advanced features (guest agent, memory ballooning)
- **Required**: Windows 11 and Server 2022 work best with VirtIO

**Reference**: https://pve.proxmox.com/wiki/Windows_2022_guest_best_practices

### Post-Deployment Validation

**What it does**: Validates that a VM is healthy and accessible

**Checks performed**:
1. Proxmox status (VM is running)
2. IP address assignment (via QEMU agent)
3. Port connectivity (SSH for Linux, RDP for Windows)

**Requirements**:
- QEMU guest agent installed in VMs
- Network connectivity
- Open firewall ports

## Configuration Reference

### Backend Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `PROXMOX_HOST` | Proxmox server IP | `192.168.1.150` |
| `PROXMOX_PORT` | API port | `8006` |
| `PROXMOX_USER` | Username | `root@pam` |
| `PROXMOX_PASSWORD` | Password | `your_password` |
| `DEFAULT_NODE` | Default node name | `pve` or `bestia` |
| `DEFAULT_STORAGE` | Default storage | `local-lvm` |
| `DEFAULT_NETWORK_BRIDGE` | Network bridge | `vmbr0` |
| `CORS_ORIGINS` | Frontend URL | `http://localhost:3001` |

### Frontend Configuration

Frontend automatically connects to `http://localhost:8000/api/v1`.

To change the backend URL, edit `frontend/src/services/api.js`:

```javascript
const API_BASE_URL = 'http://your-backend-url/api/v1';
```

## Creating Templates

For best results with template cloning, prepare templates in Proxmox:

### 1. Create a Base VM

```bash
# Create VM with ID 9000
qm create 9000 --name ubuntu-template --memory 2048 --cores 2 --net0 virtio,bridge=vmbr0
```

### 2. Install OS and Tools

- Install Ubuntu/Debian/CentOS
- Install QEMU guest agent: `apt install qemu-guest-agent`
- Configure cloud-init (optional)
- Install common tools
- Apply security updates

### 3. Clean and Convert to Template

```bash
# Clean up
apt clean
rm -rf /tmp/*
history -c

# Convert to template
qm template 9000
```

### 4. Update Backend Configuration

Add template VMID to `backend/.env`:

```env
LINUX_TEMPLATE_VMID=9000
```

## Common Workflows

### Workflow 1: Deploy Production Web Server

1. Clone from `web-server-template`
2. Set name: `prod-web-01`
3. Allocate: 4 cores, 8GB RAM
4. Enable "Start After Clone"
5. Deploy
6. Run validation
7. SSH to server: `ssh root@<ip-address>`
8. Deploy application

### Workflow 2: Create Development Environment

1. Clone from `dev-template`
2. Set name: `dev-environment-<developer>`
3. Allocate: 2 cores, 4GB RAM
4. Deploy multiple instances in parallel
5. Validate all instances
6. Distribute IPs to team

### Workflow 3: Deploy Windows Server 2022

1. Select OS Type: **Windows**
2. Choose Windows Server 2022 ISO
3. Choose VirtIO drivers ISO (`virtio-win-*.iso`)
4. Set name: `win-dc-01` (Domain Controller example)
5. Allocate: 4 cores, 8GB RAM, 100GB disk
6. Enable **QEMU Guest Agent**
7. Click **"Create 1 VM"**
8. During installation: Load VirtIO SCSI driver (browse to `D:\viostor\2k22\amd64`)
9. After installation: Run `virtio-win-guest-tools.exe` from drivers ISO
10. Configure Windows Server roles and features

### Workflow 4: Testing Infrastructure

1. Clone from `test-template`
2. Deploy multiple test VMs
3. Run automated tests
4. Collect results
5. Destroy VMs when done

## Troubleshooting

### Connection Failed

**Symptoms**: Red banner "Proxmox Connection Failed"

**Solutions**:
1. Check backend is running: `curl http://localhost:8000/api/v1/health`
2. Verify Proxmox credentials in `backend/.env`
3. Test SSH: `ssh root@192.168.1.150`
4. Check Proxmox API: `curl -k https://192.168.1.150:8006/api2/json/version`

### Templates Not Loading

**Symptoms**: Empty template dropdown

**Solutions**:
1. Verify templates exist: SSH to Proxmox, run `qm list`
2. Ensure VMs are marked as templates
3. Check browser console for API errors
4. Verify CORS settings in backend `.env`

### Clone/Creation Fails

**Symptoms**: Error message after submitting form

**Solutions**:
1. Check storage space: `pvesm status`
2. Verify node is online
3. Check backend logs for detailed error
4. Ensure VMID is not already in use

### Validation Fails

**Symptoms**: "degraded" or "unhealthy" status

**Solutions**:
1. Install QEMU guest agent: `apt install qemu-guest-agent`
2. Start agent: `systemctl start qemu-guest-agent`
3. Verify network configuration
4. Check firewall rules
5. Wait longer for VM to boot (2-5 minutes)

### Port Not Reachable

**Symptoms**: Port check fails in validation

**Solutions**:
1. Verify SSH/RDP service is running
2. Check VM firewall: `ufw status`
3. Check Proxmox firewall rules
4. Test manually: `telnet <ip> 22`

## Production Deployment

### Option 1: Docker Compose (Recommended)

**Advantages**:
- ✅ Containerized and isolated
- ✅ Easy to update and rollback
- ✅ Consistent across environments
- ✅ Built-in health checks and auto-restart
- ✅ No dependency conflicts

**Deployment steps:**

1. **Clone repository on server**:
   ```bash
   git clone <repository-url> /opt/proxmox-deployer
   cd /opt/proxmox-deployer
   ```

2. **Configure environment**:
   ```bash
   cp backend/.env.example backend/.env
   nano backend/.env  # Edit with production values
   ```

3. **Build and start**:
   ```bash
   docker-compose up -d --build
   ```

4. **Set up reverse proxy** (optional, for HTTPS):

   Nginx configuration for SSL termination:
   ```nginx
   server {
       listen 443 ssl http2;
       server_name proxmox-deployer.example.com;

       ssl_certificate /etc/ssl/certs/deployer.crt;
       ssl_certificate_key /etc/ssl/private/deployer.key;

       location / {
           proxy_pass http://localhost:3001;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
       }
   }
   ```

5. **Enable auto-start on boot**:

   Create `/etc/systemd/system/proxmox-deployer.service`:
   ```ini
   [Unit]
   Description=Proxmox VM Deployer
   Requires=docker.service
   After=docker.service

   [Service]
   Type=oneshot
   RemainAfterExit=yes
   WorkingDirectory=/opt/proxmox-deployer
   ExecStart=/usr/bin/docker-compose up -d
   ExecStop=/usr/bin/docker-compose down

   [Install]
   WantedBy=multi-user.target
   ```

   Enable the service:
   ```bash
   systemctl enable proxmox-deployer
   systemctl start proxmox-deployer
   ```

**Monitoring and maintenance:**
```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Update to latest version
git pull
docker-compose up -d --build

# Backup configuration
tar -czf proxmox-deployer-backup.tar.gz backend/.env

# View resource usage
docker stats
```

---

### Option 2: Systemd Services (Traditional)

**Use if Docker is not available on your system.**

### Backend (Systemd Service)

Create `/etc/systemd/system/proxmox-deployer-api.service`:

```ini
[Unit]
Description=Proxmox VM Deployer API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/proxmox-deployer/backend
Environment="PATH=/opt/proxmox-deployer/backend/venv/bin"
ExecStart=/opt/proxmox-deployer/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
systemctl enable proxmox-deployer-api
systemctl start proxmox-deployer-api
```

### Frontend (Nginx)

Build frontend:
```bash
cd frontend
npm run build
```

Nginx configuration:
```nginx
server {
    listen 80;
    server_name proxmox-deployer.example.com;

    root /opt/proxmox-deployer/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## Security Considerations

1. **HTTPS**: Use TLS certificates in production
2. **Authentication**: Add API authentication (JWT tokens)
3. **Firewall**: Restrict access to trusted networks
4. **Credentials**: Use secrets management (Vault, etc.)
5. **Rate Limiting**: Add rate limits to API endpoints
6. **Audit Logging**: Log all VM creation/deletion operations

## Next Steps

- [ ] Set up templates in Proxmox
- [ ] Configure backup policies
- [ ] Implement user authentication
- [ ] Add resource quotas
- [ ] Create monitoring dashboards
- [ ] Set up automated testing
- [ ] Document custom templates

## Support

- **Backend API Docs**: http://localhost:8000/docs
- **Project Repository**: Check CLAUDE.md for project details
- **Proxmox Documentation**: https://pve.proxmox.com/wiki/

---

Happy deploying! 🚀
