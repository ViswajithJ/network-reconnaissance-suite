from flask import Flask, render_template, request, redirect, url_for, session
from port_scanner import *
from scan_scripts.scripts import *
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")


@app.route("/", methods=["GET"])
def index():
    if request.method == "GET":
        return render_template("index.html")


@app.route("/ip", methods=["GET", "POST"])
def ip():
    if request.method == "GET":
        return render_template("ipinput.html")
    elif request.method == "POST":
        if request.form.get("scan") == "Scan":
            global ip
            ip = request.form.get("ip")
            print(ip)
            if check_host(ip):
                return redirect(url_for("port"))
            else:
                return redirect(url_for("error"))


@app.route("/port", methods=["GET", "POST"])
def port():
    if request.method == "GET":
        return render_template("port.html")
    elif request.method == "POST":
        start_port = int(request.form.get("start_port"))
        end_port = int(request.form.get("end_port"))
        print(start_port, end_port)
        if (start_port <= 0) or (end_port > 65536):
            return redirect(url_for("error"))
        else:
            open_ports, closed_ports, filtered_ports = port_scan(
                ip, start_port, end_port
            )
            open_ports_json = json.dumps(open_ports)
            closed_ports_json = json.dumps(closed_ports)
            filtered_ports_json = json.dumps(filtered_ports)

            port_scan_results = [
                open_ports_json,
                closed_ports_json,
                filtered_ports_json,
            ]
            session["port_scan_results"] = port_scan_results
            return redirect(
                url_for(
                    "output"
                    # open_ports=open_ports_json,
                    # closed_ports=closed_ports_json,
                    # filtered_ports=filtered_ports_json,
                )
            )


@app.route("/output", methods=["GET", "POST"])
def output():
    if request.method == "GET":
        # open_ports = json.loads(request.args.get("open_ports"))
        # closed_ports = json.loads(request.args.get("closed_ports"))
        # filtered_ports = json.loads(request.args.get("filtered_ports"))
        port_scan_results = session.pop("port_scan_results", None)
        print(type(port_scan_results))
        open_ports = json.loads(port_scan_results[0])
        closed_ports = json.loads(port_scan_results[1])
        filtered_ports = json.loads(port_scan_results[2])
        return render_template(
            "output.html",
            open_ports=open_ports,
            closed_ports=closed_ports,
            filtered_ports=filtered_ports,
        )
    elif request.method == "POST":
        if request.form.get("submit") == "Yes":
            return redirect(url_for("script"))


@app.route("/script", methods=["GET", "POST"])
def script():
    if request.method == "GET":
        return render_template("script.html")
    elif request.method == "POST":
        if request.form.get("submit") == "Check":
            script_list = request.form.getlist("script")
            print(script_list)
            output = []
            for script in script_list:
                headers = detect_version(ip, 80)
                if script == "clickjacking":
                    output.append(check_clickjacking_vulnerability(headers))
                elif script == "insecuremc":
                    output.append(check_insecure_mixed_content(headers))
                elif script == "hsts":
                    output.append(check_hsts_vulnerability(headers))
                elif script == "reflectedxss":
                    output.append(check_reflected_xss_vulnerability(headers))
                elif script == "cachecontrol":
                    output.append(check_cache_control_vulnerability(headers))
                elif script == "serverinfo":
                    output.append(check_server_info_vulnerability(headers))
                elif script == "cachepoisoning":
                    output.append(check_cache_poisoning_vulnerability(headers))
                elif script == "corsvul":
                    output.append(check_cors_vulnerability(headers))
            return json.dumps(output)


# @app.route("/script", methods=["GET", "POST"])
# def script():
#     if request.method == "GET":
#         return render_template("script.html")
#     elif request.method == "POST":
#         if request.form.get("submit") == "Check":
#             script_list = request.form.getlist("script")
#             for script in script:
#                 if script == "ssl_check":
#                     return redirect(url_for("domaininput"))


# @app.route("/domain", methods=["GET", "POST"])
# def domain():
#     if request.method == "GET":
#         return render_template("domaininput.html")
#     elif request.method == "POST":
#         if request.form.get("Scan") == "scan":
#             domain = request.form.get("ip")
#             result = check_ssl_certificate(domain, 443)
# 			return render_template("output")


@app.route("/error", methods=["GET"])
def error():
    if request.method == "GET":
        return render_template("error.html")


if __name__ == "__main__":
    app.run()
