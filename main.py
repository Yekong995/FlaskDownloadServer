from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory,
    flash,
)
from werkzeug.security import safe_join
from secure import *
from rich.console import Console
from rich.traceback import install as trace_install
from rich.pretty import install as pretty_install
from signal import signal, SIGINT
import sys
import os

console = Console()
trace_install(console=console)
pretty_install(console=console)

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.urandom(24)
csp = ContentSecurityPolicy()
hsts = StrictTransportSecurity()
xfo = XFrameOptions().deny()
xss = XXSSProtection().set("1; mode=block")
secure_headers = Secure(csp=csp, hsts=hsts, xfo=xfo, xxp=xss)
secure_headers = Secure.Framework(secure_headers)


def handler(_signal_received, _frame):
    console.log("SIGINT or CTRL-C detected. Exiting gracefully")
    sys.exit(0)


signal(SIGINT, handler)

console.log("Collecting files")

if not os.path.exists("file"):
    os.makedirs("file")

files = []

for file in os.listdir("file"):
    if os.path.isfile(os.path.join("file", file)):
        files.append(file)

console.log(f"Found {len(files)} files. All were collected successfully")


@app.after_request
def apply_caching(response):
    secure_headers.flask(response)
    return response


@app.route("/")
def index():
    if len(files) == 0:
        flash("No files found", "error")

    return render_template("index.html", files=files)


@app.route("/download/<filename>")
def download(filename):
    if filename not in files:
        flash(f"File {filename} does not exist", "error")
        return redirect(url_for("index"))

    user_ip = request.remote_addr
    console.log(f"File {filename} requested by {user_ip}")

    file_path = safe_join(app.root_path, "file")
    
    if file_path is None:
        flash("File not found", "error")
        console.log(f"File {filename} not found")
        return redirect(url_for("index"))

    return send_from_directory(directory=file_path, path=filename, as_attachment=True)

@app.route("/refresh")
def refresh():
    console.log("Reloading files")
    files.clear()

    for file in os.listdir("file"):
        if os.path.isfile(os.path.join("file", file)):
            files.append(file)

    console.log(f"Found {len(files)} files. All were collected successfully")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True, processes=True)
