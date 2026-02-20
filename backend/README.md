# Proxmox VM Deployer API - Backend

Python FastAPI backend for deploying VMs on Proxmox via templates and direct creation.

## Features

- **Template Cloning**: Clone VMs from existing templates with customization
- **VM Creation**: Create new VMs from scratch with full configuration
- **Post-Deployment Validation**: Automatic health checks and port connectivity testing
- **Auto-Documentation**: Interactive API documentation via Swagger UI
- **Async Operations**: Built on FastAPI for high performance

## Prerequisites

- Python 3.12+ (Python 3.14 not supported due to pydantic-core compatibility)
- Access to Proxmox VE 8.x server
- Proxmox API credentials

## Setup

### 1. Create Virtual Environment

```bash
cd backend
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your Proxmox configuration:

```env
# Proxmox API Configuration
PROXMOX_HOST=192.168.1.150
PROXMOX_PORT=8006
PROXMOX_USER=root@pam
PROXMOX_PASSWORD=your_password_here
PROXMOX_VERIFY_SSL=false

# Default Cluster Configuration
DEFAULT_NODE=your_node_name
DEFAULT_STORAGE=local-lvm
DEFAULT_NETWORK_BRIDGE=vmbr0

# Optional: Template Configuration
LINUX_TEMPLATE_VMID=9000
WINDOWS_TEMPLATE_VMID=9001

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3001
```

## Running the API

### Development Mode

```bash
# From backend directory with venv activated
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Health Check

```
GET  /api/v1/health              - Basic health check
GET  /api/v1/proxmox/status      - Proxmox connection status
```

### Templates (Priority Feature)

```
GET  /api/v1/templates           - List all templates
GET  /api/v1/templates/{vmid}    - Get template details
POST /api/v1/templates/clone     - Clone VM from template
GET  /api/v1/templates/{vmid}/validate - Validate template exists
```

### VMs

```
POST /api/v1/vms/create          - Create new VM
GET  /api/v1/vms/{vmid}          - Get VM info
GET  /api/v1/vms/{vmid}/status   - Get VM status
POST /api/v1/vms/{vmid}/validate - Run post-deployment validation
```

## Usage Examples

### Clone a Template

```bash
curl -X POST "http://localhost:8000/api/v1/templates/clone" \
  -H "Content-Type: application/json" \
  -d '{
    "source_vmid": 9000,
    "name": "my-new-server",
    "full_clone": true,
    "cores": 4,
    "memory": 8192,
    "start_after_clone": true
  }'
```

### Create a New VM

```bash
curl -X POST "http://localhost:8000/api/v1/vms/create" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-vm",
    "cores": 2,
    "memory": 2048,
    "disk_size": 20,
    "os_type": "linux",
    "start_on_creation": false
  }'
```

### Validate a VM

```bash
curl -X POST "http://localhost:8000/api/v1/vms/150/validate?os_type=linux"
```

## Post-Deployment Validation

The validation service performs the following checks:

1. **Proxmox Status**: Verifies VM is running in Proxmox
2. **IP Address**: Waits for VM to get an IP (via QEMU agent)
3. **Port Connectivity**: Tests SSH (port 22) for Linux or RDP (port 3389) for Windows

Validation typically takes 2-5 minutes depending on VM boot time.

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── dependencies.py      # Dependency injection
│   │
│   ├── api/v1/
│   │   ├── health.py        # Health endpoints
│   │   ├── templates.py     # Template endpoints (PRIORITY)
│   │   ├── vms.py           # VM endpoints
│   │   └── router.py        # Main router
│   │
│   ├── schemas/
│   │   ├── template.py      # Template schemas
│   │   ├── vm.py            # VM schemas
│   │   └── validation.py    # Validation schemas
│   │
│   ├── services/
│   │   ├── proxmox_service.py     # Proxmox API wrapper
│   │   ├── template_service.py    # Template logic
│   │   ├── vm_service.py          # VM creation logic
│   │   └── validation_service.py  # Validation logic
│   │
│   ├── core/
│   │   └── exceptions.py    # Custom exceptions
│   │
│   └── utils/
│       └── port_checker.py  # Port connectivity testing
│
├── .env                     # Environment configuration
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `PROXMOX_HOST` | Proxmox server IP/hostname | Required |
| `PROXMOX_PORT` | Proxmox API port | 8006 |
| `PROXMOX_USER` | Proxmox username | Required |
| `PROXMOX_PASSWORD` | Proxmox password | Required |
| `PROXMOX_VERIFY_SSL` | Verify SSL certificates | false |
| `DEFAULT_NODE` | Default Proxmox node | Required |
| `DEFAULT_STORAGE` | Default storage pool | local-lvm |
| `DEFAULT_NETWORK_BRIDGE` | Default network bridge | vmbr0 |
| `VMID_MIN` | Minimum allowed VM ID | 150 |
| `VMID_MAX` | Maximum allowed VM ID | 999 |
| `VALIDATION_TIMEOUT` | Validation timeout (seconds) | 300 |
| `VALIDATION_SSH_PORT` | SSH port for validation | 22 |
| `VALIDATION_RDP_PORT` | RDP port for validation | 3389 |
| `API_HOST` | API server host | 0.0.0.0 |
| `API_PORT` | API server port | 8000 |
| `CORS_ORIGINS` | CORS allowed origins | http://localhost:3001 |

## Troubleshooting

### Connection Issues

```bash
# Test Proxmox connection
curl http://localhost:8000/api/v1/proxmox/status
```

### Template Not Found

- Verify templates exist in Proxmox
- Check that VMs are marked as templates
- Ensure QEMU agent is installed in templates for validation

### Validation Timeouts

- Ensure QEMU guest agent is installed in VMs
- Check that VMs can obtain IP addresses via DHCP
- Verify firewall rules allow port 22 (SSH) or 3389 (RDP)

## Development

### Code Style

The codebase follows:
- PEP 8 style guidelines
- Type hints for all functions
- Pydantic models for request/response validation
- Async/await for I/O operations

### Adding New Endpoints

1. Create schema in `app/schemas/`
2. Implement service logic in `app/services/`
3. Create API endpoint in `app/api/v1/`
4. Add router to `app/api/v1/router.py`

## License

Part of the Proxmox VM Deployer project.
