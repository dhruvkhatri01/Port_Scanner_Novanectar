from flask import Flask, render_template, request, jsonify, send_file
from scanner import scan_ports
import json, os
from datetime import datetime

app = Flask(__name__)
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

def parse_ports(port_text):
    """
    Accepts forms like:
    22,80,443
    1-1024
    22,80,8000-8010
    """
    ports = set()
    parts = [p.strip() for p in port_text.split(",") if p.strip()]
    for part in parts:
        if "-" in part:
            a,b = part.split("-",1)
            ports.update(range(int(a), int(b)+1))
        else:
            ports.add(int(part))
    return sorted(ports)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/scan", methods=["POST"])
def do_scan():
    data = request.json
    host = data.get("host")
    ports_spec = data.get("ports", "1-1024")
    threads = int(data.get("threads", 100))
    use_nmap = bool(data.get("use_nmap", True))
    ports = parse_ports(ports_spec)
    results = scan_ports(host, ports, threads=threads, use_nmap=use_nmap)
    # save report
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    filename = f"scan_{host}_{timestamp}.json"
    path = os.path.join(REPORTS_DIR, filename)
    with open(path, "w") as f:
        json.dump({"host": host, "ports_spec": ports_spec, "threads": threads, "results": results, "timestamp": timestamp}, f, indent=2)
    return jsonify({"status":"ok","report":filename,"results":results})

@app.route("/reports/<name>")
def get_report(name):
    path = os.path.join(REPORTS_DIR, name)
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return "Not found", 404

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)