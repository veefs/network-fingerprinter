import subprocess
import string

result = subprocess.run(["arp", "-a"], capture_output=True, text=True)
arp_output = result.stdout
devices = []

for line in arp_output.splitlines():
    if "    192" in line and "Interface" not in line:
        parts = line.split()
        if len(parts) >= 2:
            ip = parts[0]
            mac = parts[1]
            ipType = parts[2]
            devices.append({"ip": ip, "mac": mac, "ip type": ipType})

