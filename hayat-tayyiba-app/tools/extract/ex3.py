import sys, re, subprocess
MK='ً-ٰٟ'
def fixword(t):
    t=t[::-1]
    t=re.sub(f'([{MK}]+)([^{MK}])',lambda m:m.group(2)+m.group(1),t)
    t=re.sub(r'[0-9٠-٩][0-9٠-٩.,٫]*',lambda m:m.group(0)[::-1],t)
    # latin runs
    t=re.sub(r'[A-Za-z][A-Za-z0-9.]*',lambda m:m.group(0)[::-1],t)
    # ascending range like ١٩١–١٩٠ shown visually; swap "a–b" order to keep logical? keep as is
    return t
def pages(pdf):
    out=subprocess.run(['pdftotext','-bbox',pdf,'-'],capture_output=True,text=True).stdout
    for pg in out.split('<page ')[1:]:
        ws=[]
        for m in re.finditer(r'xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>',pg):
            x0,y0,x1,y1=map(float,m.groups()[:4]); t=m.group(5).replace('&amp;','&').replace('&lt;','<').replace('&gt;','>').replace('&quot;','"')
            ws.append(dict(x0=x0,y0=y0,x1=x1,y1=y1,h=y1-y0,c=(y0+y1)/2,t=fixword(t),raw=t))
        yield ws
isclw=lambda w: bool(re.search(f'[{MK}]',w['t'])) and len(re.sub(f'[{MK}]','',w['t']))<=2
def lines(ws):
    iscl=lambda w: re.search(f'[{MK}]',w['t']) and len(re.sub(f'[{MK}]','',w['t']))<=2
    cl=[w for w in ws if iscl(w)]; nc=[w for w in ws if not iscl(w)]
    nc=sorted(nc,key=lambda w:w['y1'])
    rows=[]
    for w in nc:
        for r in rows:
            if abs(r['y1']-w['y1'])<w['h']*0.3 and abs(r['h']-w['h'])<w['h']*0.3: r['ws'].append(w); break
        else: rows.append(dict(y1=w['y1'],h=w['h'],ws=[w]))
    for w in cl:
        best=None;bd=1e9
        for r in rows:
            dy=r['y1']-w['y1']
            if -w['h']*0.6<=dy<=w['h']*1.15 and abs(r['h']-w['h'])<w['h']*0.45 and len(r['ws'])>0:
                xs0=min(x['x0'] for x in r['ws']);xs1=max(x['x1'] for x in r['ws'])
                if xs0-9<=w['x0'] and w['x1']<=xs1+6 and abs(dy)<bd: bd=dy;best=r
        if best: best['ws'].append(w)
        else: rows.append(dict(y1=w['y1'],h=w['h'],ws=[w]))
    res=[]
    for r in sorted(rows,key=lambda r:r['y1']):
        ws=sorted(r['ws'],key=lambda w:-w['x1'])
        segs=[[ws[0]]]
        for w in ws[1:]:
            p=segs[-1][-1]
            if min(x['x0'] for x in segs[-1])-w['x1']>r['h']*2.2: segs.append([w])
            else: segs[-1].append(w)
        for seg in segs:
            s='';left=None;prev=None
            for w in seg:
                if left is not None:
                    th=0.2
                    if prev is not None and isclw(prev):
                        th=0.48 if '\u0651' in prev['t'] and not re.search('[\u064B-\u064D]',prev['t']) else 0.3
                    if left-w['x1']>r['h']*th: s+=' '
                s+=w['t']; left=w['x0'] if left is None else min(left,w['x0']); prev=w
            res.append(dict(y=round(r['y1'],1),h=round(r['h'],1),x0=round(min(w['x0'] for w in seg)),x1=round(max(w['x1'] for w in seg)),t=s))
    return res
if __name__=='__main__':
    for i,ws in enumerate(pages(sys.argv[1]),1):
        if int(sys.argv[2])<=i<=int(sys.argv[3]):
            print('=== page',i)
            for l in lines(ws): print(l['y'],l['h'],l['x0'],l['x1'],l['t'])
