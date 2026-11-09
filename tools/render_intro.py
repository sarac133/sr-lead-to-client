import sys, os, glob, re, shutil
sys.path.insert(0, os.path.dirname(__file__))
from pptx2html import Conv
root, out = sys.argv[1], sys.argv[2]
media = {os.path.basename(f): 'file://' + os.path.abspath(f) for f in glob.glob(root + '/ppt/media/*')}
# strip root-svg offsets / hidden defs the export leaves in (same fix as the Google Ads deck)
fixdir = out + '_media'; os.makedirs(fixdir, exist_ok=True)
for name, url in list(media.items()):
    if name.endswith('.svg'):
        t = open(url[7:], encoding='utf-8').read()
        m = re.match(r'(<svg[^>]*?style=")([^"]*)(")', t)
        if m:
            st = re.sub(r'(^|;\s*)(position|left|top|right|bottom|margin[a-z-]*|transform)\s*:[^;]*', '', m.group(2)).lstrip('; ')
            t = t[:m.start(2)] + st + t[m.end(2):]
        t = t.replace('visibility: hidden', 'visibility: visible')
        p = os.path.join(fixdir, name); open(p, 'w', encoding='utf-8').write(t); media[name] = 'file://' + os.path.abspath(p)
conv = Conv(root, media); conv.gads_icon = False
n = len(glob.glob(root + '/ppt/slides/slide*.xml'))
ident = lambda s: s
secs = []
for i in range(1, n + 1):
    bg, inner = conv.slide(i, ident)
    secs.append('<section class="sl" style="position: relative; width: 1920px; height: 1080px; overflow: hidden; container-type: inline-size; %s">%s</section>' % (bg, inner))
html = '<!doctype html><html><head><meta charset="utf-8"><style>body{margin:0;background:#111} .sl{margin:0 0 20px}</style></head><body>%s</body></html>' % '\n'.join(secs)
open(out + '.html', 'w', encoding='utf-8').write(html); print(n)
