import platform
import subprocess

from config import REGIONS

SECTION_START = "# DBDRegionSelectorHostsSectionStart"
SECTION_END = "# DBDRegionSelectorHostsSectionEnd"
ERROR_MESSAGE = "Administrator privileges required. Please run this application as an administrator."


def get_hosts_path():
    system = platform.system()
    if system == "Windows":
        return r"C:\Windows\System32\drivers\etc\hosts"
    elif system in ["Linux", "Darwin"]:  # Darwin = macOS
        return "/etc/hosts"
    else:
        raise Exception(f"Unsupported platform: {system}")


def build_hosts_section_lines(active_region=None, comment_all=False):
    lines = [
        SECTION_START,
        "# This section contains hosts file entries for DBD Region Selector that map domains to 0.0.0.0 to locally block access to specific regions.",
        "# Do not edit this section manually.",
        "",
    ]
    for region_name, region_data in REGIONS.items():
        hostname = region_data["udp_ping_beacon_endpoint"]
        if comment_all or region_name == active_region:
            lines.append(f"# 0.0.0.0 {hostname}")
        else:
            lines.append(f"0.0.0.0 {hostname}")
    lines.append("")
    lines.append(SECTION_END)
    return lines


def update_hosts_file(active_region=None, comment_all=False):
    hosts_path = get_hosts_path()

    try:
        with open(hosts_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except PermissionError:
        print(ERROR_MESSAGE)
        raise

    in_block = False
    new_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped == SECTION_START:
            in_block = True
            continue
        elif stripped == SECTION_END:
            in_block = False
            continue
        if not in_block:
            new_lines.append(line.rstrip("\n"))

    region_lines = build_hosts_section_lines(active_region, comment_all)
    new_lines.extend(region_lines)

    try:
        with open(hosts_path, "w", encoding="utf-8") as f:
            f.write("\n".join(new_lines) + "\n")
    except PermissionError:
        print(ERROR_MESSAGE)
        raise

    flush_dns_cache()


def initialize_hosts_file():
    hosts_path = get_hosts_path()

    try:
        with open(hosts_path, "r", encoding="utf-8") as f:
            content = f.read()
    except PermissionError:
        print(ERROR_MESSAGE)
        return

    if SECTION_START in content and SECTION_END in content:
        return

    lines = content.strip().splitlines()
    lines.extend(build_hosts_section_lines(comment_all=True))

    try:
        with open(hosts_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    except PermissionError:
        print(ERROR_MESSAGE)
        return

    flush_dns_cache()


def get_active_regions_from_hosts():
    hosts_path = get_hosts_path()
    active_regions = []

    try:
        with open(hosts_path, "r", encoding="utf-8") as f:
            in_block = False
            for line in f:
                stripped = line.strip()
                if stripped == SECTION_START:
                    in_block = True
                    continue
                elif stripped == SECTION_END:
                    break
                if in_block and stripped.startswith("# 0.0.0.0"):
                    for region_name, region_data in REGIONS.items():
                        if region_data["udp_ping_beacon_endpoint"] in stripped:
                            active_regions.append(region_name)
                            break
    except PermissionError:
        print(ERROR_MESSAGE)
        raise

    return active_regions


def flush_dns_cache():
    system = platform.system()
    try:
        if system == "Windows":
            subprocess.run(["ipconfig", "/flushdns"], check=True)
        elif system == "Linux":
            subprocess.run(["sudo", "systemd-resolve", "--flush-caches"], check=True)
        elif system == "Darwin":
            subprocess.run(["sudo", "dscacheutil", "-flushcache"], check=True)
            subprocess.run(["sudo", "killall", "-HUP", "mDNSResponder"], check=True)
        else:
            print(f"Unsupported platform: {system}")
    except Exception as e:
        print(f"Failed to flush DNS cache: {e}")
