import sys
import socket
import ipaddress

# רשימת הדומיינים של Quickbase לתרגום דינמי
DOMAINS = [
    "quickbase.com",
    "www.quickbase.com",
    "api.quickbase.com",
    "identity.quickbase.com",
    "assets.quickbase.com",
    "content.quickbase.com",
    # "mycompany.quickbase.com", # Realm ספציפי במידת הצורך
]

# טווחי IP/CIDR קבועים ורשמיים של שרתי Quickbase / AWS
STATIC_NETWORKS = [
    "162.219.224.0/22",
    "18.205.0.0/16",
    "18.214.0.0/15",
    "52.200.0.0/14",
]

OUTPUT_FILE = "quickbase_ips.txt"

def resolve_domains(domains):
    valid_entries = set()

    # הגדרת Timeout של 5 שניות לכל שאילתת DNS
    socket.setdefaulttimeout(5)

    # 1. עיבוד ונרמול טווחי ה-IP הסטטיים
    for net_str in STATIC_NETWORKS:
        try:
            net_obj = ipaddress.ip_network(net_str, strict=False)
            
            # סינון רשתות פרטיות או לא תקינות
            if not (net_obj.is_private or net_obj.is_loopback or net_obj.is_unspecified):
                valid_entries.add(str(net_obj))
            else:
                print(f"[WARN] Ignored private static network: {net_str}", file=sys.stderr)
        except ValueError as e:
            print(f"[ERROR] Invalid static network {net_str}: {e}", file=sys.stderr)

    # 2. תרגום דינמי של הדומיינים ואימות IPv4 בלבד
    for domain in domains:
        try:
            # AF_INET מחזיר רק כתובות IPv4 ברמת ה-socket
            results = socket.getaddrinfo(domain, None, socket.AF_INET)
            resolved_any = False
            
            for res in results:
                ip_str = res[4][0]
                try:
                    ip_obj = ipaddress.ip_address(ip_str)
                    
                    # אימות שזוהי כתובת IPv4 פומבית ותקינה
                    if isinstance(ip_obj, ipaddress.IPv4Address):
                        if not (ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_unspecified):
                            valid_entries.add(str(ip_obj))
                            resolved_any = True
                        else:
                            print(f"[WARN] Ignored private IP for {domain}: {ip_str}", file=sys.stderr)
                except ValueError:
                    continue
                    
            if resolved_any:
                print(f"[SUCCESS] Resolved {domain}")
        except (socket.gaierror, socket.timeout) as e:
            print(f"[ERROR] Could not resolve {domain}: {e}", file=sys.stderr)
            
    return sorted(list(valid_entries))

def main():
    ips = resolve_domains(DOMAINS)
    
    # מנגנון Fail-Safe: מצפים לפחות לטווחים הסטטיים + כתובות פומביות מהדומיינים
    min_expected_entries = len(STATIC_NETWORKS) + 1
    
    if len(ips) < min_expected_entries:
        print(f"[ERROR] Resolved only {len(ips)} entries. Expected at least {min_expected_entries}.", file=sys.stderr)
        print("[ERROR] Aborting file write to protect existing Palo Alto EDL.", file=sys.stderr)
        sys.exit(1) # הכשלת ה-Action במכוון
        
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for ip in ips:
            f.write(f"{ip}\n")
            
    print(f"[INFO] Successfully updated {OUTPUT_FILE} with {len(ips)} entries.")

if __name__ == "__main__":
    main()
