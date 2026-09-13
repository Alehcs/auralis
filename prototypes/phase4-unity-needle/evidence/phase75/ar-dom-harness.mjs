// Temporary DEV-only QA button; exercises the real shared overlay without
// requesting/faking an XR session or placement. Removed after evidence capture.
const showAr=document.createElement('button');showAr.textContent='Ver controles AR · prueba DOM';
showAr.onclick=()=>{const panel=document.querySelector('.phase5-ar');panel.style.display='block';panel.style.visibility='visible';panel.style.position='relative';panel.style.maxHeight='none';panel.style.overflow='visible';document.querySelector('.view-controls').after(panel);};
document.querySelector('.view-controls').append(showAr);
