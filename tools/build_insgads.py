# Build the Insurance Google Ads proposal decks (one editable component per location) from the PowerPoint.
# usage: python3 build_insgads.py <unzipped pptx dir> <project dir>
import sys, os, re, json, hashlib, shutil, html as H
sys.path.insert(0, os.path.dirname(__file__))
from pptx2html import Conv
from locales import LOC, conv, sig, commas, short
ROOT, PROJ = sys.argv[1], sys.argv[2]
TITLES = ['Cover', 'Director', 'About Sarac Ramsay', 'Clients', 'Results', 'How expats find a broker', 'The strategy', 'The channels', 'The opportunity',
  'The problem', 'The plan: 3 components', 'From where you are', 'Component 1: The intent', 'The keywords', 'Campaign structure', 'Why we build it this way',
  'Component 2: Stand out', 'Same budget, better ad', 'What an expat sees', 'Component 3: The system', 'The target: 30', 'The 30 system', 'Smart bidding',
  'Month 3: Hold the fort', 'The math', 'Google Ads plans', 'Our guarantee', 'Case study', 'Before', 'The result']
N = len(TITLES)
# local flavour for the market-specific words (all plain text, editable in the deck)
REG = {
 'UK':        dict(region='uk',       regl='UK',         area='UK + Europe', c1=('Thames Cover Brokers', 'thamescover.co.uk'), c2=('Albion Assure', 'albionassure.co.uk')),
 'Dubai':     dict(region='uae',      regl='UAE',        area='GCC',         c1=('Gulf Cover Brokers', 'gulfcoverbrokers.ae'), c2=('Emirates Cover', 'emiratesassure.ae')),
 'Marbella':  dict(region='spain',    regl='Spain',      area='Europe',      c1=('Costa Cover Brokers', 'costacover.es'), c2=('Iberia Assure', 'iberiaassure.es')),
 'Hong Kong': dict(region='hong kong', regl='Hong Kong', area='Asia',        c1=('Harbour Cover Brokers', 'harbourcover.hk'), c2=('Pearl Assure', 'pearlassure.hk')),
 'Thailand':  dict(region='thailand', regl='Thailand',   area='Asia',        c1=('Andaman Cover Brokers', 'andamancover.co.th'), c2=('Siam Assure', 'siamassure.co.th')),
}
def fixer(loc):
    L = LOC[loc]; cur = L['cur']; S = L['sym']; R = REG[loc]
    cpc = round(conv(12.85, 'AED', cur), 2); budget = round(1200 * cpc); total = 3 * budget
    if loc == 'Dubai': cpc = 12.85; budget = 15420; total = 46260
    def money(v, frm, suffix):
        x = conv(v, frm, cur)
        if suffix in ('k', 'K'): return S + short(x)
        if suffix == 'M': return S + short(sig(x, 2))
        return S + commas(sig(x, 3 if v >= 10000 else 2))
    def eur(mm):
        raw = mm.group(1); suf = mm.group(2) or ''
        v = float(raw.replace(',', '')) * {'k': 1e3, 'K': 1e3, 'M': 1e6}.get(suf, 1)
        return money(v, 'EUR', suf)
    def aed(mm):
        raw = mm.group(2); v = float(raw.replace(',', ''))
        out = {'12.85': '{:,.2f}'.format(cpc), '15,425': commas(budget), '46,275': commas(total)}.get(raw)
        if out is not None: return S + out
        return money(v, 'AED', '')
    def fix(t):
        t = t.replace('&quot;', '"')
        t = re.sub(r'€\s?(\d[\d,]*(?:\.\d+)?)([kM])?', eur, t) if '€' in t else t
        if t.strip() == 'AED' : return t.replace('AED', S.strip() or S, 1) if loc != 'Dubai' else t
        t = re.sub(r'(AED\s?)(\d[\d,.]*)', aed, t)
        if t.strip() in ('12.85', '15,425', '46,275'):
            t = t.replace(t.strip(), {'12.85': '{:,.2f}'.format(cpc), '15,425': commas(budget), '46,275': commas(total)}[t.strip()])
        t = t.replace('[location]', L['low']).replace('[Location]', L['city']).replace('[LOCATION]', L['city'].upper())
        if loc != 'Dubai':
            t = t.replace('Gulf Cover Brokers', R['c1'][0]).replace('gulfcoverbrokers.ae', R['c1'][1]).replace('Emirates Cover', R['c2'][0]).replace('emiratesassure.ae', R['c2'][1])
            t = t.replace('Dubai', L['city']).replace('dubai', L['low']).replace('DUBAI', L['city'].upper())
            t = t.replace('GCC ·', R['area'] + ' ·').replace('UAE ·', R['regl'] + ' ·')
            t = re.sub(r'\buae\b', R['region'], t); t = re.sub(r'\bUAE\b', R['regl'], t)
        return t
    return fix, dict(cpc=cpc, budget=budget, total=total)
