# Convert the html-to-pptx style deck into absolutely positioned HTML slides (sizes in % and cqw so they scale).
import re, os, sys, json, math, hashlib, html
from xml.etree import ElementTree as ET
NS = {'a':'http://schemas.openxmlformats.org/drawingml/2006/main','p':'http://schemas.openxmlformats.org/presentationml/2006/main',
      'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships','asvg':'http://schemas.microsoft.com/office/drawing/2016/SVG/main'}
W, H = 18288000, 10287000
EMU_PX = 9525
def q(n): return ('%.3f' % n).rstrip('0').rstrip('.')
def cq(px): return q(px / 19.2) + 'cqw'          # px on a 1920 slide -> container width units
def emu_cq(e): return cq(e / EMU_PX)
FONTS = {'Helvetica Neue': "'Helvetica Neue', Helvetica, Arial, sans-serif", 'Newsreader': "'Newsreader', Georgia, serif",
         'Courier New': "'Courier New', Courier, monospace", 'Menlo': "Menlo, Consolas, 'Courier New', monospace", 'Arial': "Arial, Helvetica, sans-serif"}
def color(el):
    """srgbClr child of a fill element -> css colour (with alpha)."""
    if el is None: return None
    c = el.find('a:srgbClr', NS)
    if c is None: return None
    v = c.get('val'); a = c.find('a:alpha', NS)
    if a is None: return '#' + v
    al = int(a.get('val')) / 100000
    return 'rgba(%d,%d,%d,%s)' % (int(v[0:2],16), int(v[2:4],16), int(v[4:6],16), q(al))
def stop_color(gs):
    c = gs.find('a:srgbClr', NS); v = c.get('val'); a = c.find('a:alpha', NS)
    al = int(a.get('val'))/100000 if a is not None else 1
    return 'rgba(%d,%d,%d,%s)' % (int(v[0:2],16), int(v[2:4],16), int(v[4:6],16), q(al))
def grad_css(g):
    stops = ['%s %s%%' % (stop_color(gs), q(int(gs.get('pos'))/1000)) for gs in g.findall('a:gsLst/a:gs', NS)]
    lin = g.find('a:lin', NS)
    if lin is not None:
        ang = int(lin.get('ang', 0)) / 60000
        return 'linear-gradient(%sdeg, %s)' % (q(ang + 90), ', '.join(stops))
    return 'radial-gradient(circle at center, %s)' % ', '.join(stops)

