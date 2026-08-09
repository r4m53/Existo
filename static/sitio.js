const buscar=document.querySelector('#buscar');
const tipo=document.querySelector('#tipo');
const orden=document.querySelector('#orden');
const tarjetas=[...document.querySelectorAll('.tarjeta')];
const archivo=document.querySelector('#archivo');
let tema='';
function reordenar(){
  const lista=[...tarjetas];
  if((orden?.value||'azar')==='cronologico') lista.sort((a,b)=>a.dataset.fecha.localeCompare(b.dataset.fecha));
  else for(let i=lista.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[lista[i],lista[j]]=[lista[j],lista[i]];}
  lista.forEach(x=>archivo?.appendChild(x));
}
function filtrar(){
  const q=(buscar?.value||'').trim().toLowerCase(); const t=tipo?.value||''; let visibles=0;
  tarjetas.forEach(x=>{const ok=(!q||x.dataset.busca.includes(q))&&(!t||x.dataset.tipo===t)&&(!tema||x.dataset.tema===tema); x.hidden=!ok; if(ok) visibles++;});
  const r=document.querySelector('#resultado'); if(r) r.textContent=`${visibles} escrito${visibles===1?'':'s'}`;
}
buscar?.addEventListener('input',filtrar); tipo?.addEventListener('change',filtrar);
orden?.addEventListener('change',()=>{reordenar();filtrar();});
document.querySelectorAll('[data-filtro="tema"]').forEach(b=>b.addEventListener('click',()=>{tema=b.dataset.valor;document.querySelectorAll('[data-filtro="tema"]').forEach(x=>x.classList.toggle('activo',x===b));filtrar();}));
reordenar();filtrar();
