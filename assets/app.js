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
  // search + category filter (home page only)
  var q=document.getElementById('q');if(!q)return;
  var cards=[].slice.call(document.querySelectorAll('#sounds .card')),chips=[].slice.call(document.querySelectorAll('.chip')),
      shown=document.getElementById('shown'),empty=document.querySelector('.empty'),cat='all';
  function run(){
    var t=q.value.trim().toLowerCase(),n=0;
    cards.forEach(function(c){var ok=(cat==='all'||c.dataset.cat===cat)&&(!t||(c.dataset.name+' '+c.dataset.cat.replace(/-/g,' ')).indexOf(t)>-1);c.hidden=!ok;if(ok)n++;});
    shown.textContent=n;if(empty)empty.hidden=n>0;
    var ad=document.querySelector('main .ad-slot[data-ad-slot=incontent]');if(ad)ad.style.display=(t||cat!=='all')?'none':'';
  }
  function go(){var s=document.getElementById('sounds');if(s)s.scrollIntoView();}
  q.addEventListener('input',run);
  var f=q.form;if(f)f.addEventListener('submit',function(e){e.preventDefault();run();go();
    try{var u=new URL(location.href);if(q.value.trim())u.searchParams.set('q',q.value.trim());else u.searchParams.delete('q');u.hash='sounds';history.replaceState(null,'',u);}catch(x){}});
  [].slice.call(document.querySelectorAll('.quick a[data-q]')).forEach(function(l){l.addEventListener('click',function(e){e.preventDefault();q.value=l.dataset.q;run();go();});});
  chips.forEach(function(ch){ch.addEventListener('click',function(){chips.forEach(function(x){x.classList.remove('active');x.setAttribute('aria-pressed','false')});ch.classList.add('active');ch.setAttribute('aria-pressed','true');cat=ch.dataset.filter;run();});});
  var v=new URLSearchParams(location.search).get('q');if(v){q.value=v;run();}
})();
