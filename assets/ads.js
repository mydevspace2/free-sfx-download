/* Ad loader - do not edit. Paste ad codes in ads/ads-config.js instead.
   Each slot's code is rendered inside its own sandbox-free iframe (srcdoc) so several
   Adsterra banners (which all use a global "atOptions") can live on one page.
   "global" code (Popunder / Social Bar) is injected straight into the page body. */
(function(){
  var cfg=window.SFX_ADS||{};if(cfg.enabled===false)return;
  function inject(html,target){
    var tmp=document.createElement('div');tmp.innerHTML=html;
    [].slice.call(tmp.childNodes).forEach(function(n){
      if(n.nodeName==='SCRIPT'){var s=document.createElement('script');[].slice.call(n.attributes).forEach(function(a){s.setAttribute(a.name,a.value)});s.text=n.text;target.appendChild(s);}
      else target.appendChild(n);
    });
  }
  var slots=cfg.slots||{};
  [].slice.call(document.querySelectorAll('.ad-slot[data-ad-slot]')).forEach(function(el){
    var name=el.getAttribute('data-ad-slot'),s=slots[name];if(!s)return;
    var mobile=window.matchMedia('(max-width: 760px)').matches;
    var v=(mobile&&s.mobile)?s.mobile:s;
    if(!v.code||!v.code.trim())return;
    var f=document.createElement('iframe');
    f.width=v.width||300;f.height=v.height||250;f.setAttribute('scrolling','no');f.setAttribute('title','Advertisement');f.loading='lazy';
    f.srcdoc='<!doctype html><html><head><base target="_blank"><style>html,body{margin:0;padding:0;overflow:hidden;background:transparent}</style></head><body>'+v.code+'</body></html>';
    el.appendChild(f);el.classList.add('filled');
  });
  if(cfg.global&&cfg.global.trim())inject(cfg.global,document.body);
})();
