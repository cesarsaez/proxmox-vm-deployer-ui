# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Proxmox VM Deployer is a modern web interface for deploying and managing virtual machines on Proxmox VE. It provides a user-friendly form interface for creating new VMs from scratch or cloning from templates, with special support for Windows VMs and cloud-init automation.

## Architecture

**Tech Stack:**
- **Backend:** Python FastAPI with async operations
- **Frontend:** React (Vite) with dark theme, Tailwind CSS, and Heroicons
- **Configuration:** Environment variables via .env files (never hardcode credentials)
- **Deployment:** Docker Compose for production, development scripts for local development

**API Flow:**
```
Frontend (React) → Backend API (FastAPI) → Proxmox API (Proxmoxer)
```

**Key Components:**
- Template cloning service
- VM creation service
- Cloud-init automation
- Post-deployment validation
- Audit logging system

## Environment Details

**Proxmox Server:**
- Configure connection details in `backend/.env`
- Access via SSH for direct testing when needed
- Supports Proxmox VE 7.0+

**Required Environment Variables:**
```env
PROXMOX_HOST=<your-proxmox-ip>
PROXMOX_USER=root@pam
PROXMOX_PASSWORD=<your-password>
DEFAULT_NODE=<your-node-name>
DEFAULT_STORAGE=<your-storage>
DEFAULT_NETWORK_BRIDGE=vmbr0
```

## Features

### 1. Template Cloning (Priority Feature)
- Fast VM deployment from pre-configured templates
- Full clone or linked clone support
- Batch multi-VM deployment
- Cloud-init integration for automated configuration

### 2. VM Creation from Scratch
- Complete VM configuration via web form
- Linux and Windows VM support
- Helper tooltips for all fields
- Custom resource allocation (CPU, memory, disk)

### 3. Windows VM Best Practices (Automatic)
When "Windows" OS type is selected, the system automatically configures:
- BIOS: OVMF (UEFI) with EFI disk
- Machine type: Q35 (modern chipset)
- CPU type: host (best performance)
- Storage: VirtIO SCSI (high performance)
- Network: VirtIO adapter
- Dual ISO support: Windows installation + VirtIO drivers

### 4. Cloud-Init Automation
**Location:** `backend/app/utils/cloudinit.py`

Automated VM configuration on first boot:
- User creation with SSH keys
- Network configuration (static IP or DHCP)
- Package installation
- Custom commands execution
- Automatic openssh-server installation

**Key Functions:**
- `generate_user_data()` - Creates cloud-config YAML
- `upload_custom_userdata()` - Uploads to Proxmox via SSH
- `apply_custom_cloudinit()` - Applies configuration to VM

### 5. Batch Multi-VM Deployment
- Deploy multiple VMs with single click
- Configuration templates with per-VM customization
- Consistent infrastructure deployment
- Use cases: Kubernetes clusters, dev environments, load-balanced servers

### 6. Audit Logging
**Location:** `backend/logs/audit.log`

Structured JSON logging of all operations:
- VM creation and cloning events
- Complete configuration details
- Success/failure status
- Timestamp and user information
- Compliance-ready audit trail

**Parser Script:** `backend/scripts/parse_audit_log.py`

### 7. Post-Deployment Validation
- Proxmox health check
- IP address verification (via QEMU agent)
- Port connectivity testing:
  - Port 22 (SSH) for Linux VMs
  - Port 3389 (RDP) for Windows VMs
- VM status monitoring

## File Structure

```
Proxmox/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API endpoints
│   │   ├── core/            # Configuration
│   │   ├── schemas/         # Pydantic models
│   │   ├── services/        # Business logic
│   │   └── utils/           # Utilities (cloud-init, validation)
│   ├── logs/                # Audit logs (gitignored)
│   ├── .env                 # Configuration (gitignored)
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── services/        # API client
│   │   └── App.jsx          # Main app
│   └── package.json
├── docs/
│   ├── GETTING_STARTED.md   # Setup and usage guide
│   ├── CLOUD_INIT_GUIDE.md  # Cloud-init documentation
│   └── webui.png            # UI screenshot
├── docker-compose.yml       # Production deployment
├── start.sh                 # Development startup script
└── stop.sh                  # Development shutdown script
```