class Conv:
    def __init__(self, root, media_map):
        self.root = root; self.media = media_map   # media_map: target filename -> token
    def rels(self, n):
        x = ET.parse(os.path.join(self.root, 'ppt/slides/_rels/slide%d.xml.rels' % n)).getroot()
        return {r.get('Id'): os.path.basename(r.get('Target')) for r in x}
    def blip_src(self, blip, rels):
        svg = blip.find('.//asvg:svgBlip', NS)
        rid = svg.get('{%s}embed' % NS['r']) if svg is not None else blip.get('{%s}embed' % NS['r'])
        return self.media[rels[rid]]
    def box_style(self, spPr, extra_shadow=True):
        xf = spPr.find('a:xfrm', NS); off = xf.find('a:off', NS); ext = xf.find('a:ext', NS)
        x, y, w, h = int(off.get('x')), int(off.get('y')), int(ext.get('cx')), int(ext.get('cy'))
        st = ['position: absolute', 'left: %s%%' % q(x/W*100), 'top: %s%%' % q(y/H*100), 'width: %s%%' % q(w/W*100), 'height: %s%%' % q(h/H*100), 'box-sizing: border-box']
        rot = xf.get('rot')
        if rot: st.append('transform: rotate(%sdeg)' % q(int(rot)/60000))
        g = spPr.find('a:prstGeom', NS)
        if g is not None:
            p = g.get('prst')
            if p == 'ellipse': st.append('border-radius: 50%')
            elif p == 'roundRect':
                gd = g.find('a:avLst/a:gd', NS); adj = int(gd.get('fmla').split()[-1]) if gd is not None else 16667
                st.append('border-radius: %s' % emu_cq(min(w, h) * adj / 100000))
        elif spPr.find('a:custGeom', NS) is not None:
            st.append('border-radius: %s' % emu_cq(114300))
        return st, (w, h)
    def fill_css(self, spPr, rels):
        out = []
        sf = spPr.find('a:solidFill', NS); gf = spPr.find('a:gradFill', NS); bf = spPr.find('a:blipFill', NS)
        if sf is not None: out.append('background-color: %s' % color(sf))
        elif gf is not None: out.append('background-image: %s' % grad_css(gf))
        ln = spPr.find('a:ln', NS)
        if ln is not None and ln.find('a:solidFill', NS) is not None:
            wpx = int(ln.get('w', 12700)) / EMU_PX
            dash = ln.find('a:prstDash', NS); style = 'dashed' if dash is not None and dash.get('val') not in ('solid',) else 'solid'
            out.append('border: %s %s %s' % (cq(max(wpx, 1)), style, color(ln.find('a:solidFill', NS))))
        sh = spPr.find('a:effectLst/a:outerShdw', NS)
        if sh is not None:
            blur = int(sh.get('blurRad', 0))/EMU_PX; dist = int(sh.get('dist', 0))/EMU_PX; d = math.radians(int(sh.get('dir', 0))/60000)
            out.append('box-shadow: %s %s %s %s' % (cq(dist*math.cos(d)), cq(dist*math.sin(d)), cq(blur), color(sh)))
        return out
    def blip_img(self, bf, rels):
        src = self.blip_src(bf.find('a:blip', NS), rels)
        sr = bf.find('a:srcRect', NS)
        st = 'position: absolute; display: block; max-width: none'
        if sr is not None:
            l, t, r, b = [int(sr.get(k, 0))/100000 for k in ('l', 't', 'r', 'b')]
            w = 100/(1-l-r); h = 100/(1-t-b)
            st += '; left: %s%%; top: %s%%; width: %s%%; height: %s%%' % (q(-l*w), q(-t*h), q(w), q(h))
        else: st += '; left: 0; top: 0; width: 100%; height: 100%'
        return '<img src="%s" alt="" style="%s">' % (src, st)
    def blip_css(self, bf, rels):
        src = self.blip_src(bf.find('a:blip', NS), rels)
        out = ["background-image: url('%s')" % src, 'background-repeat: no-repeat']
        sr = bf.find('a:srcRect', NS)
        if sr is not None:
            l, t, r, b = [int(sr.get(k, 0))/100000 for k in ('l', 't', 'r', 'b')]
            out.append('background-size: %s%% %s%%' % (q(100/(1-l-r)), q(100/(1-t-b))))
            out.append('background-position: %s%% %s%%' % (q(l/(l+r)*100 if l+r else 0), q(t/(t+b)*100 if t+b else 0)))
        else: out.append('background-size: 100% 100%')
        return out
    def text_html(self, txBody, fix):
        bp = txBody.find('a:bodyPr', NS)
        ins = [int(bp.get(k, d)) for k, d in (('tIns', 45720), ('rIns', 91440), ('bIns', 45720), ('lIns', 91440))]
        anchor = bp.get('anchor', 't'); nowrap = bp.get('wrap') == 'none'
        paras = []
        for p in txBody.findall('a:p', NS):
            ppr = p.find('a:pPr', NS); algn = (ppr.get('algn') if ppr is not None else None) or 'l'
            ta = {'l': 'left', 'ctr': 'center', 'r': 'right', 'just': 'justify'}.get(algn, 'left')
            lh = ''
            if ppr is not None:
                sp = ppr.find('a:lnSpc/a:spcPct', NS); spt = ppr.find('a:lnSpc/a:spcPts', NS)
                if sp is not None: lh = 'line-height: %s' % q(int(sp.get('val'))/100000*1.2)
                elif spt is not None: lh = 'line-height: %s' % cq(int(spt.get('val'))/100*4/3)
            runs = []; size_px = None
            for r in p.findall('a:r', NS):
                rp = r.find('a:rPr', NS); t0 = r.find('a:t', NS).text or ''
                t = fix(t0)
                grow = len(t.strip()) / max(len(t0.replace('&quot;', '"').strip()), 1)
                css = []
                if rp is not None:
                    if rp.get('sz'):
                        size_px = int(rp.get('sz'))/100*4/3
                        if grow > 1.05 and size_px >= 24:   # a longer converted figure in a big display number: shrink it to keep the same width
                            css.append('font-size: %s' % cq(size_px * max(1/grow, 0.45))); css.append('white-space: nowrap')
                        else: css.append('font-size: %s' % cq(size_px))
                    if rp.get('b') == '1': css.append('font-weight: 700')
                    if rp.get('i') == '1': css.append('font-style: italic')
                    if rp.get('u') == 'sng': css.append('text-decoration: underline')
                    if rp.get('strike') and rp.get('strike') != 'noStrike': css.append('text-decoration: line-through')
                    if rp.get('spc'): css.append('letter-spacing: %s' % cq(int(rp.get('spc'))/100*4/3))
                    fc = color(rp.find('a:solidFill', NS))
                    if fc: css.append('color: %s' % fc)
                    hl = rp.find('a:highlight', NS)
                    if hl is not None and color(hl): css.append('background-color: %s' % color(hl))
                    lat = rp.find('a:latin', NS)
                    if lat is not None: css.append('font-family: %s' % FONTS.get(lat.get('typeface'), "'%s', sans-serif" % lat.get('typeface')))
                runs.append('<span style="%s">%s</span>' % ('; '.join(css), html.escape(t, quote=False)))
            if not runs:
                e = p.find('a:endParaRPr', NS); szp = int(e.get('sz'))/100*4/3 if e is not None and e.get('sz') else 16
                runs.append('<span style="font-size: %s">&#160;</span>' % cq(szp))
            paras.append('<p style="margin: 0; text-align: %s%s">%s</p>' % (ta, ('; ' + lh) if lh else '', ''.join(runs)))
        st = ['padding: %s %s %s %s' % tuple(emu_cq(v) for v in ins), 'display: flex', 'flex-direction: column',
              'justify-content: %s' % {'t': 'flex-start', 'ctr': 'center', 'b': 'flex-end'}.get(anchor, 'flex-start')]
        if nowrap: st.append('white-space: nowrap')
        return st, ''.join(paras)
    def slide(self, n, fix):
        x = ET.parse(os.path.join(self.root, 'ppt/slides/slide%d.xml' % n)).getroot(); rels = self.rels(n)
        bg = x.find('p:cSld/p:bg/p:bgPr', NS); bgcss = ''
        if bg is not None:
            sf = bg.find('a:solidFill', NS); gf = bg.find('a:gradFill', NS)
            bgcss = ('background-color: %s' % color(sf)) if sf is not None else (('background-image: %s' % grad_css(gf)) if gf is not None else '')
        parts = []
        for el in x.find('p:cSld/p:spTree', NS):
            tag = el.tag.split('}')[1]
            if tag == 'sp':
                spPr = el.find('p:spPr', NS); st, _ = self.box_style(spPr); fills = self.fill_css(spPr, rels); st += fills
                tx = el.find('p:txBody', NS); inner = ''
                if tx is not None and any((t.text or '').strip() for t in tx.iter('{%s}t' % NS['a'])):
                    tst, inner = self.text_html(tx, fix); st += tst
                bf = spPr.find('a:blipFill', NS)
                if bf is not None:
                    img = self.blip_img(bf, rels)
                    if inner:   # image-filled shape with text on top
                        tst = [s for s in st if s.startswith(('padding', 'display', 'flex-direction', 'justify-content', 'white-space'))]
                        geo = [s for s in st if s not in tst]
                        inner = img + '<div style="position: absolute; inset: 0; %s">%s</div>' % ('; '.join(tst), inner)
                        st = geo
                    else: inner = img
                    st.append('overflow: hidden')
                if not fills and not inner: continue
                parts.append('<div style="%s">%s</div>' % ('; '.join(st), inner))
            elif tag == 'pic':
                spPr = el.find('p:spPr', NS); st, _ = self.box_style(spPr); st += self.fill_css(spPr, rels); st.append('overflow: hidden')
                parts.append('<div style="%s">%s</div>' % ('; '.join(st), self.blip_img(el.find('p:blipFill', NS), rels)))
        html = '\n'.join(parts)
        if n == 8 and getattr(self, 'gads_icon', True): html = fix_channel_icon(html)
        return bgcss, html


