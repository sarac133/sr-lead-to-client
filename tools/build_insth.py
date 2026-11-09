import re, json, hashlib, base64, os
S = '/tmp/claude-0/-home-claude/6f002592-31e4-5592-996b-e15f5b0fe953/scratchpad'
F = json.load(open(S + '/ins-th2/F.json'))
proj = S + '/sr-lead-to-client/project'
adir = proj + '/insth-assets'; os.makedirs(adir, exist_ok=True)
NAMES = {'Main': 'InsTH-01-Intro', '02-Director': 'InsTH-02-Director', '03-About': 'InsTH-03-About', '04-Clients': 'InsTH-04-Clients',
         '05-Results': 'InsTH-05-Results', '06-Case-File': 'InsTH-06-Case-File', '07-Challenge': 'InsTH-07-Challenge',
         '08-Result': 'InsTH-08-Result', '10-Questions': 'InsTH-10-Questions'}
EXT = {'image/webp': 'webp', 'image/png': 'png', 'image/jpeg': 'jpg', 'image/svg+xml': 'svg', 'image/gif': 'gif'}
assets = []
def unpack(m):
    mime, b64 = m.group(1), m.group(2)
    data = base64.b64decode(b64)
    name = hashlib.sha1(data).hexdigest()[:12] + '.' + EXT[mime]
    p = os.path.join(adir, name)
    if not os.path.exists(p): open(p, 'wb').write(data)
    if name not in assets: assets.append(name)
    return 'insth-assets/' + name
out = {}
for old, new in NAMES.items():
    t = F[old]
    t = re.sub(r'data:(image/[a-z+]+);base64,([A-Za-z0-9+/=]+)', unpack, t)
    assert 'data:' not in t, old
    out[new] = t
# root deck
rm = open(S + '/ins-th2/root_markup.html').read(); rs = open(S + '/ins-th2/root_script.html').read()
for old, new in NAMES.items():
    rm = rm.replace('<dc-import name="%s"' % old, '<dc-import name="%s"' % new)
assert 'name="Main"' not in rm
root = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>SR Insurance Presentation · Thailand</title>
<script src="./support.js"></script>
</head>
<body>
<!-- SR INSURANCE PRESENTATION (intro call, Insurance · Thailand). The original interactive Claude Design deck: chapters, zooms, clickable slides.
     Each slide is its own artboard (InsTH-01 … InsTH-10): edit the words there. Lead to Client shows this deck in Step 04 of the intro call. -->
''' + rm + '\n' + rs + '\n</body>\n</html>\n'
out['InsTHDeck'] = root
for n, t in out.items():
    open(os.path.join(proj, n + '.dc.html'), 'w', encoding='utf-8').write(t)
print({n: len(t) for n, t in out.items()}); print(len(assets), 'assets', sum(os.path.getsize(os.path.join(adir, a)) for a in assets))
json.dump({'files': [n + '.dc.html' for n in out], 'assets': assets}, open(S + '/insth_files.json', 'w'))
