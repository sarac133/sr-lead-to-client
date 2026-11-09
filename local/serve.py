#!/usr/bin/env python3
"""Serve the Lead to Client page locally.  Usage: python3 local/serve.py [port]"""
import http.server, os, re, sys, mimetypes, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROJECT = os.path.join(ROOT, 'project')
ASSETS = os.path.join(ROOT, 'assets')
JSPDF_BLOB = 'a81668c73027c69b9fa0c02d5ba59ba9'  # the PDF library; only lives in the artifact, so load it from a CDN
JSPDF_CDN = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js'

BLOBS = {}
for line in open(os.path.join(ASSETS, 'MANIFEST.md'), encoding='utf-8'):
    m = re.match(r'^\|\s*`([0-9a-f]{32})`\s*\|\s*(.+?)\s*\|\s*$', line)
    if m and 'not in repo' not in m.group(2):
        BLOBS[m.group(1)] = os.path.join(ASSETS, m.group(2))

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def send_file(self, path):
        if not os.path.isfile(path):
            self.send_response(404); self.end_headers(); return
        data = open(path, 'rb').read()
        ctype = mimetypes.guess_type(path)[0] or 'application/octet-stream'
        if path.endswith('.js'): ctype = 'text/javascript'
        self.send_response(200)
        self.send_header('Content-Type', ctype + ('; charset=utf-8' if ctype.startswith('text/') else ''))
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        if self.command != 'HEAD': self.wfile.write(data)
    def do_HEAD(self): self.do_GET()
    def do_GET(self):
        p = urllib.parse.unquote(urllib.parse.urlparse(self.path).path)
        if p == '/': p = '/Main.dc.html'
        if p == '/support.js': return self.send_file(os.path.join(HERE, 'support.js'))
        m = re.match(r'^/_blob/([0-9a-f]{32})$', p)
        if m:
            bid = m.group(1)
            if bid == JSPDF_BLOB:
                self.send_response(302); self.send_header('Location', JSPDF_CDN); self.end_headers(); return
            return self.send_file(BLOBS[bid]) if bid in BLOBS else self.send_file('')
        full = os.path.normpath(os.path.join(PROJECT, p.lstrip('/')))
        if not full.startswith(PROJECT + os.sep): self.send_response(403); self.end_headers(); return
        self.send_file(full)

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', port), Handler)
    print('Lead to Client running at http://localhost:%d  (Ctrl+C to stop)' % port)
    try: srv.serve_forever()
    except KeyboardInterrupt: pass
