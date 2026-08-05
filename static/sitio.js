const buscar=document.querySelector('#buscar');
const tipo=document.querySelector('#tipo');
const tarjetas=[...document.querySelectorAll('.tarjeta')];
let tema='';
function filtrar(){
  const q=(buscar?.value||'').trim().toLowerCase(); const t=tipo?.value||''; let visibles=0;
  tarjetas.forEach(x=>{const ok=(!q||x.dataset.busca.includes(q))&&(!t||x.dataset.tipo===t)&&(!tema||x.dataset.tema===tema); x.hidden=!ok; if(ok) visibles++;});
  const r=document.querySelector('#resultado'); if(r) r.textContent=`${visibles} escrito${visibles===1?'':'s'}`;
}
buscar?.addEventListener('input',filtrar); tipo?.addEventListener('change',filtrar);
document.querySelectorAll('[data-filtro="tema"]').forEach(b=>b.addEventListener('click',()=>{tema=b.dataset.valor;document.querySelectorAll('[data-filtro="tema"]').forEach(x=>x.classList.toggle('activo',x===b));filtrar();}));
filtrar();
