import numpy as np, wave, sys
SR=44100; DUR=32.0; BPM=68; beat=60/BPM
N=int(SR*DUR); L=np.zeros(N); R=np.zeros(N)
def hz(m): return 440*2**((m-69)/12)
def piano(m,t0,d,v,pan=0.0):
    f=hz(m); n=int(SR*(d+2.5)); t=np.arange(n)/SR
    s=sum((0.6**k)*np.sin(2*np.pi*f*(k+1)*t*(1+0.0004*k)) for k in range(6))
    env=np.exp(-t*(1.6+f/900))*(1-np.exp(-t*300))
    rel=np.clip((d+2.5-t)/0.4,0,1); s*=env*rel*v
    i=int(t0*SR); e=min(N,i+n); s=s[:e-i]
    L[i:e]+=s*(1-pan)/2*2**.5*0.7; R[i:e]+=s*(1+pan)/2*2**.5*0.7
def pad(ms,t0,d,v):
    n=int(SR*d); t=np.arange(n)/SR
    env=np.minimum(1,t/1.5)*np.minimum(1,(d-t)/1.5)
    for m in ms:
        for det,p in ((-0.12,-0.7),(0.12,0.7)):
            f=hz(m)*2**(det/12)
            s=(np.sin(2*np.pi*f*t)+0.3*np.sin(4*np.pi*f*t))*env*v
            i=int(t0*SR); e=min(N,i+n)
            L[i:e]+=s[:e-i]*(1-p)/2; R[i:e]+=s[:e-i]*(1+p)/2
# D major: D A Bm G  (I V vi IV), 2 bars each... 4 beats per chord
chords=[[50,57,62,66],[45,52,57,61],[47,54,59,62],[43,50,55,59]]
bar=4*beat; start=0.6
for c in range(8):
    ch=chords[c%4]; t0=start+c*bar
    if t0>DUR-3: break
    pad([x+12 for x in ch[1:]],t0,bar+0.8,0.035)
    piano(ch[0]-12,t0,bar,0.35,-0.2)
    arp=[ch[0],ch[1],ch[2],ch[3],ch[2]+12,ch[3],ch[2],ch[1]]
    for k,m in enumerate(arp): piano(m,t0+k*beat/2,beat,0.13,0.15*np.sin(k))
# melody enters bar 3
mel=[(74,0,1.5),(73,1.5,.5),(71,2,2),(69,4,1.5),(71,5.5,.5),(73,6,2),
     (74,8,1),(76,9,1),(78,10,2),(76,12,1.5),(74,13.5,.5),(74,14,2),
     (81,16,1.5),(78,17.5,.5),(76,18,2),(74,20,1),(73,21,1),(69,22,2),
     (71,24,1.5),(73,25.5,.5),(74,26,4)]
for m,b,d in mel:
    t0=start+2*bar+b*beat
    if t0<DUR-2: piano(m,t0,d*beat,0.28,0.1)
# final ringing D chord
for m in [62,66,69,74,78]: piano(m,start+8*bar,3,0.15)
# reverb: stereo noise-decay impulse
rng=np.random.default_rng(1)
def verb(x,seed):
    n=int(SR*2.8); t=np.arange(n)/SR
    ir=np.random.default_rng(seed).standard_normal(n)*np.exp(-t*2.3); ir[0]=0
    F=1<<int(np.ceil(np.log2(len(x)+n)))
    return np.fft.irfft(np.fft.rfft(x,F)*np.fft.rfft(ir,F),F)[:len(x)]
wl=verb(L,1); wr=verb(R,2)
L=L+0.05*wl/np.abs(wl).max()*np.abs(L).max()*6; R=R+0.05*wr/np.abs(wr).max()*np.abs(R).max()*6
st=np.stack([L,R],1); t=np.arange(N)/SR
st*=np.minimum(1,t/1.0)[:,None]*np.clip((DUR-t)/2.5,0,1)[:,None]
st=np.tanh(st/np.abs(st).max()*1.1)*0.85
with wave.open(sys.argv[1],'wb') as w:
    w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR)
    w.writeframes((st*32767).astype('<i2').tobytes())