# Slide 8: the PowerPoint export flattened the channel icon into a red box with a black "G". Swap in a clean search-ads icon in the deck colours.
ICON = ('<div aria-hidden="true" style="position: absolute; left: 44.5%; top: 36.3%; width: 11%; height: 19%; display: flex; align-items: center; justify-content: center">'
        '<svg viewBox="0 0 100 100" width="100%" height="100%" fill="none">'
        '<circle cx="43" cy="43" r="27" stroke="#142C49" stroke-width="7"></circle>'
        '<path d="M63 63L84 84" stroke="#C6A667" stroke-width="11" stroke-linecap="round"></path>'
        '<rect x="27" y="33" width="32" height="20" rx="5" fill="#C6A667"></rect>'
        '<text x="43" y="48" text-anchor="middle" font-family="Helvetica Neue, Helvetica, Arial, sans-serif" font-size="14" font-weight="700" fill="#142C49">Ad</text>'
        '</svg></div>')
def fix_channel_icon(html):
    import re
    html2 = re.sub(r'<div style="[^"]*background-color: #EA4335"></div>\n?', '', html, count=1)
    html2 = re.sub(r'<div style="[^"]*"><p[^>]*><span style="font-size: 11\.979cqw[^"]*">G</span></p></div>', ICON, html2, count=1)
    assert html2 != html and ICON in html2, 'slide 8 icon patch failed'
    return html2
