(function(){
  // preview player: one sound at a time
  var a=new Audio(),cur=null;a.preload='none';
  function bar(c){return c&&c.querySelector('.prog span');}
  function stop(){if(cur){cur.classList.remove('playing');var s=bar(cur);if(s)s.style.width='0';var b=cur.querySelector('.play');if(b)b.setAttribute('aria-pressed','false');}cur=null;a.pause();}
  document.addEventListener('click',function(e){
    var b=e.target.closest&&e.target.closest('.play');if(!b)return;
    var c=b.closest('.card');if(cur===c){stop();return;}
    stop();cur=c;c.classList.add('playing');b.setAttribute('aria-pressed','true');a.src=b.dataset.src;
    var pr=a.play();if(pr&&pr.catch)pr.catch(function(){if(cur===c)stop();});
  });
  a.addEventListener('timeupdate',function(){var s=bar(cur);if(s&&a.duration)s.style.width=(a.currentTime/a.duration*100)+'%';});
  a.addEventListener('ended',stop);
})();
(function(){
  var r=document.documentElement;
  // dark mode toggle
  var t=document.querySelector('[data-theme-toggle]');
  if(t)t.addEventListener('click',function(){
    var cur=r.dataset.theme||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'),n=cur==='dark'?'light':'dark';
    r.dataset.theme=n;try{localStorage.setItem('theme',n)}catch(e){}
  });
  // categories / mobile menu
  var m=document.querySelector('[data-menu]'),p=document.getElementById('navpanel');
  function setMenu(o){if(!m||!p)return;p.classList.toggle('open',o);m.setAttribute('aria-expanded',o?'true':'false');}
  if(m&&p){
    m.addEventListener('click',function(e){e.stopPropagation();setMenu(!p.classList.contains('open'));});
    document.addEventListener('click',function(e){if(p.classList.contains('open')&&!p.contains(e.target))setMenu(false);});
    document.addEventListener('keydown',function(e){if(e.key==='Escape'&&p.classList.contains('open')){setMenu(false);m.focus();}});
  }
  // search (home page only): the page shows popular picks; the full index loads on first use
  var q=document.getElementById('q');if(!q)return;
  var pop=document.getElementById('pop'),res=document.getElementById('results'),cnt=document.getElementById('count'),
      empty=document.querySelector('.empty'),moreP=document.querySelector('.more-res'),more=document.getElementById('more'),
      head=document.getElementById('sounds-h'),ad=document.querySelector('main .ad-slot[data-ad-slot=incontent]'),
      idx=null,loading=null,hits=[],lim=48,base0=cnt?cnt.textContent:'';
  function load(){if(idx)return Promise.resolve(idx);if(!loading)loading=fetch('search-index.json').then(function(r){return r.json();}).then(function(j){idx=j;return j;});return loading;}
  function esc(t){return String(t).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
  function kb(n){return n<1048576?Math.round(n/1024)+' KB':(n/1048576).toFixed(1)+' MB';}
  function dur(d){return d<10?d.toFixed(1)+' s':Math.round(d)+' s';}
  function card(x){var n=x[0],f=x[1],c=x[2],b='sounds/'+c+'/'+f;
    return '<article class="card" data-cat="'+c+'"><button class="play" type="button" data-src="'+b+'.mp3" aria-label="Play preview of '+esc(n)+'" title="Play preview"></button>'+
      '<div class="ct"><h3><a href="sound/'+f+'/">'+esc(n)+'</a></h3><p class="meta"><span class="tag">'+esc(idx.cats[c])+'</span>'+dur(x[3])+' &middot; '+kb(x[4])+'</p></div>'+
      '<div class="prog" aria-hidden="true"><span></span></div><div class="actions"><a class="btn dl" href="'+b+'.mp3" download="'+f+'.mp3">Download MP3</a>'+
      '<a class="btn ghost" href="'+b+'.wav" download="'+f+'.wav" title="WAV 48 kHz 24-bit, '+kb(x[5])+'">WAV</a></div></article>';}
  function score(x,w){var n=x[0].toLowerCase(),c=(idx.cats[x[2]]||'').toLowerCase(),d=x[6]||'',s=0;
    for(var i=0;i<w.length;i++){var t=w[i];
      if(n.indexOf(t)>-1)s+=(new RegExp('\\b'+t.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')).test(n)?10:6);
      else if(c.indexOf(t)>-1)s+=4;else if(d.indexOf(t)>-1)s+=2;else return 0;}
    return s;}
  function paint(){res.innerHTML='<div class="grid">'+hits.slice(0,lim).map(card).join('')+'</div>';
    moreP.hidden=hits.length<=lim;cnt.textContent=hits.length+(hits.length===1?' sound found':' sounds found');empty.hidden=hits.length>0;}
  function run(){var t=q.value.trim().toLowerCase();
    if(t.length<2){res.hidden=true;res.innerHTML='';pop.hidden=false;moreP.hidden=true;empty.hidden=true;cnt.textContent=base0;head.textContent='Popular sound effects';if(ad)ad.style.display='';return;}
    load().then(function(){var w=t.split(/\s+/).filter(Boolean);
      hits=idx.s.map(function(x){return [score(x,w),x];}).filter(function(p){return p[0]>0;}).sort(function(a,b){return b[0]-a[0];}).map(function(p){return p[1];});
      lim=48;pop.hidden=true;res.hidden=false;head.textContent='Search results';if(ad)ad.style.display='none';paint();});}
  var tm;q.addEventListener('input',function(){clearTimeout(tm);tm=setTimeout(run,120);});
  q.addEventListener('focus',load,{once:true});
  if(more)more.addEventListener('click',function(){lim+=48;paint();});
  function go(){var s=document.getElementById('sounds');if(s)s.scrollIntoView();}
  var f=q.form;if(f)f.addEventListener('submit',function(e){e.preventDefault();run();go();
    try{var u=new URL(location.href);if(q.value.trim())u.searchParams.set('q',q.value.trim());else u.searchParams.delete('q');u.hash='sounds';history.replaceState(null,'',u);}catch(x){}});
  [].slice.call(document.querySelectorAll('.quick a[data-q]')).forEach(function(l){l.addEventListener('click',function(e){e.preventDefault();q.value=l.dataset.q;run();go();});});
  var v=new URLSearchParams(location.search).get('q');if(v){q.value=v;run();}
})();
