import pymupdf as fitz, json, re, io, sys, os
from PIL import Image
from playwright.sync_api import sync_playwright
A='/mnt/user-data/uploads/sr-lead-to-client/assets/Sarac-Ramsay-Google-Ads-Proposal-%s.pdf'
LOCS=[('UK','uk'),('Dubai','dubai'),('Marbella','marbella'),('HongKong','hongkong'),('Thailand','thailand')]
TITLES=["Cover","Director","About Sarac Ramsay","Clients","Results","How investors find an agency","The strategy","The channels","The opportunity","The problem","The plan: 3 components","From where you are","The route","Component 1: The intent","The keywords","Campaign structure","Why we build it this way","Component 2: Stand out","Same budget, better ad","What an investor sees","Component 3: The system","The target: 30","The 30 system","Smart bidding","Month 3: Hold the fort","The math","Google Ads plans","Our guarantee","Case study","Before","The result"]
W,H=1440.0,810.0
def fam(font):
    f=font.lower()
    if 'newsreader' in f: return "'Newsreader', Georgia, serif"
    if 'mono' in f: return "'Courier New', 'Liberation Mono', monospace"
    if 'serif' in f: return "Georgia, 'Times New Roman', serif"
    return "Arial, 'Liberation Sans', Helvetica, sans-serif"
def style_of(s):
    f=s['font'].lower()
    return ('700' if ('bold' in f or s['flags']&16) else '400'), ('italic' if ('ital' in f or s['flags']&2) else 'normal')
