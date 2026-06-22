from flask import Flask, render_template, request, jsonify
import re
import requests
import subprocess
import sys
import os
import webbrowser
import threading


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller onefile bundles."""
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


app = Flask(
    __name__,
    template_folder=resource_path("templates"),
    static_folder=resource_path("static"),
)

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

current_target = {"ip": None}

def handle_options(option):

    parts = option.strip().split()

    if not parts:

        return {"status": "error", "result": "empty command"}

    command = parts[0]

    if command == "help":

        if len(parts) > 1:

            return {"status": "error", "result": "usage: help"}

        return {"status": "ok", "result": f"Current commands are: set <ip>, os, curl, ports"}

    elif command == "set":

        if len(parts) < 2:

            return {"status": "error", "result": "usage: set <ip>"}

        ip = parts[1]

        current_target["ip"] = ip

        return {"status": "ok", "result": f"target set to {ip}"}
    
    elif command == "curl":

        if len(parts) > 1:

            return {"status": "error", "result": "usage: curl"}

        ip = current_target["ip"]

        if not ip:

            return {"status": "error", "result": "no target set. use: set <ip>"}

        try:

            curl_result = subprocess.run(

                 ["curl", ip], capture_output=True, text=True, timeout=15

            )

            return {"status": "ok", "result": curl_result.stdout or curl_result.stderr}

        except subprocess.TimeoutExpired:

            return {"status": "error", "result": "curl timed out"}

        except FileNotFoundError:

            return {"status": "error", "result": "curl not found on this system"}

        except Exception as e:

            return {"status": "error", "result": f"curl failed: {e}"}


    
    elif command == "ports":

        NMAP_PATH = r"C:\Program Files (x86)\Nmap\nmap.exe"

        if len(parts) > 1:

            return {"status": "error", "result": "usage: ports"}

        ip = current_target["ip"]

        if not ip:

            return {"status": "error", "result": "no target set. use: set <ip>"}

        try:

            port_result = subprocess.run(

                 [NMAP_PATH, "-T4", "-F", "-sV", ip], capture_output=True, text=True, timeout=120

            )

            return {"status": "ok", "result": port_result.stdout or port_result.stderr}

        except subprocess.TimeoutExpired:

            return {"status": "error", "result": "ports scan timed out after 120s"}

        except FileNotFoundError:

            return {"status": "error", "result": f"nmap not found at {NMAP_PATH}"}

        except Exception as e:

            return {"status": "error", "result": f"ports scan failed: {e}"}

    
    elif command == "os":

        ip = parts[1] if len(parts) >= 2 else current_target["ip"]

        if not ip:

            return {"status": "error", "result": "no target set. use: set <ip>"}

        NMAP_PATH = r"C:\Program Files (x86)\Nmap\nmap.exe"
        
        try:

            scan_result = subprocess.run(

                 [NMAP_PATH, "-O", ip], capture_output=True, text=True, timeout=120

            )

            return {"status": "ok", "result": scan_result.stdout or scan_result.stderr}

        except subprocess.TimeoutExpired:

            return {"status": "error", "result": "os scan timed out after 120s"}

        except FileNotFoundError:

            return {"status": "error", "result": f"nmap not found at {NMAP_PATH}"}

        except Exception as e:

            return {"status": "error", "result": f"os scan failed: {e}"}

    else:

        return {"status": "error", "result": f"unknown command: {command}"}

@app.route("/scan", methods=["POST"])

def scan():

    try:

        data = request.get_json()

        target_ip = data.get("target_ip")

        result = handle_options(target_ip)

        return jsonify(result)

    except Exception as e:

        return jsonify({"status": "error", "result": f"server error: {e}"}), 200

if __name__ == "__main__":
    # don't auto-open a browser tab on every reloader restart, only the real run
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:5001")).start()
    app.run(debug=True, port=5001)


