import re,json,importlib.util
spec=importlib.util.spec_from_file_location('ex3','ex3.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
days=json.load(open('days.json'))
Q=lambda l: l['h']>=20 and l['y']>95
def prose(ls): return re.sub(r'\s+',' ',' '.join(l['t'] for l in ls)).strip()
out={}
for st in (1,2,3):
    dp={d['page'] for d in days[str(st)]}
    pages=[]
    for pno,ws in enumerate(m.pages(f'pdf/s{st}.pdf'),1):
        if pno in dp or pno in (1,2,3,7) or pno>=150 and pno==max(dp)+3: pass
        if pno in dp or pno in (1,2,3,7): continue
        L=[l for l in m.lines(ws) if l['y']<575]
        if not L: continue
        hdr=L[0]['t']; P=dict(page=pno,hdr=hdr)
        if hdr.startswith('الشهر'):
            P['type']='month'
            P['name']=[l['t'] for l in L if 20<l['h']<30][0]
            P['theme']=[l['t'] for l in L if 120<l['y']<132 and 8<l['h']<10][0]
            qi=[i for i,l in enumerate(L) if l['t'].startswith('«')][0]
            P['intro']=prose([l for l in L[:qi] if 7.5<l['h']<9 and l['y']>138])
            qs=[];i=qi
            while not L[i]['t'].startswith('—'): qs.append(L[i]); i+=1
            P['quote']=prose(qs); P['quote_src']=L[i]['t'].lstrip('— ')
            bi=[i for i,l in enumerate(L) if l['t'] in ('من سيرته','من وصاياه')][0]
            wi=[i for i,l in enumerate(L) if l['t']=='أسابيع الشهر'][0]
            P['box_title']=L[bi]['t']
            P['box']=prose([l for l in L[bi+1:wi] if l['h']>6.6])
            src=[l['t'] for l in L[bi+1:wi] if l['h']<=6.6]
            P['box_src']=' '.join(src)
            P['weeks']=[l['t'] for l in L[wi+1:] if l['x1']<330 and l['h']<7]
        elif hdr.startswith('الأسبوع'):
            P['type']='week'
            P['title']=L[1]['t']
            rest=[l for l in L[2:] if l['y']<170]
            q=[l for l in rest if l['h']>9 and l['h']<14]
            src=[l for l in rest if l['h']<7]
            P['quote']=prose(q); P['quote_src']=prose(src).lstrip('— ')
            P['raw']=[(l['y'],l['h'],l['t']) for l in rest]
        else:
            P['type']='other'
            P['raw']=[(l['y'],l['h'],l['x1'],l['t']) for l in L]
        pages.append(P)
    out[st]=pages
json.dump(out,open('pages.json','w'),ensure_ascii=False,indent=1)
