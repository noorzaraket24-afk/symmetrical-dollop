import subprocess, numpy as np, sys
SRC=sys.argv[1]; FL=sys.argv[2]=="1"; X0,Y0,X1,Y1=[float(v) for v in sys.argv[3:7]]; wins=[tuple(map(float,w.split('-'))) for w in sys.argv[7:]]
def roi(ss,dur):
    W,H=576,1024
    crop=f"crop={int((X1-X0)*W)}:{int((Y1-Y0)*H)}:{int(X0*W)}:{int(Y0*H)}"
    vf=("hflip," if FL else "")+f"scale={W}:{H},{crop},format=gray,fps=30"
    raw=subprocess.run(["ffmpeg","-v","error","-ss",str(ss),"-t",str(dur),"-i",SRC,"-vf",vf,"-f","rawvideo","-"],capture_output=True).stdout
    w=int((X1-X0)*W); h=int((Y1-Y0)*H)
    return np.frombuffer(raw,np.uint8).reshape(-1,h,w).astype(np.float32)
def env(ss,dur):
    raw=subprocess.run(["ffmpeg","-v","error","-ss",str(ss),"-t",str(dur),"-i",SRC,"-ac","1","-ar","16000","-f","f32le","-"],capture_output=True).stdout
    a=np.frombuffer(raw,np.float32); n=len(a)//533
    e=np.sqrt((a[:n*533].reshape(n,533)**2).mean(1))  # ~30Hz
    return np.log(e+1e-4)
tot=None
for s,e in wins:
    r=roi(s,e-s); mo=-r.mean(axis=(1,2))  # darker mouth region = more open
    mv=np.abs(np.diff(r,axis=0)).mean(axis=(1,2)); mv=np.r_[mv[0],mv]
    ae=env(s,e-s); n=min(len(mo),len(ae)); mo,mv,ae=mo[:n],mv[:n],ae[:n]
    def z(x): x=x-np.convolve(x,np.ones(15)/15,'same'); return (x-x.mean())/(x.std()+1e-9)
    mo,mv,ae=z(mo),z(mv),z(ae)
    lags=range(-12,13); cs=[]
    for L in lags:  # L>0: audio delayed relative to video by L frames
        if L>=0: c=np.mean(mo[:n-L]*ae[L:])+np.mean(mv[:n-L]*ae[L:])
        else: c=np.mean(mo[-L:]*ae[:n+L])+np.mean(mv[-L:]*ae[:n+L])
        cs.append(c)
    cs=np.array(cs); tot=cs if tot is None else tot+cs
    print(f"win {s}-{e}: best lag {list(lags)[int(cs.argmax())]*33:+d}ms  ", ' '.join(f"{L*33}:{c:.2f}" for L,c in zip(lags,cs) if L%2==0))
print("ALL windows best lag (audio delay vs video):", list(range(-12,13))[int(tot.argmax())]*33, "ms")
