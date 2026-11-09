import re, sys
main = sys.argv[1]; out = sys.argv[2]
s = open(main, encoding='utf-8').read()
a = s.index('<!-- STALL · THINK ABOUT IT -->'); b = s.index('</div>\n</aside>', a)
body = s[a:b].rstrip()
# inline base styles so the artboard reads well on its own; Main's helmet adds hover/open states on the same classes
ST = {
 'obj': "border: 1px solid #2F2F2F; border-radius: 8px; background-color: #202020; overflow: hidden",
 'obj-q': "flex: 1; font-size: 15px; font-weight: 600; line-height: 1.35; color: #E6E6E4",
 'obj-chev': None,
 'obj-body': "padding: 4px 16px 16px; display: flex; flex-direction: column; gap: 4px; border-top: 1px solid #2B2B2B",
 'opt': "display: flex; gap: 12px; align-items: flex-start; padding-top: 12px",
 'opt-n': "flex: none; width: 22px; height: 22px; margin-top: 2px; border-radius: 50%; background-color: #2F80C8; color: #FFFFFF; font-size: 11px; font-weight: 700; display: flex; align-items: center; justify-content: center",
 'opt-main': "flex: 1; min-width: 0",
 'opt-say': "margin: 0; font-size: 14.5px; line-height: 1.55; color: #E6E6E4",
 'branch': "margin-top: 10px; padding: 10px 12px; border-radius: 8px; background-color: #252525; border-left: 2px solid #DFAB01; display: flex; flex-direction: column; gap: 6px",
 'if': "align-self: flex-start; font-size: 11px; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase; color: #DFAB01",
 'br-say': "margin: 0; font-size: 14px; line-height: 1.5; color: #E6E6E4",
 'br-note': "margin: 0; font-size: 13px; line-height: 1.5; color: #9B9B97",
 'go': "display: inline-block; padding: 1px 8px; border-radius: 6px; background-color: #1F302C; color: #4DAB9A; font-size: 12px; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase",
 'ph': "padding: 0 5px; border-radius: 6px; background-color: #3A3220; color: #DFAB01; white-space: nowrap",
}
CAT = {'stall': ('#3A3220', '#DFAB01'), 'decision': ('#1F2D38', '#529CCA'), 'timing': ('#2A2440', '#A78BFA'), 'money': ('#1F302C', '#4DAB9A'), 'trust': ('#3A2321', '#FF7369')}
def add_style(tag):
    m = re.search(r'class="([^"]*)"', tag)
    if not m: return tag
    classes = m.group(1).split()
    st = None
    for c in classes:
        if c.startswith('cat-'):
            bg, fg = CAT[c[4:]]
            st = "flex: none; padding: 3px 7px; border-radius: 6px; background-color: %s; color: %s; font-size: 10px; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; white-space: nowrap" % (bg, fg)
        elif c in ST and ST[c]:
            st = ST[c]
    if not st: return tag
    if 'style="' in tag:
        return tag.replace('style="', 'style="' + st + '; ', 1)
    return tag[:-1] + ' style="' + st + '">'
body = re.sub(r'<(?:details|span|div|p)\b[^>]*class="[^"]*"[^>]*>', lambda m: add_style(m.group(0)), body)
body = body.replace('<summary>', '<summary style="list-style: none; display: flex; align-items: center; gap: 10px; padding: 14px 16px; cursor: pointer">')
# the arrow that Main drew with CSS is now part of the text, so it shows everywhere
body = re.sub(r'(<span class="if"[^>]*>)', r'\1↳ ', body)
doc = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Objection handling</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&amp;display=swap" rel="stylesheet">
<style>
body{margin:0}
</style>
</helmet>
<!-- OBJECTION HANDLING (Proposal Call). Shown in the Objections panel and in presenter view. Every line is plain text: double-click it on the canvas to edit. -->
<div style="width: 100%%; box-sizing: border-box; display: flex; flex-direction: column; gap: 14px; padding: {{pad}}; background-color: {{bg}}; font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif; color: #E6E6E4">
<div role="group" aria-label="Filter objections" style="display: flex; gap: 6px; flex-wrap: wrap">
<sc-for list="{{cats}}" as="oc" hint-placeholder-count="6"><button class="step-tab {{oc.cls}}" type="button" onClick="{{oc.go}}" aria-pressed="{{oc.pressed}}" style="min-height: 30px; box-sizing: border-box; padding: 0 10px; border: 1px solid {{oc.bd}}; border-radius: 6px; background-color: {{oc.bg}}; color: #E6E6E4; font-family: inherit; font-size: 12px; font-weight: 600; cursor: pointer">{{oc.label}}</button></sc-for>
</div>
<div style="display: flex; flex-direction: column; gap: 10px">
%s
</div>
</div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{"embedded":{"editor":null},"$preview":{"width":520,"height":1500}}'>
class Component extends DCLogic {
  constructor(props) {
    super(props);
    this.state = { cat: 'all' };
  }
  renderVals() {
    const cat = this.state.cat || 'all';
    const embedded = !!this.props.embedded;
    const ov = {};
    ['stall', 'decision', 'timing', 'money', 'trust'].forEach((k) => { ov[k] = (cat === 'all' || cat === k) ? 'block' : 'none'; });
    return {
      ov,
      pad: embedded ? '0' : '20px',
      bg: embedded ? 'transparent' : '#191919',
      cats: [['all', 'All'], ['stall', 'Stall'], ['decision', 'Decision makers'], ['timing', 'Timing'], ['money', 'Money'], ['trust', 'Trust']].map(([key, label]) => ({
        label,
        cls: cat === key ? 'is-on' : '',
        pressed: cat === key ? 'true' : 'false',
        bg: cat === key ? '#1F2D38' : '#202020',
        bd: cat === key ? '#2C5272' : '#2F2F2F',
        go: () => this.setState({ cat: key })
      }))
    };
  }
}
</script>
</body>
</html>
''' % body
open(out, 'w', encoding='utf-8').write(doc)
print(len(doc), body.count('<details'))
