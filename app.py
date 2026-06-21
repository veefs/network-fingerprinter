from flask import Flask, render_template
import re
import requests
import subprocess

app = Flask(__name__)

def get_devices():
    result = subprocess.run(["arp", "-a"], capture_output=True, text=True)
    arp_output = result.stdout
    devices = []

    for line in arp_output.splitlines():
        if "192" in line and "Interface" not in line:
            parts = line.split()
            if len(parts) >= 2:
                ip = parts[0]
                mac = parts[1]
                ipType = parts[2]

                deviceType = requests.get(f"https://api.maclookup.app/v2/macs/{mac}/company/name")
               
                devices.append({
                    "ip": ip,
                    "mac": mac,
                    "ipType": ipType,
                    "deviceType": deviceType.text
                })

                ping = subprocess.run(["ping", ip], capture_output=True, text=True)
                ping_output = ping.stdout

                if "100% loss" in ping_output:
                    print("unreachable")

                else:
                    print("reachable")

                

    return devices

@app.route("/")

def index():
    devices = get_devices()
    return render_template("index.html", devices=devices)

if __name__ == "__main__":
    app.run(debug=True, port=5001)