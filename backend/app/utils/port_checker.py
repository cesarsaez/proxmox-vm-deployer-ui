"""Port connectivity checking utilities"""
import asyncio
import socket
import time
from typing import Dict, Any


async def check_port_open(host: str, port: int, timeout: int = 5) -> Dict[str, Any]:
    """
    Check if a TCP port is open and responding

    Args:
        host: Hostname or IP address
        port: Port number
        timeout: Connection timeout in seconds

    Returns:
        Dictionary with check results
    """
    try:
        start_time = time.time()

        # Try to open a connection
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout
        )

        # Calculate latency
        latency = (time.time() - start_time) * 1000

        # Close connection
        writer.close()
        await writer.wait_closed()

        return {
            "passed": True,
            "reachable": True,
            "latency_ms": round(latency, 2),
            "message": f"Port {port} is open and responding"
        }

    except asyncio.TimeoutError:
        return {
            "passed": False,
            "reachable": False,
            "error": "Connection timeout",
            "message": f"Port {port} is not reachable (timeout)"
        }
    except ConnectionRefusedError:
        return {
            "passed": False,
            "reachable": False,
            "error": "Connection refused",
            "message": f"Port {port} is closed or refusing connections"
        }
    except socket.gaierror as e:
        return {
            "passed": False,
            "reachable": False,
            "error": f"DNS resolution failed: {str(e)}",
            "message": f"Cannot resolve hostname {host}"
        }
    except Exception as e:
        return {
            "passed": False,
            "reachable": False,
            "error": str(e),
            "message": f"Failed to check port {port}: {str(e)}"
        }


def check_port_sync(host: str, port: int, timeout: int = 5) -> Dict[str, Any]:
    """
    Synchronous version of port check

    Args:
        host: Hostname or IP address
        port: Port number
        timeout: Connection timeout in seconds

    Returns:
        Dictionary with check results
    """
    try:
        start_time = time.time()

        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)

        # Try to connect
        result = sock.connect_ex((host, port))

        # Calculate latency
        latency = (time.time() - start_time) * 1000

        sock.close()

        if result == 0:
            return {
                "passed": True,
                "reachable": True,
                "latency_ms": round(latency, 2),
                "message": f"Port {port} is open and responding"
            }
        else:
            return {
                "passed": False,
                "reachable": False,
                "error": f"Connection failed with code {result}",
                "message": f"Port {port} is not reachable"
            }

    except socket.timeout:
        return {
            "passed": False,
            "reachable": False,
            "error": "Connection timeout",
            "message": f"Port {port} is not reachable (timeout)"
        }
    except socket.gaierror as e:
        return {
            "passed": False,
            "reachable": False,
            "error": f"DNS resolution failed: {str(e)}",
            "message": f"Cannot resolve hostname {host}"
        }
    except Exception as e:
        return {
            "passed": False,
            "reachable": False,
            "error": str(e),
            "message": f"Failed to check port {port}: {str(e)}"
        }


async def check_multiple_ports(host: str, ports: list[int], timeout: int = 5) -> Dict[int, Dict[str, Any]]:
    """
    Check multiple ports concurrently

    Args:
        host: Hostname or IP address
        ports: List of port numbers
        timeout: Connection timeout in seconds

    Returns:
        Dictionary mapping port numbers to check results
    """
    tasks = [check_port_open(host, port, timeout) for port in ports]
    results = await asyncio.gather(*tasks)

    return {port: result for port, result in zip(ports, results)}
