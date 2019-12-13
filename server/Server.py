#!/usr/bin/env python

# Simple HTTP Server that accepts only GET requests and prints request parameters
# Use this to test curly if you are contributing :)

import http.server
import socketserver
import logging

PORT = 8000


class GetHandler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):
        logging.error(self.headers)
        http.server.SimpleHTTPRequestHandler.do_GET(self)


Handler = GetHandler
httpd = socketserver.TCPServer(("", PORT), Handler)

httpd.serve_forever()
