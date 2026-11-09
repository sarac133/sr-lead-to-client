import sys, json, os
sys.path.insert(0, os.path.dirname(__file__))
from pptx2html import Conv
from locales import fixer, LOC, sig, commas
from locales import conv as lconv
import re, html as H
def raw_notes(root):
    out = []
    for n in range(1, 32):
        rels = open(os.path.join(root, 'ppt/slides/_rels/slide%d.xml.rels' % n)).read()
        m = re.search(r'notesSlide(\d+)\.xml', rels)
        t = open(os.path.join(root, 'ppt/notesSlides/notesSlide%s.xml' % m.group(1)), encoding='utf-8').read()
        paras = [''.join(re.findall(r'<a:t>([^<]*)', p)) for p in re.findall(r'<a:p>.*?</a:p>', t, re.S)]
        out.append(' '.join(H.unescape(p).strip() for p in paras if p.strip() and not p.strip().isdigit()))
    return out
def note_fix(text, loc):
    L = LOC[loc]; S = L['sym']
    mon = lambda v: S + commas(sig(lconv(v, 'EUR', L['cur']), 3))
    text = text.replace('So Martin, ', 'So [NAME], ')
    for v in (310000, 180000, 10000):
        text = text.replace('€' + format(v, ','), mon(v))
    if loc != 'Dubai':
        text = text.replace('more than 20,000 searches a month in Dubai', '[~X] searches a month in ' + L['city'])
    return text
S = sys.argv[1]; outdir = sys.argv[2]
TITLES = ['Cover', 'Director', 'About Sarac Ramsay', 'Clients', 'Results', 'How investors find an agency', 'The strategy', 'The channels',
  'The opportunity', 'The problem', 'The plan: 3 components', 'From where you are', 'The route', 'Component 1: The intent', 'The keywords',
  'Campaign structure', 'Why we build it this way', 'Component 2: Stand out', 'Same budget, better ad', 'What an investor sees',
  'Component 3: The system', 'The target: 30', 'The 30 system', 'Smart bidding', 'Month 3: Hold the fort', 'The math', 'Google Ads plans',
  'Our guarantee', 'Case study', 'Before', 'The result']
mm = json.load(open(S + '/gads/build/media_map.json'))
NOTES = raw_notes(S + '/gads/x')
conv = Conv(S + '/gads/x', {k: 'gads-assets/' + v for k, v in mm.items()})
FONT = '<link rel="preconnect" href="https://fonts.googleapis.com">\n<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;0,6..72,700;1,6..72,400;1,6..72,500;1,6..72,600;1,6..72,700&amp;display=swap" rel="stylesheet">'
for loc in LOC:
    name = 'GAds' + loc.replace(' ', '')
    fix, info = fixer(loc)
    secs = []
    for n in range(1, 32):
        bg, inner = conv.slide(n, fix)
        note = H.escape(note_fix(NOTES[n-1], loc), quote=False)
        secs.append('<!-- SLIDE %d · %s -->\n<div style="display: {{v.s%d}}; min-width: 0">\n<section aria-label="Slide %d: %s" style="display: {{sd}}; position: relative; width: 100%%; aspect-ratio: 16 / 9; overflow: hidden; container-type: inline-size; %s">\n%s\n</section>\n<div class="sr-notes" style="display: {{nd}}; margin-top: {{nmt}}; padding: {{npad}}; border-radius: 8px; background-color: {{nbg}}; font-family: \'Inter\', system-ui, -apple-system, \'Segoe UI\', sans-serif"><div style="font-size: 10px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #9B9B97">Speaker notes · slide %d</div><p style="margin: 6px 0 0; font-size: {{nfs}}; line-height: 1.55; color: #E6E6E4">%s</p></div>\n</div>' % (n, TITLES[n-1], n, n, TITLES[n-1], bg, inner, n, note))
    doc = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Google Ads Proposal · %(loc)s</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
%(font)s
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&amp;display=swap" rel="stylesheet">
<style>
body{margin:0}
</style>
</helmet>
<!-- GOOGLE ADS PROPOSAL · REAL ESTATE · %(LOC)s (%(cur)s). Every text on the slides and in the speaker notes under them is plain text: double-click it on the canvas to change words or numbers. -->
<div style="width: 100%%; box-sizing: border-box; display: grid; grid-template-columns: {{cols}}; gap: {{gap}}; padding: {{pad}}; background-color: {{bg}}; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #142C49">
%(slides)s
</div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{"slide":{"editor":null},"mode":{"editor":null},"$preview":{"width":1960,"height":5600}}'>
class Component extends DCLogic {
  renderVals() {
    // mode "deck" (Lead to Client): one slide. mode "notes" (presenter view): that slide's speaker notes only.
    // No mode (this artboard on the canvas): every slide with its notes underneath, for editing.
    const mode = this.props.mode;
    const one = mode === 'deck' || mode === 'notes';
    const s = Math.max(0, Math.min(30, Number(this.props.slide) || 0));
    const v = {};
    for (let i = 1; i <= 31; i++) v['s' + i] = (!one || s === i - 1) ? 'block' : 'none';
    const notes = mode === 'notes';
    return {
      v,
      sd: notes ? 'none' : 'block',
      nd: mode === 'deck' ? 'none' : 'block',
      nmt: notes ? '0' : '10px',
      npad: notes ? '0' : '12px 14px',
      nbg: notes ? 'transparent' : '#202020',
      nfs: notes ? '17px' : '14px',
      cols: one ? 'minmax(0, 1fr)' : 'repeat(3, minmax(0, 1fr))',
      gap: one ? '0' : '24px',
      pad: one ? '0' : '24px',
      bg: one ? 'transparent' : '#191919'
    };
  }
}
</script>
</body>
</html>
''' % dict(loc=loc, LOC=loc.upper(), cur=LOC[loc]['cur'], font=FONT, slides='\n'.join(secs))
    open(os.path.join(outdir, name + '.dc.html'), 'w', encoding='utf-8').write(doc)
    print(name, len(doc)//1024, 'KB')
json.dump(TITLES, open(S + '/gads/build/titles.json', 'w'))
