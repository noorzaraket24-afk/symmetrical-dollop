import subprocess, numpy as np, sys
SR=44100; TARGET=float(sys.argv[1])
raw=subprocess.run(["ffmpeg","-v","error","-i","music.mp3","-ac","2","-ar",str(SR),"-f","f32le","-"],capture_output=True).stdout
x=np.frombuffer(raw,np.float32).reshape(-1,2).copy(); END=len(x)/SR
m=x.mean(1); hop=441; win=2048
n=(len(m)-win)//hop
frames=np.stack([m[i*hop:i*hop+win]*np.hanning(win) for i in range(n)])
S=np.abs(np.fft.rfft(frames,axis=1))[:, :400]
# 40 log bands
edges=np.unique(np.geomspace(2,400,41).astype(int)); B=np.stack([S[:,edges[i]:edges[i+1]].mean(1) for i in range(len(edges)-1)],1)
F=np.log(B+1e-6); F=(F-F.mean(0))/(F.std(0)+1e-6)   # 100 fps features
def dist(a,b,w=150):  # compare 1.5s windows centred at frame a and b
    return np.mean((F[a-w//2:a+w//2]-F[b-w//2:b+w//2])**2)
best=None
need=TARGET-END
for k in (2,3):
    L=need/k
    for A in range(500,2200,2):          # 5s..22s
        for Bf in range(int((A/100+L-1.2)*100), int((A/100+L+1.2)*100), 2):
            if Bf+80>=len(F) or Bf/100>END-6: continue
            d=dist(A,Bf)
            if best is None or d<best[0]: best=(d,A,Bf,k)
d,A,Bf,k=best
print(f"best: A={A/100:.2f}s B={Bf/100:.2f}s loops={k} dist={d:.3f}")
# refine junction by sample cross-correlation (+-30ms)
a=int(A/100*SR); b=int(Bf/100*SR); seg=m[b:b+4096]
cc=[np.dot(seg,m[a+o:a+o+4096]) for o in range(-1323,1323)]
a+= int(np.argmax(cc))-1323
L=b-a; fade=int(0.35*SR); out=[x[:b]]
cur_end=b
for i in range(k):
    last = (i==k-1)
    piece=x[a: (len(x) if last else b)].copy()
    # equal-power crossfade at the junction
    t=np.linspace(0,1,fade)[:,None]
    tail=out[-1][-fade:].copy()
    head=piece[:fade]
    blend=tail*np.cos(t*np.pi/2)+head*np.sin(t*np.pi/2)
    out[-1]=out[-1][:-fade]; out.append(blend); out.append(piece[fade:])
y=np.concatenate(out)
print("length", len(y)/SR)
y.astype(np.float32).tofile("music_ext.f32")
subprocess.run(["ffmpeg","-v","error","-y","-f","f32le","-ar",str(SR),"-ac","2","-i","music_ext.f32","-c:a","libmp3lame","-b:a","256k","music_ext.mp3"],check=True)
