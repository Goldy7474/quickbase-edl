import socket
import sys
import ipaddress

# רשימת הדומיינים של Quickbase לתרגום דינמי
DOMAINS = [
    "quickbase.com",
    "www.quickbase.com",
    "api.quickbase.com",
    "identity.quickbase.com",
    "assets.quickbase.com",
    "content.quickbase.com",
    # הוסיפו כאן את ה-Realm הספציפי שלכם במידת הצורך:
    # "mycompany.quickbase.com",
]

# טווחי IP/CIDR קבועים ורשמיים של שרתי Quickbase / AWS
# כל רשת עוברת נרמול אוטומטי למניעת שגיאות סינטקס ב-PAN-OS
STATIC_NETWORKS = [
    "162.219.224.0/22",
    "18.205.0.0/16",
    "18.214.0.0/15",
    "52.200.0.0/14",     # תוקן מ-52.200.0.0/13 לסאבנט/CIDR תקין
]

OUTPUT_FILE = "quickbase_ips.txt"

def resolve_domains(domains):
    valid_entries = set()

    # 1. עיבוד ונרמול טווחי ה-IP הסטטיים
    for net_str in STATIC_NETWORKS:
        try:
            # strict=False ממיר אוטומטית כתובת Host לכתובת Network תקינה
            net_obj = ipaddress.ip_network(net_str, strict=False)
            valid_entries.add(str(net_obj))
        except ValueError as e:
            print(f"[ERROR] Invalid static network {net_str}: {e}", file=sys.stderr)

    # 2. תרגום דינמי של הדומיינים ואימות IPv4 בלבד
    for domain in domains:
        try:
            results = socket.getaddrinfo(domain, None)
            resolved_any = False
            for res in results:
                ip_str = res[4][0]
                try:
                    ip_obj = ipaddress.ip_address(ip_str)
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
