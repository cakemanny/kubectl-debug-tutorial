from http import HTTPStatus
import http.server
import os
import socketserver

import bcrypt

evil_global_leak_bucket = []


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    pass


class MyHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == '/leak':
            for _ in range(1000):
                evil_global_leak_bucket.append(b'x' * 1000)
            self.respond_simple(
                HTTPStatus.OK, f'I think my bucket has a hole in it...\n',
            )
        # do work
        pw = bcrypt.hashpw("has hash ash".encode(), bcrypt.gensalt()).decode()
        self.respond_simple(
            HTTPStatus.OK,
            f'is this what you are looking for?: {pw}\n',
        )

    def respond_simple(
        self, status, message, content_type='text/plain; charset=utf-8',
        charset='utf-8'
    ):
        response_bytes = message.encode(charset)
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

def main():
    host, port = '0.0.0.0', int(os.getenv('PORT', 8000))
    httpd = ThreadedHTTPServer((host, port), MyHandler)
    print(f'listening at http://{host}:{port}/')
    httpd.serve_forever()
