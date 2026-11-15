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