def note_fix(t, loc, fix):
    t = t.replace('So Martin, ', 'So [NAME], ')
    t = re.sub(r'€[\d,]+[kM]?', lambda m: fix(m.group(0)), t)
    if loc != 'Dubai': t = t.replace('Dubai', LOC[loc]['city'])
    return t
def raw_notes(root):
    out = []
    for n in range(1, N + 1):
        rels = open(os.path.join(root, 'ppt/slides/_rels/slide%d.xml.rels' % n)).read()
        m = re.search(r'notesSlide(\d+)\.xml', rels)
        t = open(os.path.join(root, 'ppt/notesSlides/notesSlide%s.xml' % m.group(1)), encoding='utf-8').read()
        ps = [''.join(re.findall(r'<a:t>([^<]*)', p)) for p in re.findall(r'<a:p>.*?</a:p>', t, re.S)]
        out.append(' '.join(H.unescape(p).strip() for p in ps if p.strip() and not p.strip().isdigit()))
    return out
# media -> project/insgads-assets
adir = os.path.join(PROJ, 'insgads-assets'); os.makedirs(adir, exist_ok=True)
mm = {}
for f in sorted(os.listdir(os.path.join(ROOT, 'ppt/media'))):
    b = open(os.path.join(ROOT, 'ppt/media', f), 'rb').read()
    nm = hashlib.md5(b).hexdigest()[:12] + os.path.splitext(f)[1].lower()
    mm[f] = nm; open(os.path.join(adir, nm), 'wb').write(b)
NOTES = raw_notes(ROOT)
def merged(left, top, w, h, sz, spc, lh, lines, ff="'Newsreader', Georgia, serif", center=False):
    # one text box for a headline the PowerPoint export cut into overlapping pieces: lines of (text, italic, colour) runs
    E = lambda v: '%.3f%%' % (v)
    px = sz * 4 / 3; cq = lambda p: ('%.3f' % (p / 19.2)).rstrip('0').rstrip('.') + 'cqw'
    ps = []
    for ln in lines:
        rs = ''.join('<span style="color: %s%s">%s</span>' % (c, '; font-style: italic' if i else '', H.escape(t, quote=False)) for t, i, c in ln)
        ps.append('<p style="margin: 0; text-align: %s; line-height: %s; font-size: %s; letter-spacing: %s; white-space: nowrap">%s</p>' % ('center' if center else 'left', lh, cq(px), cq(spc / 100 * 4 / 3), rs))
    return ('<div style="position: absolute; left: %s; top: %s; width: %s; height: %s; box-sizing: border-box; padding: 0.139cqw; font-family: %s; font-weight: 400">%s</div>'
            % (E(left / 18288000 * 100), E(top / 10287000 * 100), E(w / 18288000 * 100), E(h / 10287000 * 100), ff, ''.join(ps)))
W_, G_, GOLD = '#FFFFFF', '#C6A667', '#C6A667'
conv_ = Conv(ROOT, {k: 'insgads-assets/' + v for k, v in mm.items()}); conv_.gads_icon = False
conv_.skip = [(1, 'The best sales'), (1, 'expat service'), (1, 'around the world'), (3, "One of the world"), (3, 'expat service'), (3, 'growth consultants'),
              (26, 'one-time'), (26, '/mo'), (10, 'Why most'), (10, 'to attract'), (28, 'How we helped'), (28, '€180,000 '), (28, 'in commissions in 35')]
