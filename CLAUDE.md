# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Proxmox VM Deployer is a web interface to deploy VMs through a user-friendly form interface, either by creating new VMs from scratch or cloning from templates.

## Architecture

**Tech Stack:**
- Backend: Python API that interfaces with Proxmox API
- Frontend: React with dark theme and heroicons
- Configuration: .env files for Proxmox connection details (API URL, credentials, datastores, template names, cluster info, target nodes)

**API Flow:**
Frontend (React) → Backend API (Python) → Proxmox API

## Environment Details

**Proxmox Host:**
- IP: 192.168.1.150
- SSH access: root@192.168.1.150 (default SSH key available)
- Version: 8.3.5

**Infrastructure:**
- PBS Container ID: 200 (192.168.1.44)
- Backup datastore: usb-backup (/mnt/usb-backup on host, /mnt/datastore/pbs in PBS)
- USB backup disk: 938GB ext4 mounted at /mnt/usb-backup

## Features

**VM Deployment Options:**
1. Brand new VM creation - form with all inputs and helper tooltips
2. Clone VM templates - simplified form with template selection and helper tooltips

**Post-Deployment Validation:**
- Check Proxmox health status
- Test port connectivity:
  - Port 22 (SSH) for Linux VMs
  - Port 3389 (RDP) for Windows VMs
- Validate VM is alive after deployment

## Development Notes

- All configuration should use .env files (never hardcode credentials)
- SSH testing can be done directly to root@192.168.1.150 for exploration
- Refer to PROXMOX_BACKUP_SETUP.md for detailed infrastructure documentation