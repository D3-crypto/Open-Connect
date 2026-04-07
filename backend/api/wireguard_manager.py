import subprocess
import logging

logger = logging.getLogger(__name__)

WIREGUARD_INTERFACE = "wg0"

def get_next_available_ip():
    """
    Very basic IP allocation for MVP.
    In a production system, this would query the DB to find the highest assigned 10.7.0.x IP
    and return the next one.
    """
    from .models import Device
    
    # Get all currently assigned IPs that start with 10.7.0.
    devices_with_ips = Device.objects.filter(wireguard_ip__startswith='10.7.0.').values_list('wireguard_ip', flat=True)
    
    if not devices_with_ips:
        return "10.7.0.2" # .1 is usually the server itself
        
    highest_last_octet = 1
    for ip in devices_with_ips:
        try:
            last_octet = int(ip.split('.')[-1])
            if last_octet > highest_last_octet:
                highest_last_octet = last_octet
        except ValueError:
            continue
            
    next_octet = highest_last_octet + 1
    if next_octet > 254:
        raise Exception("Subnet exhausted! Time to upgrade to a /16 subnet.")
        
    return f"10.7.0.{next_octet}"

def add_wireguard_peer(public_key, assigned_ip):
    """
    Executes the wg kernel command to add a peer.
    Using subprocess.run with an array to prevent shell injection.
    """
    try:
        # Command: wg set wg0 peer <public_key> allowed-ips <assigned_ip>/32
        result = subprocess.run(
            ["wg", "set", WIREGUARD_INTERFACE, "peer", public_key, "allowed-ips", f"{assigned_ip}/32"],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"Successfully added WG peer {public_key[:8]}... with IP {assigned_ip}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.error(f"Failed to add WG peer. Error: {e}")
        # Note: We won't raise an exception here during dev if WireGuard isn't installed locally
        return False