conv_.extra = {
  1: [merged(1358801, 3690491, 14500000, 3000000, 66, -99, 1.2 * 0.96765, [[('The best sales and marketing advisors', 0, '#FFFFFF')], [('for ', 0, '#FFFFFF'), ('expat service companies', 1, GOLD), (' around the', 0, '#FFFFFF')], [('world.', 0, '#FFFFFF')]])],
  3: [merged(1263551, 2557611, 8000000, 1500000, 46.5, 0, 1.2 * 0.96765, [[("One of the world's leading", 0, '#142C49')], [('expat service', 1, GOLD), (' growth consultants.', 0, '#142C49')]])],
}
FONT = '<link rel="preconnect" href="https://fonts.googleapis.com">\n<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;0,6..72,700;1,6..72,400;1,6..72,500;1,6..72,600;1,6..72,700&amp;display=swap" rel="stylesheet">'
TEMPLATE = open(os.path.join(os.path.dirname(__file__), 'insgads_template.html'), encoding='utf-8').read()
for loc in LOC:
    name = 'InsGAds' + loc.replace(' ', '')
    fix, info = fixer(loc)
    secs = []
    conv_.extra[10] = [merged(0, 1041053, 18288000, 1000000, 49.5, -74, 1.2 * 0.92374, [[('Why most Google Ads strategies fail ', 0, '#FFFFFF'), ('to attract qualified expats.', 1, GOLD)]], center=True)]
    conv_.extra[28] = [merged(1358801, 3284934, 15000000, 3000000, 63, -126, 1.2 * 0.96765, [[('How we helped an Expat Insurance Broker earn', 0, '#FFFFFF')], [(fix('€180,000'), 0, GOLD), (' in commissions in 35 days', 0, '#FFFFFF')]])]
    units = []
    for numtxt, left, unit, ut in (('€5,000', 1192560, 'one-time', 'one-time'), ('€2,000', 6812310, '/mo', '/mo'), ('€1,000', 12432060, '/mo', '/mo')):
        amt = fix(numtxt); ul = left + int(len(amt) * 0.205 * 1e6) + 40000
        units.append('<div style="position: absolute; left: %.3f%%; top: %.3f%%; width: %.3f%%; height: %.3f%%; box-sizing: border-box; padding: 0.139cqw; font-family: \'Helvetica Neue\', Helvetica, Arial, sans-serif"><p style="margin: 0; font-size: 0.833cqw; line-height: 1.2; white-space: nowrap; color: #9A9387">%s</p></div>' % (ul / 18288000 * 100, 3055739 / 10287000 * 100, 900000 / 18288000 * 100, 219819 / 10287000 * 100, ut))
    conv_.extra[26] = units
    for n in range(1, N + 1):
        bg, inner = conv_.slide(n, fix)
        note = H.escape(note_fix(NOTES[n - 1], loc, fix), quote=False)
        secs.append('<!-- SLIDE %d · %s -->\n<div style="display: {{v.s%d}}; min-width: 0">\n<section aria-label="Slide %d: %s" style="display: {{sd}}; position: relative; width: 100%%; aspect-ratio: 16 / 9; overflow: hidden; container-type: inline-size; %s">\n%s\n</section>\n<div class="sr-notes" style="display: {{nd}}; margin-top: {{nmt}}; padding: {{npad}}; border-radius: 8px; background-color: {{nbg}}; font-family: \'Inter\', system-ui, -apple-system, \'Segoe UI\', sans-serif"><div style="font-size: 10px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #9B9B97">Speaker notes · slide %d</div><p style="margin: 6px 0 0; font-size: {{nfs}}; line-height: 1.55; color: #E6E6E4">%s</p></div>\n</div>' % (n, TITLES[n-1], n, n, TITLES[n-1], bg, inner, n, note))
    doc = TEMPLATE.replace('@@LOC@@', loc).replace('@@LOCU@@', loc.upper()).replace('@@CUR@@', LOC[loc]['cur']).replace('@@FONT@@', FONT).replace('@@MAX@@', str(N - 1)).replace('@@N@@', str(N)).replace('@@SLIDES@@', '\n'.join(secs))
    open(os.path.join(PROJ, name + '.dc.html'), 'w', encoding='utf-8').write(doc)
    print(name, len(doc) // 1024, 'KB', info)
json.dump(TITLES, open(os.path.join(os.path.dirname(__file__), 'insgads_titles.json'), 'w'))
