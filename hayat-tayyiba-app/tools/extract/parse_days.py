import re,json,importlib.util
spec=importlib.util.spec_from_file_location('ex3','ex3.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
res={}
for st in (1,2,3):
    days=[]
    for pno,ws in enumerate(m.pages(f'pdf/s{st}.pdf'),1):
        L=m.lines(ws)
        big=[l for l in L if l['h']>30 and l['x1']>370]
        if not big or not any('بذرة اليوم' in l['t'] or 'ورقة اليوم' in l['t'] or 'ثمرة اليوم' in l['t'] or 'اليوم' in l['t'] for l in L if l['x1']<100): continue
        wd=[l for l in L if 60<l['y']<70 and l['h']>9]
        date=[l for l in L if 72<l['y']<80 and l['x1']>300]
        qs=[l for l in L if 130<l['y']<500 and abs(l['h']-8.1)<0.3 and l['x1']>=316 and l['x1']<=322]
        # group question lines by section (y bands)
        bands={'m':[], 'n':[], 'e':[]}
        for q in qs:
            k='m' if q['y']<225 else ('n' if q['y']<345 else 'e')
            bands[k].append(q['t'])
        meta=[l['t'] for l in L if 95<l['y']<105]
        days.append(dict(page=pno,num=big[0]['t'],wd=wd[0]['t'] if wd else '',date=date[0]['t'] if date else '',meta=meta,
            q=[' '.join(bands[k]) for k in 'mne'], nlines=[len(bands[k]) for k in 'mne'],
            seed=[l['t'] for l in L if l['x1']<100 and l['y']<85]))
    res[st]=days
    print(st,len(days),days[0]['seed'],sum(1 for d in days if max(d['nlines'])!=1 or min(d['nlines'])!=1))
json.dump(res,open('days.json','w'),ensure_ascii=False,indent=0)
