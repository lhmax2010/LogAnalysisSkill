"""Acceptance-only proof that configured real endpoints are remote and direct."""
import fcntl
import ipaddress
from pathlib import Path
import socket
import struct
from urllib.parse import urlsplit
from .errors import FlowError
from .transport import direct_host


def address(value):
    ip = ipaddress.ip_address(value.split('%', 1)[0])
    return ip.ipv4_mapped if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped else ip


def local_addresses():
    found = {address('127.0.0.1'), address('::1')}
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        for _, name in socket.if_nameindex():
            try:
                raw = fcntl.ioctl(sock.fileno(), 0x8915, struct.pack('256s', name.encode()[:15]))
                found.add(address(socket.inet_ntoa(raw[20:24])))
            except OSError:
                pass
    source = Path('/proc/net/if_inet6')
    if source.exists():
        for line in source.read_text().splitlines():
            found.add(ipaddress.ip_address(int(line.split()[0], 16)))
    return found


def prove_remote(url, network):
    parsed = urlsplit(url)
    host = parsed.hostname
    if not direct_host(host, network.get('no_proxy_hosts', [])):
        raise FlowError(2, 'real_instance_must_be_direct')
    try:
        resolved = {address(item[4][0]) for item in socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme=='https' else 80), type=socket.SOCK_STREAM)}
    except (OSError, ValueError):
        raise FlowError(2, 'real_instance_resolution_failed') from None
    local = local_addresses()
    if not resolved or any(ip.is_loopback or ip.is_unspecified or ip.is_link_local or ip in local for ip in resolved):
        raise FlowError(2, 'real_backend_requires_non_loopback_instance')
    return {'resolved_ips': sorted(str(ip) for ip in resolved), 'direct': True}


def peer_is_remote(response):
    try:
        peer, local = address(response['peer_ip']), address(response['local_ip'])
        return peer != local and not (peer.is_loopback or peer.is_unspecified or peer.is_link_local) and peer not in local_addresses()
    except (KeyError, ValueError):
        return False
