import soundfile as sf, numpy as np, subprocess, io, json, re, os, sys
import pyloudnorm as pyln
from scipy.signal import resample_poly
from manifest import S, CATS
from seg import segs
OUT='/workspace/work/sfx-site/build_audio'; os.makedirs(OUT,exist_ok=True)
SR=48000
def load(p):
    out=subprocess.run(['ffmpeg','-v','error','-i',p,'-ar',str(SR),'-f','wav','-acodec','pcm_f32le','-'],capture_output=True).stdout
    d,sr=sf.read(io.BytesIO(out),dtype='float64',always_2d=True); return d
def tp(x): 
    return 20*np.log10(np.abs(resample_poly(x,4,1,axis=0)).max()+1e-12)
def slug(s): return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')
meta=[]
for cat,name,path,o in S:
    d=load(path); n=len(d)
    a,b=0,n
    if 'seg' in o:
        sg,_=segs(path); i=o['seg']
        a=int(max(0,sg[i][0]-0.01)*SR); b=int((sg[i+1][0]-0.02)*SR) if i+1<len(sg) else n
    if 't' in o: a=int(o['t'][0]*SR); b=min(n,int(o['t'][1]*SR))
    x=d[a:b]
    env=np.abs(x).max(axis=1); pk=env.max()
    st=np.argmax(env>pk*10**(-40/20)); st=max(0,st-int(0.004*SR))
    if 't' in o: st=0
    en=len(env)-np.argmax(env[::-1]>pk*10**(-60/20)); en=min(len(env),en+int(0.02*SR))
    x=x[st:en]
    capped=False
    if 'max' in o and len(x)>o['max']*SR: x=x[:int(o['max']*SR)]; capped=True
    L=len(x); 
    fin=int(o.get('fin',0.003)*SR); x[:fin]*=np.linspace(0,1,fin)[:,None]
    fo=int((0.4 if capped or 't' in o else min(0.05,L/SR*0.15))*SR); x[-fo:]*=np.linspace(1,0,fo)[:,None]**2
    if x.shape[1]==2 and np.allclose(x[:,0],x[:,1],atol=1e-4): x=x[:,:1]
    meter=pyln.Meter(SR,block_size=min(0.4,max(0.05,L/SR*0.9)))
    xx=x if x.shape[1]>1 else x[:,0]
    try: lu=meter.integrated_loudness(xx)
    except Exception: lu=pyln.Meter(SR,block_size=0.02).integrated_loudness(xx)
    peak=tp(x); gl=-14-lu; gp=-1-peak
    g=gl if gl<=gp else min(gl,gp+6)
    fname=slug(name); os.makedirs(f'{OUT}/{cat}',exist_ok=True)
    wav=f'{OUT}/{cat}/{fname}.wav'; mp3=f'{OUT}/{cat}/{fname}.mp3'
    tmp=f'/tmp/p_{fname}.wav'; adj=0
    for it in range(5):
        y=x*10**(g/20); lim=g>gp
        sf.write(tmp,y.astype('float32'),SR,subtype='FLOAT')
        af=('alimiter=limit=0.84:attack=1:release=60:level=disabled,' if lim else '')+f'volume={adj}dB'
        subprocess.run(['ffmpeg','-v','error','-y','-i',tmp,'-af',af,'-c:a','pcm_s24le',wav],check=True)
        subprocess.run(['ffmpeg','-v','error','-y','-i',wav,'-c:a','libmp3lame','-b:a','320k','-id3v2_version','3','-metadata',f'title={name}','-metadata','comment=CC0 public domain',mp3],check=True)
        ftp=max(tp(load(mp3)),tp(load(wav)))
        if ftp<=-1.0: break
        adj-=(ftp+1.0)+0.2
    z=load(wav); m2=pyln.Meter(SR,block_size=min(0.4,max(0.05,len(z)/SR*0.9))); zz=z if z.shape[1]>1 else z[:,0]
    try: fl=m2.integrated_loudness(zz)
    except Exception: fl=pyln.Meter(SR,block_size=0.02).integrated_loudness(np.concatenate([zz,zz]))
    meta.append(dict(cat=cat,name=name,file=fname,src=path,dur=round(len(z)/SR,2),lufs=float(round(fl,1)),tp=float(round(ftp,1)),ch=z.shape[1],lim=bool(lim),lufs_=0,mp3=os.path.getsize(mp3),wav=os.path.getsize(wav)))
    print(f"{cat[:12]:12} {name[:28]:28} {len(z)/SR:5.2f}s ch{z.shape[1]} LUFS {fl:6.1f} TP {ftp:5.1f} lim={lim}")
json.dump(meta,open(OUT+'/meta.json','w'),indent=1)
