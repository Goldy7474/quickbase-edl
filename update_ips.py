import socket
import sys

# רשימת הדומיינים של Quickbase לפענוח
DOMAINS = [
    "quickbase.com",
    "www.quickbase.com",
    "api.quickbase.com",
    "identity.quickbase.com",
]

OUTPUT_FILE = "quickbase_ips.txt"

def resolve_domains(domains):
    ip_addresses = set()
    for domain in domains:
        try:
            results = socket.getaddrinfo(domain, None)
            for res in results:
                ip = res[4][0]
                ip_addresses.add(ip)
            print(f"[SUCCESS] Resolved {domain}")
        except socket.gaierror as e:
            print(f"[ERROR] Could not resolve {domain}: {e}", file=sys.stderr)
            
    return sorted(list(ip_addresses))

def main():
    ips = resolve_domains(DOMAINS)
    if not ips:
        print("[ERROR] No IPs resolved. Aborting to protect existing file.")
        sys.exit(1)
        
    with open(OUTPUT_FILE, "w") as f:
        for ip in ips:
            f.write(f"{ip}\n")
            
    print(f"[INFO] Successfully updated {OUTPUT_FILE} with {len(ips)} IPs.")

if __name__ == "__main__":
    main()
