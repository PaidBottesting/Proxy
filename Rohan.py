import socket
import socks
import time

# Proxy list to test
proxies = [
    ("159.223.202.0", 8080),
    ("34.124.190.108", 8080),
    ("74.122.101.11", 25340),
    ("199.102.104.70", 4145),
]

# Test parameters
TEST_HOST = "8.8.8.8"  # Public DNS server
TEST_PORT = 53         # DNS port (UDP)
TIMEOUT = 5            # Seconds to wait

def test_proxy(proxy_ip, proxy_port):
    try:
        sock = socks.socksocket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.set_proxy(socks.SOCKS5, proxy_ip, proxy_port)
        sock.settimeout(TIMEOUT)
        dns_query = b"\x00\x01\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x03www\x06google\x03com\x00\x00\x01\x00\x01"
        sock.sendto(dns_query, (TEST_HOST, TEST_PORT))
        sock.recvfrom(1024)
        print(f"Proxy {proxy_ip}:{proxy_port} supports UDP")
        return True
    except (socks.ProxyError, socket.timeout, socket.error) as e:
        print(f"Proxy {proxy_ip}:{proxy_port} does NOT support UDP or is dead ({str(e)})")
        return False
    finally:
        sock.close()

# Test all proxies
for proxy_ip, proxy_port in proxies:
    test_proxy(proxy_ip, proxy_port)