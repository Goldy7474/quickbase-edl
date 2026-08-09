import socket
import sys
import ipaddress

# רשימת הדומיינים של Quickbase לתרגום (כולל Wildcards נפוצים ורכיבי SSO/Assets)
DOMAINS = [
    "quickbase.com",
    "www.quickbase.com",
    "api.quickbase.com",
    "identity.quickbase.com",
    "assets.quickbase.com",
    "content.quickbase.com",
    # אם יש לכם Realm ספציפי בארגון, הוסיפו אותו כאן:
    # "your-company-realm.quickbase.com",
]

# טווחי IP קבועים/ידועים של Quickbase (אם קיימים)
STATIC_NETWORKS = [
    # דוגמה מומלצת במידה ויש טווחי CIDR רשמיים:
    # "162.219.224.0/22"
]

OUTPUT_FILE = "quickbase_ips.txt"

def resolve_domains(domains):
    valid_entries = set()

    # 1. עיבוד טווחי IP/CIDR סטטיים
    for net_str in STATIC_NETWORKS:
        try:
            net_obj = ipaddress.ip_network(net_str, strict=False)
            valid_entries.add(str(net_obj))
        except ValueError as e:
            print(f"[ERROR] Invalid static network {net_str}: {e}", file=sys.stderr)

    # 2. תרגום דינמי של הדומיינים ואימות IPv4
    for domain in domains:
        try:
            results = socket.getaddrinfo(domain, None)
            resolved_any = False
            for res in results:
                ip_str = res[4][0]
                try:
                    ip_obj = ipaddress.ip_address(ip_str)
                    # סינון קפדני: רק IPv4 נכנס ל-EDL
                    if isinstance(ip_obj, ipaddress.IPv4Address):
                        valid_entries.add(str(ip_obj))
                        resolved_any = True
                except ValueError:
                    continue
            if resolved_any:
                print(f"[SUCCESS] Resolved {domain}")
        except socket.gaierror as e:
            print(f"[ERROR] Could not resolve {domain}: {e}", file=sys.stderr)
            
    return sorted(list(valid_entries))

def main():
    ips = resolve_domains(DOMAINS)
    if not ips:
        print("[ERROR] No valid IPv4s resolved. Aborting to protect existing file.", file=sys.stderr)
        sys.exit(1)
        
    with open(OUTPUT_FILE, "w") as f:
        for ip in ips:
            f.write(f"{ip}\n")
            
    print(f"[INFO] Successfully updated {OUTPUT_FILE} with {len(ips)} entries.")

if __name__ == "__main__":
    main()
