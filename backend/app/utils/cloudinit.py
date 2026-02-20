"""Cloud-init utilities for generating user-data and applying configuration"""
import yaml
from typing import Dict, Any, Optional
from app.schemas.template import CloudInitConfig


def generate_user_data(config: CloudInitConfig, hostname: str) -> str:
    """
    Generate cloud-init user-data YAML from configuration

    Args:
        config: CloudInitConfig object
        hostname: VM hostname

    Returns:
        YAML string for cloud-init user-data
    """
    user_data: Dict[str, Any] = {
        '#cloud-config': None,  # This will be serialized as just "#cloud-config"
        'hostname': hostname,
        'manage_etc_hosts': True,
    }

    # Remove the special marker - we'll add it manually
    user_data.pop('#cloud-config')
    user_data_dict = {
        'hostname': hostname,
        'manage_etc_hosts': True,
    }

    # Add users
    if config.users:
        users_list = []
        for user_config in config.users:
            user_dict: Dict[str, Any] = {
                'name': user_config.username,
                'shell': '/bin/bash',
            }

            if user_config.password:
                user_dict['passwd'] = user_config.password
                user_dict['lock_passwd'] = False

            if user_config.ssh_keys:
                user_dict['ssh_authorized_keys'] = user_config.ssh_keys

            if user_config.sudo:
                user_dict['sudo'] = 'ALL=(ALL) NOPASSWD:ALL'

            if user_config.groups:
                user_dict['groups'] = user_config.groups
            else:
                user_dict['groups'] = []

            # Always add sudo group if sudo privileges are granted
            if user_config.sudo and 'sudo' not in user_dict['groups']:
                user_dict['groups'].append('sudo')

            users_list.append(user_dict)

        user_data_dict['users'] = users_list

    # Add packages
    packages_list = []

    # Always include openssh-server for SSH access
    packages_list.append('openssh-server')

    if config.packages:
        # Add user-specified packages, avoiding duplicates
        for pkg in config.packages:
            if pkg not in packages_list:
                packages_list.append(pkg)

    if packages_list:
        user_data_dict['packages'] = packages_list
        user_data_dict['package_update'] = True
        user_data_dict['package_upgrade'] = True

    # Add run commands
    runcmd_list = [
        # Ensure SSH service is enabled and started
        'systemctl enable ssh',
        'systemctl start ssh'
    ]

    if config.runcmd:
        # Add user-specified commands after SSH setup
        runcmd_list.extend(config.runcmd)

    if runcmd_list:
        user_data_dict['runcmd'] = runcmd_list

    # Generate YAML
    yaml_content = yaml.dump(user_data_dict, default_flow_style=False, sort_keys=False)

    # Add cloud-config header
    return f"#cloud-config\n{yaml_content}"


def parse_ipconfig(ipconfig_str: str) -> Dict[str, str]:
    """
    Parse ipconfig string into Proxmox format

    Args:
        ipconfig_str: IP configuration string (e.g., 'ip=192.168.1.100/24,gw=192.168.1.1')

    Returns:
        Dictionary with parsed IP configuration
    """
    config = {}

    if not ipconfig_str:
        return {'ip': 'dhcp'}

    # If it's already in Proxmox format, return as is
    if '=' in ipconfig_str and ',' in ipconfig_str:
        return {'ipconfig0': ipconfig_str}

    # Otherwise parse individual components
    parts = ipconfig_str.split(',')
    for part in parts:
        if '=' in part:
            key, value = part.split('=', 1)
            config[key.strip()] = value.strip()

    return {'ipconfig0': ipconfig_str} if config else {'ip': 'dhcp'}


def apply_basic_cloudinit(
    proxmox_service,
    node: str,
    vmid: int,
    config: CloudInitConfig
) -> None:
    """
    Apply basic cloud-init configuration using Proxmox built-in support

    This uses Proxmox's native cloud-init parameters (ciuser, cipassword, ipconfig, etc.)
    This is simpler but more limited than custom user-data.

    Args:
        proxmox_service: ProxmoxService instance
        node: Node name
        vmid: VM ID
        config: CloudInitConfig object
    """
    update_params = {}

    # Network configuration
    if config.ipconfig:
        ip_config = parse_ipconfig(config.ipconfig)
        update_params.update(ip_config)

    if config.nameserver:
        update_params['nameserver'] = config.nameserver

    if config.searchdomain:
        update_params['searchdomain'] = config.searchdomain

    # Basic user configuration (only supports single user)
    if config.users and len(config.users) > 0:
        first_user = config.users[0]
        update_params['ciuser'] = first_user.username

        if first_user.password:
            update_params['cipassword'] = first_user.password

        if first_user.ssh_keys:
            # SSH keys need to be URL-encoded and newline-separated
            import urllib.parse
            ssh_keys_str = '\n'.join(first_user.ssh_keys)
            update_params['sshkeys'] = urllib.parse.quote(ssh_keys_str, safe='')

    if update_params:
        proxmox_service.update_vm_config(node, vmid, **update_params)


def upload_custom_userdata(
    settings,
    node: str,
    vmid: int,
    user_data: str
) -> str:
    """
    Upload custom user-data to Proxmox snippets storage via SSH

    Args:
        settings: Application settings
        node: Node name
        vmid: VM ID
        user_data: Cloud-init user-data YAML content

    Returns:
        Snippet path (e.g., 'local:snippets/user-data-vm101.yml')
    """
    import paramiko
    import io

    # Create SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Connect to Proxmox host
        ssh.connect(
            hostname=settings.proxmox_host,
            username='root',
            password=settings.proxmox_password,
            port=22
        )

        # Create snippets directory if it doesn't exist
        ssh.exec_command('mkdir -p /var/lib/vz/snippets')

        # Upload user-data file
        filename = f'user-data-vm{vmid}.yml'
        remote_path = f'/var/lib/vz/snippets/{filename}'

        sftp = ssh.open_sftp()
        sftp.putfo(io.BytesIO(user_data.encode('utf-8')), remote_path)
        sftp.close()

        return f'local:snippets/{filename}'

    finally:
        ssh.close()


def apply_custom_cloudinit(
    proxmox_service,
    settings,
    node: str,
    vmid: int,
    config: CloudInitConfig,
    hostname: str
) -> None:
    """
    Apply custom cloud-init configuration using user-data snippets

    This approach uploads a custom user-data YAML file and configures
    the VM to use it. Supports advanced features like multiple users,
    package installation, and custom commands.

    Args:
        proxmox_service: ProxmoxService instance
        settings: Application settings
        node: Node name
        vmid: VM ID
        config: CloudInitConfig object
        hostname: VM hostname
    """
    # Generate user-data YAML
    user_data = generate_user_data(config, hostname)

    # Upload to Proxmox snippets storage
    snippet_path = upload_custom_userdata(settings, node, vmid, user_data)

    # Configure VM to use the custom user-data
    update_params = {
        'cicustom': f'user={snippet_path}'
    }

    # Still apply network config via Proxmox if specified
    if config.ipconfig:
        ip_config = parse_ipconfig(config.ipconfig)
        update_params.update(ip_config)

    if config.nameserver:
        update_params['nameserver'] = config.nameserver

    if config.searchdomain:
        update_params['searchdomain'] = config.searchdomain

    proxmox_service.update_vm_config(node, vmid, **update_params)
