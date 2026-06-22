from flask import Flask, render_template, request, jsonify
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

                ping = subprocess.run(["ping", ip], capture_output=True, text=True)
                ping_output = ping.stdout

                reachability = "NA"

                if "100% loss" in ping_output:
                    print("unreachable")
                    reachability = "False"

                else:
                    print("reachable")
                    reachability = "True"
               
                devices.append({
                    "ip": ip,
                    "mac": mac,
                    "ipType": ipType,
                    "deviceType": deviceType.text,
                    "reachability": reachability
                })
    return devices

@app.route("/")

def index():
    devices = get_devices()
    return render_template("index.html", devices=devices)

known_ips = set()

def handle_options(option):

    parts = option.strip().split()

    if not parts:

        return {"status": "error", "result": "empty command"}

    command = parts[0]

    if command == "set":

        if len(parts) < 2:

            return {"status": "error", "result": "usage: set <ip>"}

        ip = parts[1]

        known_ips.add(ip)

        return {"status": "ok", "result": f"added {ip}"}

    elif command == "os":

        if len(parts) < 2:

            return {"status": "error", "result": "usage: os <ip>"}

        ip = parts[1]

        NMAP_PATH = r"C:\Program Files (x86)\Nmap\nmap.exe"
        
        scan_result = subprocess.run(

             [NMAP_PATH, "-O", ip], capture_output=True, text=True

        )

        return {"status": "ok", "result": scan_result.stdout}

    else:

        return {"status": "error", "result": f"unknown command: {command}"}

@app.route("/scan", methods=["POST"])

def scan():

    data = request.get_json()

    target_ip = data.get("target_ip")

    result = handle_options(target_ip)

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True, port=5001)


