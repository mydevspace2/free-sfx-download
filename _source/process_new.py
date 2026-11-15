"""Process candidate additions (grow/cands.py) the same way as src/process.py:
trim lead silence, 3 ms fade-in (or opts fin), short fade-out (0.4 s when cut/capped, 0.8 s for ambience caps),
level towards -14 LUFS with true peak <= -1 dBTP, export MP3 320k + WAV 48k/24-bit into build_audio/<cat>/.
Extra crop rules: auto event grouping (gap<=0.35 s, max 6 s), one=True (first event only), seg=i, pick='longest', cap=True (ambience 6 s).
Usage: python3 process_new.py START END   (indexes into C); results appended to grow/meta_new/<slug>.json
"""
import soundfile as sf, numpy as np, subprocess, io, json, re, os, sys, glob
import pyloudnorm as pyln
from scipy.signal import resample_poly
sys.path.insert(0, '/workspace/work/sfx-site/grow'); sys.path.insert(0, os.path.dirname(__file__))
from cands import C
from seg import segs
SRC = '/workspace/work/sfx-site/src/'
OUT = '/workspace/work/sfx-site/build_audio'
MD = '/workspace/work/sfx-site/grow/meta_new'; os.makedirs(MD, exist_ok=True)
SR = 48000
def path(s):
    if s.startswith('B'):
        g = [x for x in glob.glob(SRC + f'bsb/flac/{s[1:]}.*') if x.endswith(('.flac', '.wav'))]
        g.sort(key=lambda x: not x.endswith('.flac'))
        return g[0]
    return SRC + s
def load(p):
    out = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ar', str(SR), '-f', 'wav', '-acodec', 'pcm_f32le', '-'], capture_output=True).stdout
    d, sr = sf.read(io.BytesIO(out), dtype='float64', always_2d=True); return d
def tp(x):
    return 20 * np.log10(np.abs(resample_poly(x, 4, 1, axis=0)).max() + 1e-12)
def slug(s): return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')

def crop(p, o, n):
    """returns (a, b, cut) sample indexes"""
    if 't' in o: return int(o['t'][0]*SR), min(n, int(o['t'][1]*SR)), True
    sg, L = segs(p, rel=-35, gap=0.25)
    mx = o.get('max', 6.0)
    if o.get('cap'):
        a = sg[0][0] if sg else 0
        return int(a*SR), min(n, int((a + o.get('max', 6.0))*SR)), True
    if 'seg' in o or o.get('one') or o.get('pick'):
        i = o.get('seg', 0)
        if o.get('pick') == 'longest':
            i = max(range(len(sg)), key=lambda k: sg[k][1]-sg[k][0])
        a = max(0, sg[i][0]-0.01); b = (sg[i+1][0]-0.02) if i+1 < len(sg) else n/SR
        b = min(b, sg[i][1] + 1.2, a + mx)
        return int(a*SR), min(n, int(b*SR)), (i+1 < len(sg)) or b < n/SR
    # auto grouping
    if not sg: return 0, n, False
    a = sg[0][0]; e = sg[0][1]
    for s0, s1, _ in sg[1:]:
        if s0 - e <= 0.35 and s1 - a <= mx: e = s1
        else: break
    nxt = [s0 for s0, _, _ in sg if s0 > e]
    b = min(e + 1.0, nxt[0]-0.02 if nxt else n/SR, a + mx)
    cut = b < n/SR - 0.05
    return int(max(0, a-0.01)*SR), min(n, int(b*SR)), cut

