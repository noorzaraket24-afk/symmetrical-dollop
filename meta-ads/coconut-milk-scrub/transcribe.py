import sherpa_onnx, numpy as np, wave, json, sys
M='models/sherpa-onnx-whisper-turbo/'
rec=sherpa_onnx.OfflineRecognizer.from_whisper(encoder=M+'turbo-encoder.int8.onnx',decoder=M+'turbo-decoder.int8.onnx',tokens=M+'turbo-tokens.txt',language='ar',task='transcribe',num_threads=4,tail_paddings=1000)
w=wave.open('audio.wav'); sr=w.getframerate(); a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768
P=[2.35,2.57,19.91,20.12,24.77,25.07,31.60,31.97,32.87,33.07,34.73,35.05,46.27,46.79,47.36,47.67,52.22,52.44,53.70,54.25,55.33,55.59,62.19,62.49,69.85,70.07,72.39,72.59,91.71,91.92,101.60,102.29,104.43,104.75,107.72,108.04,114.23,114.49,116.68,116.98,118.68,119.41,126.55,126.76,131.16,131.51,140.22,140.50]
bounds=[0.0]+P+[len(a)/sr]
segs=[(bounds[i],bounds[i+1]) for i in range(0,len(bounds)-1,2)]
out=[]
for s,e in segs:
    st=rec.create_stream(); st.accept_waveform(sr,a[int(s*sr):int(e*sr)]); rec.decode_stream(st)
    t=st.result.text.strip(); out.append((s,e,t)); print(f"[{s:6.2f}-{e:6.2f}] {t}",flush=True)
json.dump(out,open('transcript.json','w'),ensure_ascii=False,indent=1)
