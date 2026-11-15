(function(){
  // preview player: one sound at a time
  var a=new Audio(),cur=null;a.preload='none';
  function stop(){if(cur){cur.classList.remove('playing');var s=cur.querySelector('.prog span');if(s)s.style.width='0';}cur=null;a.pause();}
  document.addEventListener('click',function(e){
    var b=e.target.closest&&e.target.closest('.play');if(!b)return;
    var c=b.closest('.card');if(cur===c){stop();return;}
    stop();cur=c;c.classList.add('playing');a.src=b.dataset.src;a.currentTime=0;
    var pr=a.play();if(pr&&pr.catch)pr.catch(function(){stop();});
  });
  a.addEventListener('timeupdate',function(){if(cur&&a.duration){var s=cur.querySelector('.prog span');if(s)s.style.width=(a.currentTime/a.duration*100)+'%';}});
  a.addEventListener('ended',stop);
})();
(function(){
  // dark mode toggle
  var b=document.querySelector('[data-theme-toggle]');
  if(b)b.addEventListener('click',function(){
    var r=document.documentElement,cur=r.dataset.theme||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'),n=cur==='dark'?'light':'dark';
    r.dataset.theme=n;try{localStorage.setItem('theme',n)}catch(e){}
  });
  // search + category filter (home page only)
  var q=document.getElementById('q');if(!q)return;
  var cards=[].slice.call(document.querySelectorAll('.card')),chips=[].slice.call(document.querySelectorAll('.chip')),
      shown=document.getElementById('shown'),empty=document.querySelector('.empty'),cat='all';
  function run(){
    var t=q.value.trim().toLowerCase(),n=0;
    cards.forEach(function(c){var ok=(cat==='all'||c.dataset.cat===cat)&&(!t||(c.dataset.name+' '+c.dataset.cat.replace(/-/g,' ')).indexOf(t)>-1);c.hidden=!ok;if(ok)n++;});
    shown.textContent=n;if(empty)empty.hidden=n>0;
    var ad=document.querySelector('main .ad-slot[data-ad-slot=incontent]');if(ad)ad.style.display=(t||cat!=='all')?'none':'';
  }
  q.addEventListener('input',run);
  chips.forEach(function(ch){ch.addEventListener('click',function(){chips.forEach(function(x){x.classList.remove('active')});ch.classList.add('active');cat=ch.dataset.filter;run();});});
  var p=new URLSearchParams(location.search).get('q');if(p){q.value=p;run();}
})();
