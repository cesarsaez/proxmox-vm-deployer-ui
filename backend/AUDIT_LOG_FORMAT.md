# Audit Log Format Documentation

## Overview

The Proxmox VM Deployer audit system logs all VM deployment and cloning operations to `logs/audit.log` in **JSON Lines** format (one JSON object per line). This format is optimized for programmatic parsing and database ingestion.

## Log File Location

```
logs/audit.log          # Current audit log
logs/audit.log.1        # Rotated log (previous 10MB)
logs/audit.log.2        # Older rotated log
...
logs/audit.log.10       # Oldest rotated log (auto-deleted)
```

**Rotation**: Automatically rotates when file reaches 10MB, keeps 10 backup files.

## JSON Lines Format

Each line is a complete JSON object. This makes it easy to:
- Parse line-by-line without loading entire file
- Stream into databases (MongoDB, PostgreSQL JSON)
- Process with command-line tools (`jq`, `grep`, etc.)
- Import into log aggregation systems (ELK, Splunk, Graylog)

## Common Fields

All audit entries contain these fields:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `timestamp` | string | ISO 8601 UTC timestamp | `2026-02-09T18:30:45.123Z` |
| `operation` | string | Operation type | `vm_creation`, `template_clone`, `batch_clone` |
| `operation_type` | string | Category | `create`, `clone`, `batch`, `validate` |
| `username` | string | Proxmox username used | `root@pam` |
| `status` | string | Operation result | `success`, `failed`, `partial` |

## Operation Types

### 1. VM Creation (`operation: "vm_creation"`)

Logged when creating a new VM from scratch.

**Example Entry:**
```json
{
  "timestamp": "2026-02-09T18:30:45.123Z",
  "operation": "vm_creation",
  "operation_type": "create",
  "username": "root@pam",
  "status": "success",
  "vm_name": "win-server-01",
  "vm_id": 105,
  "configuration": {
    "cores": 4,
    "sockets": 1,
    "cpu_type": "host",
    "memory_mb": 8192,
    "disk_size_gb": 100,
    "storage": "local-lvm",
    "network_bridge": "vmbr0",
    "network_model": "virtio",
    "os_type": "windows",
    "bios": "ovmf",
    "machine": "q35",
    "iso": "local:iso/windows-server-2022.iso",
    "virtio_iso": "local:iso/virtio-win-0.1.266.iso",
    "enable_guest_agent": true,
    "start_on_creation": false,
    "tags": ["production", "web-server"]
  },
  "node": "bestia",
  "task_id": "UPID:bestia:00001234:00005678:65C6D8A5:qmcreate:105:root@pam:",
  "error": null
}
```

**Fields Specific to VM Creation:**

| Field | Type | Description |
|-------|------|-------------|
| `vm_name` | string | Name of the VM |
| `vm_id` | integer | VM ID (auto-assigned if null in request) |
| `configuration.cores` | integer | Number of CPU cores |
| `configuration.sockets` | integer | Number of CPU sockets |
| `configuration.cpu_type` | string | CPU type (host, kvm64, qemu64) |
| `configuration.memory_mb` | integer | RAM in megabytes |
| `configuration.disk_size_gb` | integer | Disk size in gigabytes |
| `configuration.storage` | string | Storage pool name |
| `configuration.network_bridge` | string | Network bridge |
| `configuration.network_model` | string | Network card model |
| `configuration.os_type` | string | OS type (linux, windows) |
| `configuration.bios` | string | BIOS type (seabios, ovmf) |
| `configuration.machine` | string | Machine type (q35, i440fx) |
| `configuration.iso` | string | Installation ISO volid |
| `configuration.virtio_iso` | string | VirtIO drivers ISO (Windows) |
| `configuration.enable_guest_agent` | boolean | Guest agent enabled |
| `configuration.start_on_creation` | boolean | Auto-start after creation |
| `configuration.tags` | array | List of tags |
| `node` | string | Proxmox node name |
| `task_id` | string | Proxmox task ID (UPID) |
| `error` | string | Error message (null if successful) |