def proc(k):
    cat, name, s, o = C[k]
    p = path(s); d = load(p); n = len(d)
    a, b, cut = crop(p, o, n)
    x = d[a:b].copy()
    env = np.abs(x).max(axis=1); pk = env.max()
    if pk < 1e-4: return dict(name=name, err='silent')
    st = np.argmax(env > pk*10**(-40/20)); st = max(0, st-int(0.004*SR))
    if 't' in o or o.get('cap'): st = 0
    en = len(env) - np.argmax(env[::-1] > pk*10**(-60/20)); en = min(len(env), en+int(0.02*SR))
    if not cut: x = x[st:en]
    else: x = x[st:]
    capped = False
    mx = o.get('max', 6.0 if not o.get('cap') else 6.0)
    if len(x) > mx*SR: x = x[:int(mx*SR)]; capped = True
    L = len(x)
    fin = int(o.get('fin', 0.003)*SR); x[:fin] *= np.linspace(0, 1, fin)[:, None]
    fo_s = 0.8 if o.get('cap') else (0.4 if (capped or cut) else min(0.05, L/SR*0.15))
    fo = max(1, min(int(fo_s*SR), L//3)); x[-fo:] *= np.linspace(1, 0, fo)[:, None]**2
    if x.shape[1] == 2 and np.allclose(x[:, 0], x[:, 1], atol=1e-4): x = x[:, :1]
    if x.shape[1] > 2: x = x[:, :2]
    meter = pyln.Meter(SR, block_size=min(0.4, max(0.05, L/SR*0.9)))
    xx = x if x.shape[1] > 1 else x[:, 0]
    try: lu = meter.integrated_loudness(xx)
    except Exception: lu = pyln.Meter(SR, block_size=0.02).integrated_loudness(xx)
    if not np.isfinite(lu): lu = -40
    peak = tp(x); gl = -14-lu; gp = -1-peak
    g = gl if gl <= gp else min(gl, gp+(12 if o.get('cap') else 9))
    fname = slug(name); os.makedirs(f'{OUT}/{cat}', exist_ok=True)
    wav = f'{OUT}/{cat}/{fname}.wav'; mp3 = f'{OUT}/{cat}/{fname}.mp3'
    tmp = f'/tmp/pn_{fname}.wav'; adj = 0
    for it in range(5):
        y = x*10**(g/20); lim = g > gp
        sf.write(tmp, y.astype('float32'), SR, subtype='FLOAT')
        af = ('alimiter=limit=0.84:attack=1:release=60:level=disabled,' if lim else '') + f'volume={adj}dB'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp, '-af', af, '-c:a', 'pcm_s24le', wav], check=True)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', wav, '-c:a', 'libmp3lame', '-b:a', '320k', '-id3v2_version', '3', '-metadata', f'title={name}', '-metadata', 'comment=CC0 public domain', mp3], check=True)
        ftp = max(tp(load(mp3)), tp(load(wav)))
        if ftp <= -1.0: break
        adj -= (ftp+1.0)+0.2
    os.remove(tmp)
    z = load(wav); m2 = pyln.Meter(SR, block_size=min(0.4, max(0.05, len(z)/SR*0.9))); zz = z if z.shape[1] > 1 else z[:, 0]
    try: fl = m2.integrated_loudness(zz)
    except Exception: fl = pyln.Meter(SR, block_size=0.02).integrated_loudness(np.concatenate([zz, zz]))
    m = dict(cat=cat, name=name, file=fname, src=p.replace(SRC, ''), dur=round(len(z)/SR, 2), lufs=float(round(fl, 1)), tp=float(round(ftp, 1)),
             ch=z.shape[1], lim=bool(lim), lufs_=0, mp3=os.path.getsize(mp3), wav=os.path.getsize(wav), k=k, srcpeak=float(round(20*np.log10(pk), 1)))
    json.dump(m, open(f'{MD}/{fname}.json', 'w'))
    return m

if __name__ == '__main__':
    from concurrent.futures import ProcessPoolExecutor
    a, b = int(sys.argv[1]), int(sys.argv[2])
    ks = [k for k in range(a, min(b, len(C))) if not os.path.exists(f'{MD}/{slug(C[k][1])}.json')]
    with ProcessPoolExecutor(2) as ex:
        for m in ex.map(proc, ks):
            print(f"{m.get('cat','')[:10]:10} {m['name'][:28]:28} {m.get('dur',0):5.2f}s LUFS {m.get('lufs',0):6.1f} TP {m.get('tp',0):5.1f} {m.get('err','')}", flush=True)
