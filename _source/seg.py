import soundfile as sf, numpy as np, sys, subprocess, io
def load(p):
    out=subprocess.run(['ffmpeg','-v','error','-i',p,'-f','wav','-acodec','pcm_f32le','-'],capture_output=True).stdout
    d,sr=sf.read(io.BytesIO(out),dtype='float32'); 
    return d,sr
def segs(p,rel=-35,gap=0.12):
    d,sr=load(p); m=np.abs(d).max(axis=1) if d.ndim>1 else np.abs(d)
    w=int(sr*0.01); n=len(m)//w
    env=m[:n*w].reshape(n,w).max(axis=1); pk=env.max(); th=pk*10**(rel/20)
    act=env>th; out=[];s=None;last=-999
    for i,a in enumerate(act):
        if a:
            if s is None: s=i
            elif (i-last)*0.01>gap: out.append((s,last)); s=i
            last=i
    if s is not None: out.append((s,last))
    return [(round(a*.01,2),round(b*.01+.01,2), round(20*np.log10(env[a:b+1].max()/pk+1e-9),1)) for a,b in out], round(len(m)/sr,2)
if __name__=='__main__':
    for p in sys.argv[1:]:
        s,L=segs(p); print(p.split('/')[-1],L,s[:12])
