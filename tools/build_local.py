import sys, json, os
sys.path.insert(0, os.path.dirname(__file__))
from pptx2html import Conv
from locales import fixer, LOC
S = sys.argv[1]; loc = sys.argv[2]; out = sys.argv[3]
mm = json.load(open(S + '/gads/build/media_map.json'))
conv = Conv(S + '/gads/x', {k: 'assets/' + v for k, v in mm.items()})
fix, info = fixer(loc)
fonts = S + '/gads/fonts/nr/package/files/'
ff = ''.join("@font-face{font-family:'Newsreader';font-style:%s;font-weight:%s;src:url('file://%snewsreader-latin-%s-%s.woff2') format('woff2')}" % (st, w, fonts, w, st) for w in (400,500,600,700) for st in ('normal','italic'))
slides = []
for n in range(1, 32):
    bg, inner = conv.slide(n, fix)
    slides.append('<section class="sl" style="position: relative; width: 1920px; height: 1080px; overflow: hidden; container-type: inline-size; %s">%s</section>' % (bg, inner))
html = '<!doctype html><html><head><meta charset="utf-8"><style>%s body{margin:0;background:#111} .sl{margin:0 0 20px}</style></head><body>%s</body></html>' % (ff, '\n'.join(slides))
open(out, 'w', encoding='utf-8').write(html)
print(loc, len(html)//1024, 'KB', info)
