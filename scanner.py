import nmap
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

def scan_port(host, port, nm_scanner=None, timeout=3):
    """Scan single port using python-nmap if available, otherwise TCP connect."""
    result = {"port": port, "state": "unknown", "service": None, "protocol": None}
    try:
        if nm_scanner:
            scan = nm_scanner.scan(hosts=str(host), ports=str(port), arguments='-sV -Pn --host-timeout 10s')
            # parse
            host_data = scan.get('scan', {}).get(host, {})
            tcp = host_data.get('tcp', {})
            port_info = tcp.get(port, {})
            if port_info:
                result["state"] = port_info.get("state", "unknown")
                result["service"] = port_info.get("name") or port_info.get("product")
                result["protocol"] = port_info.get("extrainfo")
            else:
                # fallback to socket connect
                raise Exception("No nmap tcp info")
        else:
            raise Exception("No nmap scanner")
    except Exception:
        # Fallback: simple TCP connect
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                code = s.connect_ex((host, port))
                if code == 0:
                    result["state"] = "open"
                else:
                    result["state"] = "closed"
        except Exception as e:
            result["state"] = f"error: {e}"
    return result

def scan_ports(host, ports, threads=50, use_nmap=True):
    """
    Scan a list of ports on host.
    ports: iterable of ints
    """
    nm = None
    if use_nmap:
        try:
            nm = nmap.PortScanner()
        except Exception:
            nm = None
    results = []
    with ThreadPoolExecutor(max_workers=threads) as ex:
        futures = {ex.submit(scan_port, host, p, nm_scanner=nm): p for p in ports}
        for fut in as_completed(futures):
            res = fut.result()
            results.append(res)
    # sort by port
    return sorted(results, key=lambda x: x["port"])