# Cloud-Init Implementation Guide

## Overview

This guide explains the cloud-init implementation for automated Ubuntu VM configuration in the Proxmox VM Deployer. Cloud-init allows you to automatically configure VMs on first boot with custom users, SSH keys, network settings, packages, and commands - without manual intervention.

## Table of Contents

- [What is Cloud-Init?](#what-is-cloud-init)
- [Features](#features)
- [Architecture](#architecture)
- [Backend Implementation](#backend-implementation)
- [Frontend Implementation](#frontend-implementation)
- [How to Deploy VMs with Cloud-Init](#how-to-deploy-vms-with-cloud-init)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Technical Details](#technical-details)

---

## What is Cloud-Init?

Cloud-init is an industry-standard method for cloud instance initialization. It reads configuration data at boot time and automatically configures the VM with:
- User accounts and SSH keys
- Network settings (static IP or DHCP)
- Package installation
- Custom commands and scripts
- System services

### Why Cloud-Init?

✅ **Automation** - No manual configuration needed after deployment
✅ **Consistency** - Same configuration applied every time
✅ **Security** - SSH key-based authentication, no passwords
✅ **Speed** - Configure everything in one boot cycle
✅ **Flexibility** - Support for packages, users, and custom scripts

---

## Features

Our cloud-init implementation supports:

### Network Configuration
- Static IP address with gateway
- DNS nameserver configuration
- DNS search domain

### User Management
- Create custom users with sudo privileges
- Configure SSH public keys for passwordless authentication
- Add users to multiple groups
- Automatic sudo access (NOPASSWD)

### Software Installation
- Automatic package installation on first boot
- Package updates and upgrades
- Pre-installed `openssh-server` for SSH access

### Custom Commands
- Run shell commands after system setup
- Start and enable services
- Create files and configure system settings

---

## Architecture

### Flow Diagram

```
User (UI) → Frontend → Backend API → Cloud-Init Module → Proxmox API
                                            ↓
                                    Generate user-data.yml
                                            ↓
                                    Upload to Proxmox snippets
                                            ↓
                                    Configure VM (cicustom)
                                            ↓
                                    VM boots → Cloud-init runs → Configured VM
```

### Components

1. **Frontend (React)** - User interface for cloud-init configuration
2. **Backend API (Python/FastAPI)** - Processes requests and generates cloud-init data
3. **Cloud-Init Module** - Python utilities for generating user-data YAML
4. **Proxmox Storage** - Stores cloud-init snippets
5. **Cloud-Init Drive** - Virtual CD-ROM attached to VMs with configuration

---

## Backend Implementation

### File Structure

```
backend/
├── app/
│   ├── schemas/
│   │   └── template.py                 # Data models for cloud-init
│   ├── services/
│   │   └── template_service.py         # Service layer - applies cloud-init
│   └── utils/
│       └── cloudinit.py                # Cloud-init utilities (MAIN MODULE)
```

### Key Files

#### 1. `backend/app/utils/cloudinit.py`

**Location:** `/backend/app/utils/cloudinit.py`

**Purpose:** Core module for cloud-init implementation. Contains all the logic for:
- Generating user-data YAML from configuration
- Uploading snippets to Proxmox
- Applying cloud-init settings to VMs

**Key Functions:**

##### `generate_user_data(config: CloudInitConfig, hostname: str) -> str`
Generates the cloud-config YAML file content from configuration.

```python
def generate_user_data(config: CloudInitConfig, hostname: str) -> str:
    """
    Generate cloud-init user-data YAML from configuration

    Args:
        config: CloudInitConfig object with user settings
        hostname: VM hostname

    Returns:
        YAML string with #cloud-config header
    """
```

**What it does:**
- Creates users with SSH keys and sudo access
- Adds packages (always includes openssh-server)
- Configures groups and permissions
- Adds custom commands
- Formats everything as valid cloud-config YAML

##### `upload_custom_userdata(settings, node: str, vmid: int, user_data: str) -> str`
Uploads the generated user-data YAML to Proxmox snippets storage via SSH.

```python
def upload_custom_userdata(settings, node: str, vmid: int, user_data: str) -> str:
    """
    Upload custom user-data to Proxmox snippets storage

    Args:
        settings: Application settings
        node: Proxmox node name
        vmid: VM ID
        user_data: Cloud-init YAML content

    Returns:
        Snippet path (e.g., 'local:snippets/user-data-vm101.yml')
    """
```

**What it does:**
- Connects to Proxmox host via SSH (using paramiko)
- Creates `/var/lib/vz/snippets/` directory if needed
- Uploads user-data file as `user-data-vm<VMID>.yml`
- Returns the snippet reference for VM configuration

##### `apply_custom_cloudinit(proxmox_service, settings, node: str, vmid: int, config: CloudInitConfig, hostname: str) -> None`
Main function that orchestrates the cloud-init application process.

```python
def apply_custom_cloudinit(proxmox_service, settings, node: str, vmid: int,
                          config: CloudInitConfig, hostname: str) -> None:
    """
    Apply custom cloud-init configuration using user-data snippets

    Args:
        proxmox_service: ProxmoxService instance
        settings: Application settings
        node: Node name
        vmid: VM ID
        config: CloudInitConfig object
        hostname: VM hostname
    """
```

**What it does:**
1. Calls `generate_user_data()` to create YAML
2. Calls `upload_custom_userdata()` to upload to Proxmox
3. Configures VM with `cicustom` parameter to use the uploaded file
4. Applies network settings (IP, DNS, gateway) via Proxmox API

**Important Implementation Details:**

```python
# Auto-include openssh-server (lines 63-74)
packages_list = []
packages_list.append('openssh-server')  # Always included

if config.packages:
    for pkg in config.packages:
        if pkg not in packages_list:
            packages_list.append(pkg)

# Auto-start SSH service (lines 77-86)
runcmd_list = [
    'systemctl enable ssh',
    'systemctl start ssh'
]

if config.runcmd:
    runcmd_list.extend(config.runcmd)
```

#### 2. `backend/app/schemas/template.py`

**Location:** `/backend/app/schemas/template.py`

**Purpose:** Defines the data models (Pydantic schemas) for cloud-init configuration.

**Key Classes:**

##### `CloudInitUser` (lines 20-26)
```python
class CloudInitUser(BaseModel):
    username: str = Field(..., description="Username")
    password: Optional[str] = Field(None, description="Password")
    ssh_keys: Optional[list[str]] = Field(None, description="SSH public keys")
    sudo: bool = Field(default=False, description="Grant sudo privileges")
    groups: Optional[list[str]] = Field(None, description="Groups")
```

##### `CloudInitConfig` (lines 29-43)
```python
class CloudInitConfig(BaseModel):
    ipconfig: Optional[str] = Field(None, description="IP configuration")
    nameserver: Optional[str] = Field(None, description="DNS nameserver")
    searchdomain: Optional[str] = Field(None, description="DNS search domain")
    users: Optional[list[CloudInitUser]] = Field(None, description="Users to create")
    packages: Optional[list[str]] = Field(None, description="Packages to install")
    runcmd: Optional[list[str]] = Field(None, description="Commands to run")
```

##### `CloneRequest` (lines 46-64)
Updated to include cloud-init configuration:
```python
class CloneRequest(BaseModel):
    # ... existing fields ...
    cloudinit: Optional[CloudInitConfig] = Field(None, description="Cloud-init config")
```

#### 3. `backend/app/services/template_service.py`

**Location:** `/backend/app/services/template_service.py`

**Purpose:** Service layer that handles template cloning and calls cloud-init utilities.

**Key Changes:**

##### `clone_from_template()` method (line 193)
Added cloud-init application after VM cloning:

```python
# Apply cloud-init configuration if specified
if request.cloudinit:
    self._apply_cloudinit(target_node, new_vmid, request)
```

##### `_apply_cloudinit()` method (lines 300-325)
```python
def _apply_cloudinit(self, node: str, vmid: int, request: CloneRequest) -> None:
    """
    Apply cloud-init configuration to cloned VM

    Args:
        node: Node name
        vmid: VM ID
        request: Clone request with cloud-init config
    """
    from app.utils.cloudinit import apply_custom_cloudinit

    if request.cloudinit:
        hostname = request.name
        apply_custom_cloudinit(
            proxmox_service=self.proxmox,
            settings=self.settings,
            node=node,
            vmid=vmid,
            config=request.cloudinit,
            hostname=hostname
        )
```

---

## Frontend Implementation

### File Structure

```
frontend/
└── src/
    └── components/
        └── TemplateCloneForm.jsx    # Main form with cloud-init UI
```

### Key File: `TemplateCloneForm.jsx`

**Location:** `/frontend/src/components/TemplateCloneForm.jsx`

**Purpose:** React component that provides the user interface for cloud-init configuration.

#### State Management (lines 19-41)

Each VM in the clone list includes cloud-init configuration:

```javascript
const [vmsToClone, setVmsToClone] = useState([{
  source_vmid: '',
  new_vmid: '',
  name: '',
  cores: 2,
  memory: 2048,
  full_clone: true,
  start_after_clone: false,
  tags: [],
  // Cloud-init configuration
  enable_cloudinit: false,
  cloudinit: {
    ipconfig: '',
    nameserver: '8.8.8.8',
    searchdomain: 'local',
    username: '',
    ssh_keys: '',
    sudo: true,
    groups: 'sudo',
    packages: '',
    runcmd: ''
  }
}])
```

#### Event Handlers

##### `handleCloudInitChange()` (lines 79-98)
Handles changes to cloud-init form fields:

```javascript
const handleCloudInitChange = (e) => {
  const { name, value, type, checked } = e.target
  const updatedVMs = [...vmsToClone]
  const fieldName = name.replace('cloudinit.', '')

  if (name === 'enable_cloudinit') {
    updatedVMs[currentVMIndex] = {
      ...updatedVMs[currentVMIndex],
      enable_cloudinit: checked
    }
  } else {
    updatedVMs[currentVMIndex] = {
      ...updatedVMs[currentVMIndex],
      cloudinit: {
        ...updatedVMs[currentVMIndex].cloudinit,
        [fieldName]: type === 'checkbox' ? checked : value
      }
    }
  }
  setVmsToClone(updatedVMs)
}
```

#### API Payload Construction (lines 130-160)

Converts form data to API payload:

```javascript
const payload = vmsToClone.map(vm => {
  const vmPayload = {
    source_vmid: parseInt(vm.source_vmid),
    name: vm.name,
    // ... other fields ...
  }

  // Add cloud-init if enabled
  if (vm.enable_cloudinit && vm.cloudinit.username) {
    const cloudinit = {
      ipconfig: vm.cloudinit.ipconfig || undefined,
      nameserver: vm.cloudinit.nameserver || undefined,
      searchdomain: vm.cloudinit.searchdomain || undefined,
      users: [{
        username: vm.cloudinit.username,
        ssh_keys: vm.cloudinit.ssh_keys
          ? vm.cloudinit.ssh_keys.split('\n').filter(k => k.trim())
          : undefined,
        sudo: vm.cloudinit.sudo,
        groups: vm.cloudinit.groups
          ? vm.cloudinit.groups.split(',').map(g => g.trim()).filter(g => g)
          : undefined
      }],
      packages: vm.cloudinit.packages
        ? vm.cloudinit.packages.split(',').map(p => p.trim()).filter(p => p)
        : undefined,
      runcmd: vm.cloudinit.runcmd
        ? vm.cloudinit.runcmd.split('\n').filter(c => c.trim())
        : undefined
    }

    if (cloudinit.users[0].username) {
      vmPayload.cloudinit = cloudinit
    }
  }

  return vmPayload
})
```

#### UI Components (lines 360-520)

Cloud-init section with collapsible form:

```jsx
{/* Cloud-Init Configuration */}
<div className="space-y-4 pt-6 border-t border-dark-border">
  <div className="flex items-center justify-between">
    <div>
      <h4>Cloud-Init Configuration</h4>
      <p>For Ubuntu cloud images - automatically configure users, network, and packages</p>
    </div>
    <FormCheckbox
      name="enable_cloudinit"
      checked={vmsToClone[currentVMIndex].enable_cloudinit}
      onChange={handleCloudInitChange}
    />
  </div>

  {vmsToClone[currentVMIndex].enable_cloudinit && (
    <div className="space-y-4">
      {/* Network Configuration */}
      {/* User Configuration */}
      {/* Software & Commands */}
    </div>
  )}
</div>
```

---

## How to Deploy VMs with Cloud-Init

### Prerequisites

1. **Ubuntu Cloud Image Template** in Proxmox (e.g., VM 9000 - ubuntu-noble-template)
2. **Template has cloud-init drive** configured (ide2 or scsi2 with cloudinit)
3. **Backend running** at http://localhost:8000
4. **Frontend running** at http://localhost:3001 or http://localhost:3002

### Step-by-Step Guide

#### Step 1: Access the Web Interface

Open your browser and navigate to:
```
http://localhost:3002
```

#### Step 2: Navigate to Clone from Template

Click on the **"Clone from Template"** tab in the interface.

#### Step 3: Select Ubuntu Template

1. In the **Template** dropdown, select your Ubuntu cloud image template
   - Example: `ubuntu-noble-template (ID: 9000)`
2. Template information will be displayed showing cores, memory, and node

#### Step 4: Configure Basic VM Settings

Fill in the basic VM details:

| Field | Example | Required |
|-------|---------|----------|
| **New VM ID** | `105` | No (auto-assigned) |
| **VM Name** | `my-ubuntu-server` | Yes |
| **CPU Cores** | `2` | Yes |
| **Memory (MB)** | `2048` | Yes |
| **Tags** | `production, web` | No |
| **Full Clone** | ✓ Checked | Yes |
| **Start After Clone** | ✓ Checked | Optional |

#### Step 5: Enable Cloud-Init

1. Scroll down to the **"Cloud-Init Configuration"** section
2. Click the toggle switch to **enable cloud-init**
3. The cloud-init form will expand showing all configuration options

#### Step 6: Configure Network Settings

Fill in the network configuration:

| Field | Example | Description |
|-------|---------|-------------|
| **IP Configuration** | `ip=192.168.1.175/24,gw=192.168.1.1` | Static IP or leave empty for DHCP |
| **DNS Nameserver** | `8.8.8.8` | DNS server (default: 8.8.8.8) |
| **Search Domain** | `local` | DNS search domain (default: local) |

**IP Configuration Format:**
```
ip=<IP_ADDRESS>/<NETMASK>,gw=<GATEWAY>
```

**Examples:**
- Static IP: `ip=192.168.1.100/24,gw=192.168.1.1`
- DHCP: Leave empty or remove the field

#### Step 7: Configure User Settings

Create your admin user:

| Field | Example | Required | Description |
|-------|---------|----------|-------------|
| **Username** | `admin` or `bob` | Yes | User account name |
| **SSH Public Keys** | `ssh-rsa AAAAB3NzaC1...` | Yes* | Your SSH public key (one per line) |
| **Grant Sudo Access** | ✓ Checked | No | Passwordless sudo privileges |
| **Groups** | `sudo,docker,users` | No | Comma-separated groups |

*Required for SSH access (no password is set)

**To get your SSH public key:**
```bash
cat ~/.ssh/id_rsa.pub
# or
cat ~/.ssh/id_ed25519.pub
```

#### Step 8: Configure Software & Commands (Optional)

##### Packages to Install

Add comma-separated package names:
```
vim,git,docker.io,htop,curl,nginx
```

**Note:** `openssh-server` is **automatically included** - you don't need to add it!

##### Custom Commands

Add shell commands (one per line):
```
systemctl enable docker
systemctl start docker
echo "Setup complete" > /root/setup.log
usermod -aG docker admin
```

#### Step 9: Review and Deploy

1. Review all your settings
2. Click the **"Clone 1 VM"** button at the bottom
3. Wait for the deployment to complete (~2-3 minutes)

#### Step 10: Wait for Cloud-Init

After deployment:

1. **Wait 2-3 minutes** for cloud-init to complete
2. Cloud-init runs automatically on first boot
3. You'll see a success message with the VM ID

#### Step 11: Access Your VM

Once cloud-init completes, SSH to your VM:

```bash
ssh username@ip-address

# Example:
ssh bob@192.168.1.175
```

**You should be logged in without a password!** (using your SSH key)

#### Step 12: Verify Configuration

Check that everything was configured correctly:

```bash
# Check username
whoami

# Check sudo access
sudo whoami
# Should return: root

# Check hostname
hostname

# Check IP address
ip addr show

# Check installed packages
dpkg -l | grep -E '(vim|git|docker)'

# Check cloud-init status
cloud-init status
# Should show: status: done
```

---

## Examples

### Example 1: Basic Web Server

**Scenario:** Deploy a simple web server with Nginx

**Cloud-Init Configuration:**

```
Network:
  IP Configuration: ip=192.168.1.200/24,gw=192.168.1.1
  DNS Nameserver: 8.8.8.8

User:
  Username: webadmin
  SSH Keys: [your ssh public key]
  Sudo Access: ✓
  Groups: sudo

Software:
  Packages: nginx,vim,curl

Commands:
  systemctl enable nginx
  systemctl start nginx
  echo "Welcome" > /var/www/html/index.html
```

**Result:** VM with Nginx installed and running, accessible at http://192.168.1.200

### Example 2: Docker Development Server

**Scenario:** Development server with Docker pre-installed

**Cloud-Init Configuration:**

```
Network:
  IP Configuration: ip=192.168.1.201/24,gw=192.168.1.1
  DNS Nameserver: 8.8.8.8

User:
  Username: developer
  SSH Keys: [your ssh public key]
  Sudo Access: ✓
  Groups: sudo,docker

Software:
  Packages: docker.io,docker-compose,git,vim,htop

Commands:
  systemctl enable docker
  systemctl start docker
  usermod -aG docker developer
  docker pull nginx
```

**Result:** Ready-to-use Docker development environment

### Example 3: Database Server

**Scenario:** PostgreSQL database server

**Cloud-Init Configuration:**

```
Network:
  IP Configuration: ip=192.168.1.202/24,gw=192.168.1.1
  DNS Nameserver: 8.8.8.8

User:
  Username: dbadmin
  SSH Keys: [your ssh public key]
  Sudo Access: ✓
  Groups: sudo

Software:
  Packages: postgresql,postgresql-contrib

Commands:
  systemctl enable postgresql
  systemctl start postgresql
  sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'mypassword';"
```

### Example 4: Kubernetes Node

**Scenario:** Kubernetes worker node

**Cloud-Init Configuration:**

```
Network:
  IP Configuration: ip=192.168.1.210/24,gw=192.168.1.1
  DNS Nameserver: 8.8.8.8

User:
  Username: k8sadmin
  SSH Keys: [your ssh public key]
  Sudo Access: ✓
  Groups: sudo

Software:
  Packages: docker.io,curl,apt-transport-https,ca-certificates

Commands:
  systemctl enable docker
  systemctl start docker
  swapoff -a
  sed -i '/ swap / s/^/#/' /etc/fstab
  curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -
  echo "deb http://apt.kubernetes.io/ kubernetes-xenial main" > /etc/apt/sources.list.d/kubernetes.list
  apt-get update
  apt-get install -y kubelet kubeadm kubectl
```

---

## Troubleshooting

### SSH Connection Refused

**Problem:** `ssh: connect to host X.X.X.X port 22: Connection refused`

**Solution:** Wait 2-3 minutes for cloud-init to complete. The SSH server is installed and started automatically, but it takes time on first boot.

**Verify:**
```bash
# Check if VM is reachable
ping 192.168.1.175

# Check cloud-init status via Proxmox console
ssh root@192.168.1.150 "qm terminal <VMID>"
# Inside VM console:
cloud-init status
```

### Wrong Username

**Problem:** Using the wrong username to SSH

**Solution:** Use the username you specified in the cloud-init configuration, not a default username like `ubuntu` or `root`.

**Check the user-data file:**
```bash
ssh root@192.168.1.150 "cat /var/lib/vz/snippets/user-data-vm<VMID>.yml"
```

### SSH Key Not Working

**Problem:** SSH asking for password despite providing key

**Causes:**
1. Wrong SSH key format or corrupted key
2. Key not properly pasted (missing parts)
3. Extra whitespace or line breaks

**Solution:**
- Verify your public key format: should start with `ssh-rsa`, `ssh-ed25519`, or similar
- Copy the entire key including the type prefix
- Don't include line breaks in the middle of the key

**Test your key format:**
```bash
ssh-keygen -l -f ~/.ssh/id_rsa.pub
```

### Cloud-Init Failed Error

**Problem:** Seeing `[FAILED] Failed to start cloud-final.service` in console

**Solution:** This is usually harmless. The main cloud-init stages already completed. Verify:

```bash
# Inside VM (via Proxmox console)
cloud-init status --long

# Check if user was created
id username

# Check if packages were installed
dpkg -l | grep openssh-server
```

### Network Not Configured

**Problem:** VM has no network connectivity

**Causes:**
1. Invalid IP configuration format
2. Wrong gateway or network settings
3. Network interface name mismatch

**Solution:**
- Verify IP format: `ip=192.168.1.100/24,gw=192.168.1.1`
- Check gateway is correct for your network
- Leave empty for DHCP if static IP doesn't work

**Verify inside VM:**
```bash
ip addr show
ip route show
cat /etc/netplan/*.yaml
```

### Packages Not Installed

**Problem:** Specified packages are missing

**Solution:**
- Cloud-init may still be running (wait a few minutes)
- Check for package installation errors

**Verify:**
```bash
# Check cloud-init logs
sudo cat /var/log/cloud-init-output.log

# Check for errors
sudo cloud-init analyze show

# Manually install if needed
sudo apt update
sudo apt install <package-name>
```

### Commands Didn't Run

**Problem:** Custom commands in runcmd didn't execute

**Solution:**
- Check cloud-init logs for errors
- Verify command syntax (must be valid shell commands)
- Commands run as root by default

**Check logs:**
```bash
sudo cat /var/log/cloud-init-output.log
sudo journalctl -u cloud-final
```

---

## Technical Details

### User-Data File Format

Cloud-init uses YAML format with a special header:

```yaml
#cloud-config
hostname: my-vm
manage_etc_hosts: true

users:
  - name: admin
    shell: /bin/bash
    ssh_authorized_keys:
      - ssh-rsa AAAAB3NzaC1yc2E...
    sudo: ALL=(ALL) NOPASSWD:ALL
    groups:
      - sudo

packages:
  - openssh-server
  - vim
  - git

package_update: true
package_upgrade: true

runcmd:
  - systemctl enable ssh
  - systemctl start ssh
```

### Storage Location

User-data files are stored on the Proxmox host:

```
/var/lib/vz/snippets/user-data-vm<VMID>.yml
```

Example:
```
/var/lib/vz/snippets/user-data-vm105.yml
/var/lib/vz/snippets/user-data-vm106.yml
```

### VM Configuration

Cloud-init is attached to VMs using the `cicustom` parameter:

```bash
qm set <VMID> --cicustom 'user=local:snippets/user-data-vm<VMID>.yml'
```

Network settings are configured separately:

```bash
qm set <VMID> --ipconfig0 'ip=192.168.1.100/24,gw=192.168.1.1'
qm set <VMID> --nameserver '8.8.8.8'
qm set <VMID> --searchdomain 'local'
```

### Cloud-Init Stages

Cloud-init runs in multiple stages:

1. **cloud-init-local** (early boot)
   - Determine data sources
   - Apply networking config

2. **cloud-init** (network is up)
   - Retrieve instance data
   - Apply configuration modules

3. **cloud-config** (after network)
   - Run config modules
   - Install packages
   - Create users
   - Configure SSH

4. **cloud-final** (final stage)
   - Run runcmd scripts
   - Final modules
   - Signal completion

### Logs and Debugging

Important log files inside the VM:

```bash
# Main cloud-init output
/var/log/cloud-init-output.log

# Cloud-init internal logs
/var/log/cloud-init.log

# Check status
cloud-init status
cloud-init status --long

# Analyze boot time
cloud-init analyze show
cloud-init analyze dump

# View user-data that was applied
cloud-init query userdata
```

### Requirements

#### Proxmox Host
- Proxmox VE 7.0 or higher
- Snippets storage enabled: `pvesm set local --content vztmpl,iso,snippets`
- SSH access for uploading user-data files

#### VM Template
- Ubuntu 24.04 (Noble) cloud image or similar
- Cloud-init package installed
- Cloud-init drive configured (ide2 or scsi2)
- NoCloud data source enabled

#### Python Dependencies
```
paramiko==3.5.0    # For SSH file upload
PyYAML==6.0.2      # For YAML generation
proxmoxer==2.1.0   # For Proxmox API calls
```

---

## API Reference

### Clone VM with Cloud-Init

**Endpoint:** `POST /api/v1/templates/clone`

**Request Body:**
```json
{
  "source_vmid": 9000,
  "name": "my-ubuntu-vm",
  "cores": 2,
  "memory": 2048,
  "full_clone": true,
  "start_after_clone": true,
  "cloudinit": {
    "ipconfig": "ip=192.168.1.175/24,gw=192.168.1.1",
    "nameserver": "8.8.8.8",
    "searchdomain": "local",
    "users": [
      {
        "username": "admin",
        "ssh_keys": ["ssh-rsa AAAAB3NzaC1yc2E..."],
        "sudo": true,
        "groups": ["sudo", "docker"]
      }
    ],
    "packages": ["vim", "git", "docker.io"],
    "runcmd": [
      "systemctl enable docker",
      "systemctl start docker"
    ]
  }
}
```

**Response:**
```json
{
  "vmid": 105,
  "name": "my-ubuntu-vm",
  "node": "bestia",
  "status": "started",
  "message": "VM 105 cloned and started successfully",
  "task_id": "UPID:bestia:..."
}
```

---

## Best Practices

### Security

✅ **Use SSH keys** instead of passwords
✅ **Grant sudo carefully** - only to trusted users
✅ **Use strong SSH key types** - ed25519 or RSA 4096-bit
✅ **Limit groups** - only add necessary groups
✅ **Review custom commands** - they run as root

### Networking

✅ **Use static IPs** for servers
✅ **Document IP assignments** to avoid conflicts
✅ **Use correct gateway** for your network
✅ **Set appropriate DNS servers**

### Packages

✅ **Install only needed packages** - reduces attack surface
✅ **Keep package list small** - faster deployment
✅ **Use specific package names** - avoid wildcards
✅ **openssh-server is automatic** - don't add it manually

### Custom Commands

✅ **Test commands first** - in a test VM
✅ **Use full paths** - /usr/bin/systemctl instead of systemctl
✅ **Check for errors** - add error handling
✅ **Keep it simple** - complex scripts should be in separate files

---

## Additional Resources

### Official Documentation

- [Cloud-Init Documentation](https://cloudinit.readthedocs.io/)
- [Ubuntu Cloud Images](https://cloud-images.ubuntu.com/)
- [Proxmox Cloud-Init](https://pve.proxmox.com/wiki/Cloud-Init_Support)

### Example Cloud-Config Files

See the `/var/lib/vz/snippets/` directory on your Proxmox host for examples of generated user-data files.

### Support

For issues or questions:
1. Check the troubleshooting section above
2. Review cloud-init logs in `/var/log/cloud-init*.log`
3. Check Proxmox system logs
4. Review backend API logs

---

## Summary

This cloud-init implementation provides a powerful, automated way to deploy and configure Ubuntu VMs in Proxmox. Key benefits:

✅ **Automated Configuration** - No manual setup required
✅ **Consistent Deployments** - Same config every time
✅ **Secure by Default** - SSH key authentication, sudo control
✅ **Fast Deployment** - 2-3 minutes from click to SSH access
✅ **Flexible** - Supports users, packages, networking, and custom scripts

The implementation includes:
- **Backend:** Python cloud-init utilities in `app/utils/cloudinit.py`
- **Frontend:** React UI with comprehensive cloud-init form
- **Automatic:** openssh-server always installed and started
- **Production-Ready:** Tested and working with Ubuntu 24.04

Start deploying customized VMs in minutes! 🚀
