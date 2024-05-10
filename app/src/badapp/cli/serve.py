from http import HTTPStatus
import http.server
import os
import socketserver

import bcrypt


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    pass


class MyHandler(http.server.BaseHTTPRequestHandler):

    def _hash_password(self, password):
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def do_GET(self):
        # do work
        pw = self._hash_password("has hash ash")
        self.respond_simple(
            HTTPStatus.OK,
            f'is this what you are looking for?: {pw}',
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