---

### 2. Template Clone (`operation: "template_clone"`)

Logged when cloning a VM from a template.

**Example Entry:**
```json
{
  "timestamp": "2026-02-09T18:35:12.456Z",
  "operation": "template_clone",
  "operation_type": "clone",
  "username": "root@pam",
  "status": "success",
  "source_template": {
    "template_id": 9000,
    "template_name": "ubuntu-noble-template"
  },
  "vm_name": "web-server-02",
  "vm_id": 106,
  "configuration": {
    "cores": 4,
    "memory_mb": 8192,
    "storage": "local-lvm",
    "full_clone": true,
    "start_after_clone": false,
    "tags": ["staging", "web"]
  },
  "node": "bestia",
  "task_id": "UPID:bestia:00001235:00005679:65C6D8B0:qmclone:9000:root@pam:",
  "error": null
}
```

**Fields Specific to Template Clone:**

| Field | Type | Description |
|-------|------|-------------|
| `source_template.template_id` | integer | Source template VM ID |
| `source_template.template_name` | string | Source template name |
| `vm_name` | string | Name of the new VM |
| `vm_id` | integer | New VM ID |
| `configuration.cores` | integer | CPU cores (can override template) |
| `configuration.memory_mb` | integer | RAM in MB (can override template) |
| `configuration.storage` | string | Target storage |
| `configuration.full_clone` | boolean | Full clone vs linked clone |
| `configuration.start_after_clone` | boolean | Auto-start after clone |
| `configuration.tags` | array | List of tags |
| `node` | string | Proxmox node name |
| `task_id` | string | Proxmox task ID |
| `error` | string | Error message (null if successful) |

---

### 3. Batch Operations (`operation_type: "batch"`)

Logged for batch cloning or batch VM creation.

**Example Entry:**
```json
{
  "timestamp": "2026-02-09T18:40:00.789Z",
  "operation": "batch_clone",
  "operation_type": "batch",
  "username": "root@pam",
  "status": "partial",
  "summary": {
    "total_requested": 5,
    "successful": 4,
    "failed": 1,
    "success_rate": "80.0%"
  },
  "operations": [
    {
      "vm_name": "kube-node-01",
      "vm_id": 107,
      "status": "created",
      "message": "VM 107 cloned successfully"
    },
    {
      "vm_name": "kube-node-02",
      "vm_id": 108,
      "status": "created",
      "message": "VM 108 cloned successfully"
    },
    {
      "vm_name": "kube-node-03",
      "vm_id": 109,
      "status": "created",
      "message": "VM 109 cloned successfully"
    },
    {
      "vm_name": "kube-node-04",
      "vm_id": 110,
      "status": "created",
      "message": "VM 110 cloned successfully"
    },
    {
      "vm_name": "kube-node-05",
      "vm_id": 0,
      "status": "failed",
      "message": "Failed: Storage full"
    }
  ]
}
```

**Fields Specific to Batch Operations:**

| Field | Type | Description |
|-------|------|-------------|
| `operation` | string | `batch_clone` or `batch_create` |
| `status` | string | `success` (all OK) or `partial` (some failed) |
| `summary.total_requested` | integer | Total VMs requested |
| `summary.successful` | integer | Number of successful operations |
| `summary.failed` | integer | Number of failed operations |
| `summary.success_rate` | string | Success percentage |
| `operations` | array | Individual operation results |
| `operations[].vm_name` | string | VM name |
| `operations[].vm_id` | integer | VM ID (0 if failed) |
| `operations[].status` | string | Operation status |
| `operations[].message` | string | Status message |

---

### 4. Validation (`operation: "validation"`)

Logged for post-deployment validation checks.

**Example Entry:**
```json
{
  "timestamp": "2026-02-09T18:45:30.123Z",
  "operation": "validation",
  "operation_type": "validate",
  "username": "root@pam",
  "vm_id": 107,
  "vm_name": "kube-node-01",
  "validation_status": "healthy",
  "checks": {
    "proxmox_status": {
      "passed": true,
      "message": "VM is running"
    },
    "ip_address": {
      "passed": true,
      "message": "IP: 192.168.1.200"
    },
    "ssh_port": {
      "passed": true,
      "message": "Port 22 is reachable"
    }
  }
}
```