## Development Notes

### Security
- **Never hardcode credentials** - Always use .env files
- .env files are gitignored to prevent credential leaks
- Audit logs may contain operational data - keep them gitignored
- Test with non-production credentials when possible

### Testing
- SSH access to Proxmox server can be used for direct testing
- Use `backend/.env.example` as template for configuration
- Test cloud-init with Ubuntu cloud images (template VM recommended)

### Cloud-Init Implementation
- Requires Proxmox snippets storage: `pvesm set local --content vztmpl,iso,snippets`
- User-data files stored in `/var/lib/vz/snippets/` on Proxmox host
- SSH access required for uploading cloud-init configurations
- Always includes openssh-server for SSH access

### Windows VM Deployment
- Requires VirtIO drivers ISO (download from Fedora project)
- VirtIO ISOs prioritized in dropdown (sorted alphabetically)
- During Windows installation: Load VirtIO SCSI driver from `viostor\<version>\amd64`
- Post-installation: Run `virtio-win-guest-tools.exe` for all drivers

### Code Conventions
- Python: Follow PEP 8, use type hints
- JavaScript: Use ES6+, functional components with hooks
- API: RESTful design, OpenAPI documentation at `/docs`
- Error handling: Always return meaningful error messages

## Common Tasks

### Adding a New API Endpoint
1. Define schema in `backend/app/schemas/`
2. Implement service logic in `backend/app/services/`
3. Create endpoint in `backend/app/api/v1/`
4. Update frontend API client in `frontend/src/services/api.js`

### Modifying Cloud-Init Behavior
- Edit `backend/app/utils/cloudinit.py`
- Update schemas in `backend/app/schemas/template.py`
- Modify frontend form in `frontend/src/components/TemplateCloneForm.jsx`

### Adding Validation
- Implement in `backend/app/utils/validation.py`
- Call from service layer after VM creation
- Handle results in frontend with status display

## Running the Application

### Development
```bash
# Start both services
./start.sh

# Access frontend: http://localhost:3001
# Access API docs: http://localhost:8000/docs
```

### Production (Docker)
```bash
# Configure backend/.env first
docker-compose up -d

# View logs
docker-compose logs -f
```

## Troubleshooting

### Connection Issues
- Verify Proxmox credentials in `backend/.env`
- Check network connectivity to Proxmox server
- Test SSH access if using cloud-init

### Cloud-Init Not Working
- Verify snippets storage is enabled on Proxmox
- Check SSH access to Proxmox host
- Ensure template has cloud-init drive configured

### Windows VM Won't Boot
- Verify OVMF (UEFI) is configured
- Check EFI disk is present
- Ensure boot order is correct (ISO → Disk)

### Templates Not Loading
- Ensure VMs are marked as templates in Proxmox
- Check Proxmox API connectivity
- Verify CORS settings in backend/.env

## Important Reminders

1. **Never commit .env files** - They contain credentials
2. **Never commit logs/** - May contain sensitive operational data
3. **Always test changes** - Especially for cloud-init and Windows configurations
4. **Document new features** - Update relevant .md files in docs/
5. **Follow existing patterns** - Consistency improves maintainability
6. **Use audit logging** - All VM operations should be logged

## Reference Documentation

- **Getting Started:** `docs/GETTING_STARTED.md`
- **Cloud-Init Guide:** `docs/CLOUD_INIT_GUIDE.md`
- **Proxmox API:** https://pve.proxmox.com/wiki/Proxmox_VE_API
- **Cloud-Init Docs:** https://cloudinit.readthedocs.io/

---

**Last Updated:** 2026-02-20
**Project Version:** 1.0
**Proxmox VE Supported:** 7.0+
