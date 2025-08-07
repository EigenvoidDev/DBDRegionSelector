import platform
import socket
import subprocess
import threading

from config import REGIONS, LATENCY_THRESHOLDS

ping_processes = {}
threads = {}
results = {}
lock = threading.Lock()


def resolve_hostname(hostname):
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror as e:
        print(f"Failed to resolve {hostname}: {e}")
        return None


def start_continuous_ping(host, result_dict, region_name):
    system = platform.system()

    if system == "Windows":
        cmd = ["ping", "-t", host]
        creationflags = subprocess.CREATE_NO_WINDOW
    else:
        cmd = ["ping", host]
        creationflags = 0

    def run():
        sent = 0
        received = 0

        try:
            with subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                creationflags=creationflags,
            ) as proc:
                ping_processes[region_name] = proc
                for line in proc.stdout:
                    if region_name not in result_dict:
                        break
                    latency = parse_latency(line)

                    if is_ping_reply(line):
                        sent += 1

                    if latency is not None:
                        received += 1
                        status = classify_latency(latency)
                        with lock:
                            result_dict[region_name].update(
                                {"latency_ms": latency, "status": status}
                            )

                    if sent > 0:
                        packet_loss = ((sent - received) / sent) * 100
                        with lock:
                            result_dict[region_name]["packet_loss_percentage"] = round(
                                packet_loss, 2
                            )
                            result_dict[region_name][
                                "packet_loss_str"
                            ] = f"{packet_loss:.2f}%"
        except Exception as e:
            print(f"[{region_name}] Continuous ping error: {e}")
            with lock:
                result_dict[region_name]["status"] = "error"

    thread = threading.Thread(target=run, daemon=True)
    threads[region_name] = thread
    thread.start()
    return thread


def is_ping_reply(line):
    return "time=" in line or "TTL=" in line or "ttl=" in line


def parse_latency(line):
    if "time=" in line:
        try:
            time_str = line.split("time=")[1].split()[0]
            return float(time_str.replace("ms", "").strip())
        except Exception as e:
            print(f"Latency parse error: {e} (line: {line})")
            return None
    elif "Average =" in line:
        try:
            parts = line.split("Average =")[-1]
            return float(parts.strip().replace("ms", ""))
        except Exception as e:
            print(f"Latency parse error: (Average): {e} (line: {line})")
            return None
    return None


def classify_latency(latency, error=None):
    if latency is None:
        return error if error else "no_response"
    elif latency <= LATENCY_THRESHOLDS["good"]:
        return "good"
    elif latency <= LATENCY_THRESHOLDS["ok"]:
        return "ok"
    else:
        return "bad"


def ping_all_regions():
    for region_name, region_data in REGIONS.items():
        hostname = region_data["service_endpoint"]
        ip = resolve_hostname(hostname)
        if ip:
            results[region_name] = {
                "region": region_data["region"],
                "hostname": hostname,
                "ip": ip,
                "latency_ms": None,
                "packet_loss_percentage": None,
                "status": "initializing",
            }
            start_continuous_ping(ip, results, region_name)
        else:
            results[region_name] = {
                "region": region_data["region"],
                "hostname": hostname,
                "ip": None,
                "latency_ms": None,
                "packet_loss_percentage": 100.0,
                "status": "unresolved",
            }

    return results


def terminate_all_pings():
    for region, proc in ping_processes.items():
        try:
            if proc.poll() is None:
                proc.terminate()
        except Exception as e:
            print(f"Error terminating ping for {region}: {e}")
    ping_processes.clear()
    threads.clear()