def collect(doc):
    pages=[]
    for p in doc:
        spans=[]; baked=[]
        for b in p.get_text('rawdict')['blocks']:
            for l in b.get('lines',[]):
                rot=abs(l['dir'][0]-1)>1e-3 or abs(l['dir'][1])>1e-3
                for s in l['spans']:
                    ch=s['chars']
                    while ch and ch[-1]['c'].isspace(): ch=ch[:-1]
                    while ch and ch[0]['c'].isspace(): ch=ch[1:]
                    if not ch: continue
                    raw=''.join(c['c'] for c in ch)
                    if len(raw.replace(' ',''))>2 and raw.replace(' ','').replace('·','').replace('/','').replace('.','').replace('-','').replace('—','').replace('%','').replace(':','').isupper():
                        keep=[]
                        for ci,c in enumerate(ch):
                            if c['c'].isspace() and 0<ci<len(ch)-1 and abs(c['bbox'][0]-ch[ci-1]['bbox'][2])<0.06 and abs(ch[ci+1]['bbox'][0]-c['bbox'][2])<0.06: continue
                            keep.append(c)
                        ch=keep
                    t=''
                    gaps=sorted(ch[k]['bbox'][0]-ch[k-1]['bbox'][2] for k in range(1,len(ch)) if not ch[k]['c'].isspace() and not ch[k-1]['c'].isspace())
                    med=gaps[len(gaps)//2] if gaps else 0
                    for ci,c in enumerate(ch):
                        if ci and not c['c'].isspace() and not ch[ci-1]['c'].isspace() and c['bbox'][0]-ch[ci-1]['bbox'][2]>max(med,0)+0.22*s['size']: t+=' '
                        t+=c['c']
                    if not t.strip(): continue
                    x0,y0,x1,y1=s['bbox']; x0=ch[0]['bbox'][0]; x1=ch[-1]['bbox'][2]
                    if rot or s['font'].startswith('Type3') or s['alpha']<40 or s['size']<=0 or False:
                        baked.append((x0,y0,x1,y1)); continue
                    w,st=style_of(s)
                    spans.append(dict(t=t,x0=x0,y0=y0,x1=x1,y1=y1,size=s['size'],fam=fam(s['font']),w=w,st=st,col='#%06x'%s['color'],al=s['alpha']))
        pages.append((spans,baked))
    return pages
def backgrounds(loc,key,pages):
    dA=fitz.open(A%loc)
    for p in dA:
        for xr in p.get_contents():
            data=dA.xref_stream(xr)
            dA.update_stream(xr, re.sub(rb'\bBT\b', b'BT 3 Tr', data))
    dB=fitz.open(A%loc)
    z=1600/W; mat=fitz.Matrix(z,z); os.makedirs('project/gads-pages',exist_ok=True)
    for i,(pa,pb) in enumerate(zip(dA,dB)):
        a=Image.open(io.BytesIO(pa.get_pixmap(matrix=mat,alpha=False).tobytes('png'))).convert('RGB')
        b=Image.open(io.BytesIO(pb.get_pixmap(matrix=mat,alpha=False).tobytes('png'))).convert('RGB')
        for (x0,y0,x1,y1) in pages[i][1]:
            box=(max(0,int(x0*z)-3),max(0,int(y0*z)-3),min(1600,int(x1*z)+3),min(900,int(y1*z)+3))
            a.paste(b.crop(box),box[:2])
        a.save('project/gads-pages/%s-%02d.webp'%(key,i+1),'WEBP',quality=82)
def measure(pw,allspans):
    pg=pw.new_page()
    css=open('/tmp/fontcss.txt').read()
    pg.goto('http://127.0.0.1:8891/GAdsUK.dc.html')
    pg.evaluate("css=>{document.body.innerHTML='';const st=document.createElement('style');st.textContent=css+' body{margin:0}span{position:absolute;white-space:pre;font-optical-sizing:none;font-variation-settings:\"opsz\" 16}';document.head.appendChild(st)}",css)
    items=[dict(t=s['t'],fam=s['fam'],w=s['w'],st=s['st'],size=s['size']) for s in allspans]
    pg.evaluate("""async (items)=>{ const fams=['Newsreader']; for(const w of [400,700]) for(const st of ['normal','italic']) { try{await document.fonts.load(st+' '+w+' 20px Newsreader','Ag')}catch(e){} } await document.fonts.ready; }""",items)
    res=pg.evaluate("""(items)=>items.map(it=>{const e=document.createElement('span');e.style.fontFamily=it.fam;e.style.fontWeight=it.w;e.style.fontStyle=it.st;e.style.fontSize='1000px';e.textContent=it.t;document.body.appendChild(e);const w=e.getBoundingClientRect().width/1000*it.size;e.remove();return w})""",items)
    pg.close(); return res
def num(x): return ('%.3f'%x).rstrip('0').rstrip('.')
def build(loc,key,pw):
    doc=fitz.open(A%loc); pages=collect(doc); backgrounds(loc,key,pages)
    allsp=[s for sp,_ in pages for s in sp]; nat=measure(pw,allsp); k=0
    secs=[]
    for i,(sp,_) in enumerate(pages):
        html=[]
        for s in sp:
            n=nat[k]; k+=1
            wpdf=s['x1']-s['x0']; ln=len(s['t'])
            ls=(wpdf-n)/(ln-1) if ln>1 else 0
            lsx=('letter-spacing: %scqw; '%num(ls/W*100)) if abs(ls)>0.012*s['size'] else ''
            h=s['y1']-s['y0']
            op=('opacity: %s; '%num(s['al']/255)) if s['al']<250 else ''
            html.append('<div style="position: absolute; left: %s%%; top: %s%%; height: %scqw; white-space: pre; font-family: %s; font-weight: %s; font-style: %s; font-size: %scqw; line-height: %scqw; %s%scolor: %s; font-optical-sizing: none; font-variation-settings: \'opsz\' 16">%s</div>'%(num(s['x0']/W*100),num(s['y0']/H*100),num(h/W*100),s['fam'],s['w'],s['st'],num(s['size']/W*100),num(h/W*100),lsx,op,s['col'],s['t'].replace('&','&amp;').replace('<','&lt;')))
        secs.append('<section aria-label="Slide %d: %s" style="display: {{v.s%d}}; position: relative; width: 100%%; aspect-ratio: 16 / 9; overflow: hidden; container-type: inline-size; background-color: #142C49"><img src="gads-pages/%s-%02d.webp" alt="" style="position: absolute; inset: 0; display: block; width: 100%%; height: 100%%; user-select: none; -webkit-user-drag: none" draggable="false">\n%s\n</section>'%(i+1,TITLES[i],i+1,key,i+1,'\n'.join(html)))
    out='''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Google Ads proposal: %s</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,700;1,6..72,400;1,6..72,700&amp;display=swap" rel="stylesheet">
<style>
body{margin:0}
</style>
</helmet>
<div style="display: grid; grid-template-columns: {{cols}}; gap: {{gap}}; padding: {{pad}}; background-color: {{bg}}">
%s
</div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{"slide":{"editor":null},"mode":{"editor":null},"$preview":{"width":1960,"height":2400}}'>
// Google Ads proposal, %s. Backgrounds are the text-free pages of the PDF (gads-pages/%s-NN.webp). Every piece of text is a live element
// placed exactly where the PDF has it (made by tools/gen_gads_from_pdf.py), so it can be edited.
class Component extends DCLogic {
  renderVals() {
    // mode "deck" (Lead to Client): one slide. mode "notes" (presenter view): nothing to show. No mode (artboard on the canvas): every slide.
    const mode = this.props.mode;
    const one = mode === 'deck' || mode === 'notes';
    const s = Math.max(0, Math.min(30, Number(this.props.slide) || 0));
    const v = {};
    for (let i = 1; i <= 31; i++) v['s' + i] = mode === 'notes' ? 'none' : ((!one || s === i - 1) ? 'block' : 'none');
    return { v, cols: one ? 'minmax(0, 1fr)' : 'repeat(3, minmax(0, 1fr))', gap: one ? '0' : '24px', pad: one ? '0' : '24px', bg: one ? 'transparent' : '#191919' };
  }
}
</script>
</body>
</html>
'''%(loc,'\n'.join(secs),loc,key)
    open('project/GAds%s.dc.html'%loc,'w').write(out)
    print(loc,len(out),len(allsp))
if __name__=='__main__':
    css=''
    for w in (400,700):
        for st in ('normal','italic'): css+="@font-face{font-family:'Newsreader';font-style:%s;font-weight:%d;src:url(http://127.0.0.1:8891/fonts/newsreader-latin-%d-%s.woff2) format('woff2')}"%(st,w,w,st)
    open('/tmp/fontcss.txt','w').write(css)
    with sync_playwright() as pw:
        br=pw.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox','--allow-file-access-from-files'])
        sel=sys.argv[1:] or [k for _,k in LOCS]
        for loc,key in LOCS:
            if key in sel: build(loc,key,br)
        br.close()
