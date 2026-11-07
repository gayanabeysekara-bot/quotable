import numpy as np, subprocess, sys, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
src=Image.open(sys.argv[1]).convert('RGB'); SW,SH=src.size
W,H,FPS,DUR=1080,1350,30,32.0; AR=H/W
# warm grade the source once: lift reds slightly, cream paper
a=np.asarray(src).astype(np.float32)
a[...,0]=a[...,0]*1.0+4; a[...,1]=a[...,1]*0.985; a[...,2]=a[...,2]*0.94
src=Image.fromarray(np.clip(a,0,255).astype(np.uint8))
def ease(x): x=min(max(x,0),1); return x*x*(3-2*x)
# (start,end,(cx,cy,w) from,(cx,cy,w) to)
shots=[(0,6.4,(543,724,1086),(560,660,960)),
       (5.6,11.8,(690,410,560),(705,395,450)),
       (11.0,16.6,(780,520,620),(640,660,620)),
       (15.8,21.6,(650,1170,600),(650,1235,500)),
       (20.8,27.0,(470,330,660),(690,390,660)),
       (26.2,32.0,(690,430,700),(543,724,1086))]
X=0.8
def crop(cx,cy,w):
    h=w*AR
    if h>SH: h=SH; w=h/AR
    x0=min(max(cx-w/2,0),SW-w); y0=min(max(cy-h/2,0),SH-h)
    return src.transform((W,H),Image.EXTENT,(x0,y0,x0+w,y0+h),Image.BICUBIC)
def shot_frame(s,t):
    a,b,p,q=s; u=ease((t-a)/(b-a))
    return crop(*[p[i]+(q[i]-p[i])*u for i in range(3)])
# heart sprite
def heart(sz,col):
    im=Image.new('RGBA',(sz*4,sz*4)); d=ImageDraw.Draw(im); S=sz*4
    pts=[(S/2+S*0.42*16*math.sin(t)**3/16, S*0.45-S*0.42*(13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t))/16) for t in np.linspace(0,2*math.pi,200)]
    d.polygon(pts,fill=col); return im.resize((sz,sz),Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.6))
rng=np.random.default_rng(7)
parts=[]
for i in range(26):
    sz=int(rng.uniform(18,46)); col=[(205,40,60),(225,90,150),(190,30,40)][i%3]
    parts.append(dict(img=heart(sz,col+(255,)),x=rng.uniform(40,W-40),t0=rng.uniform(-6,DUR),
        sp=rng.uniform(55,95),sw=rng.uniform(15,40),ph=rng.uniform(0,6),al=rng.uniform(0.35,0.7)))
bok=[]
for i in range(14):
    r=int(rng.uniform(30,80)); im=Image.new('RGBA',(r*2,r*2)); ImageDraw.Draw(im).ellipse((0,0,r*2-1,r*2-1),fill=(255,170,170,255))
    bok.append(dict(img=im.filter(ImageFilter.GaussianBlur(r/3)),x=rng.uniform(0,W),y=rng.uniform(0,H),ph=rng.uniform(0,6),r=r))
# vignette (warm cream edge)
yy,xx=np.mgrid[0:H,0:W]; d=np.sqrt(((xx-W/2)/(W/2))**2+((yy-H/2)/(H/2))**2)
vig=np.clip((d-0.75)/0.6,0,1)**1.5*0.55
vig_img=Image.fromarray((vig*255).astype(np.uint8))
cream=Image.new('RGB',(W,H),(250,236,228))
fT=ImageFont.truetype('/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf',78)
fS=ImageFont.truetype('/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf',44)
def text_layer(lines,alpha):
    lay=Image.new('RGBA',(W,H)); d=ImageDraw.Draw(lay); y=H-330
    for txt,f,col in lines:
        bw=d.textlength(txt,font=f); d.text(((W-bw)/2,y),txt,font=f,fill=col+(int(255*alpha),)); y+=f.size+22
    glow=Image.new('RGBA',(W,H),(255,250,245,0)); m=lay.split()[3].filter(ImageFilter.GaussianBlur(14)).point(lambda v:min(255,v*2))
    glow.putalpha(m); return Image.alpha_composite(glow,lay)
ff=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
    '-i',sys.argv[2],'-c:v','libx264','-preset','slow','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k',
    '-shortest','-movflags','+faststart',sys.argv[3]],stdin=subprocess.PIPE)
for n in range(int(DUR*FPS)):
    t=n/FPS; act=[s for s in shots if s[0]<=t<s[1]]
    fr=shot_frame(act[0],t)
    if len(act)>1: fr=Image.blend(fr,shot_frame(act[1],t),ease((t-act[1][0])/X))
    fr=Image.composite(cream,fr,vig_img)
    # soft breathing warm glow
    g=0.06+0.04*math.sin(t*0.9)
    fr=Image.blend(fr,ImageChops.screen(fr,Image.new('RGB',(W,H),(255,200,190))),g)
    o=Image.new('RGBA',(W,H))
    for b in bok:
        a_=0.10+0.08*math.sin(t*0.7+b['ph']); im=b['img'].copy(); im.putalpha(im.split()[3].point(lambda v:int(v*a_)))
        o.alpha_composite(im,(int(b['x']+20*math.sin(t*0.3+b['ph'])-b['r']),int(b['y']-8*t)%H-b['r'] if False else int(b['y']-b['r']+15*math.cos(t*0.25+b['ph']))))
    hearts_on=ease((t-3)/3)
    for p in parts:
        age=t-p['t0']; 
        if age<0: continue
        y=H+40-age*p['sp']
        if y<-60: continue
        x=p['x']+p['sw']*math.sin(age*1.1+p['ph'])
        fade=min(1,age/1.5)*min(1,(y+60)/250)*p['al']*hearts_on
        if fade<=0.01: continue
        im=p['img'].rotate(12*math.sin(age+p['ph']),expand=True,resample=Image.BICUBIC)
        im.putalpha(im.split()[3].point(lambda v,f=fade:int(v*f)))
        o.alpha_composite(im,(int(x-im.width/2),int(y)))
    if t>27.2:
        a_=ease((t-27.2)/1.4)
        o.alpha_composite(text_layer([("Some moments feel like love.",fT,(60,25,30)),("— and they stay with you",fS,(170,40,55))],a_))
    fr=Image.alpha_composite(fr.convert('RGBA'),o).convert('RGB')
    w_in=1-ease(t/1.6); w_out=ease((t-30.6)/1.4)
    wa=max(w_in,w_out)
    if wa>0: fr=Image.blend(fr,Image.new('RGB',(W,H),(253,248,244)),wa)
    ff.stdin.write(fr.tobytes())
ff.stdin.close(); ff.wait()