---

## Parsing Examples

### Command Line (jq)

```bash
# View all successful operations
jq 'select(.status == "success")' logs/audit.log

# Count operations by type
jq -r '.operation' logs/audit.log | sort | uniq -c

# Find all Windows VMs created
jq 'select(.operation == "vm_creation" and .configuration.os_type == "windows")' logs/audit.log

# Find failures
jq 'select(.status == "failed")' logs/audit.log

# Get VM creations in last hour
jq 'select(.timestamp > "'$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S)'Z")' logs/audit.log

# Extract VM names and IDs
jq -r '[.timestamp, .vm_name, .vm_id] | @csv' logs/audit.log
```

### Python Parser

```python
import json
from datetime import datetime

def parse_audit_log(log_file='logs/audit.log'):
    """Parse audit log and return list of entries"""
    entries = []
    with open(log_file, 'r') as f:
        for line in f:
            entry = json.loads(line.strip())
            entries.append(entry)
    return entries

# Get all VM creations
entries = parse_audit_log()
vm_creations = [e for e in entries if e['operation'] == 'vm_creation']

# Count by status
from collections import Counter
status_counts = Counter(e['status'] for e in entries)
print(status_counts)  # {'success': 45, 'failed': 3, 'partial': 2}
```

### PostgreSQL Import

```sql
-- Create table
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP,
    operation VARCHAR(50),
    operation_type VARCHAR(20),
    username VARCHAR(100),
    status VARCHAR(20),
    vm_name VARCHAR(255),
    vm_id INTEGER,
    configuration JSONB,
    node VARCHAR(100),
    task_id TEXT,
    error TEXT,
    raw_data JSONB
);

-- Import from JSON Lines
-- Use Python script or pg_bulkload
```

### MongoDB Import

```bash
# Import JSON Lines directly
mongoimport --db proxmox --collection audit_log \
  --file logs/audit.log --jsonArray=false

# Query in MongoDB
db.audit_log.find({ status: "success" })
db.audit_log.find({ "configuration.os_type": "windows" })
db.audit_log.aggregate([
  { $group: { _id: "$operation", count: { $sum: 1 } } }
])
```

---

## Utility Scripts

See `backend/scripts/parse_audit_log.py` for a complete parser with:
- CSV export
- Statistics generation
- Database import helpers
- Filtering by date/user/status

---

## Log Rotation

Logs rotate automatically:
- **Trigger**: When file reaches 10MB
- **Backups**: Keeps 10 rotated files
- **Naming**: `audit.log.1`, `audit.log.2`, etc.
- **Oldest**: Automatically deleted when exceeding 10 backups

To adjust rotation settings, edit `backend/app/services/audit_service.py`:

```python
handler = RotatingFileHandler(
    self.log_file,
    maxBytes=10 * 1024 * 1024,  # Change to 50MB
    backupCount=20,              # Keep 20 backups
    encoding='utf-8'
)
```

---

## Security Considerations

- **No Passwords**: Audit logs never contain passwords
- **File Permissions**: Ensure logs are readable only by authorized users
- **Retention Policy**: Define how long to keep logs (compliance requirements)
- **Encryption**: Consider encrypting log files at rest
- **Access Control**: Restrict log file access to admin users only

---

## Compliance and Reporting

The audit log format supports:
- **SOC 2 Compliance**: Comprehensive activity logging
- **GDPR**: Track data processing operations
- **Change Management**: Document infrastructure changes
- **Incident Response**: Trace VM deployment history
- **Capacity Planning**: Analyze resource allocation patterns

---

## Support

For questions about audit logging:
- Review this documentation
- Check `backend/app/services/audit_service.py` source code
- See example parser: `backend/scripts/parse_audit_log.py`
