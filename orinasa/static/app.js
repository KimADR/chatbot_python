const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const api = async (url, opts={}) => {
  const res = await fetch(url, {headers:{'Content-Type':'application/json', ...(opts.headers||{})}, ...opts});
  let data;
  const type = res.headers.get('content-type') || '';
  data = type.includes('application/json') ? await res.json() : await res.text();
  if (!res.ok) throw new Error(data?.detail || data || `Erreur ${res.status}`);
  return data;
};
const fmtAr = (n) => new Intl.NumberFormat('fr-FR',{maximumFractionDigits:2}).format(n || 0);
const labels = {dashboard:"Vue d'ensemble",assistant:"Assistant",incidents:"Incidents",handover:"Relève",knowledge:"Fiches atelier",calculations:"Calculs"};

function showView(id){
  $$('.view').forEach(v=>v.classList.remove('active-view'));
  $$('.nav-item').forEach(v=>v.classList.toggle('active',v.dataset.view===id));
  $('#'+id).classList.add('active-view');
  $('#breadcrumb').textContent = labels[id] || id;
  window.scrollTo({top:0,behavior:'smooth'});
  if(id==='incidents') loadIncidents();
  if(id==='handover') loadHandover();
  if(id==='knowledge') loadKnowledge();
}
$$('.nav-item').forEach(b=>b.addEventListener('click',()=>showView(b.dataset.view)));
$$('[data-jump]').forEach(b=>b.addEventListener('click',()=>showView(b.dataset.jump)));

function statusLabel(s){return {ouvert:'Ouvert',en_cours:'En cours',resolu:'Résolu',annule:'Annulé'}[s] || s}
function priorityIcon(p){return p==='critique'?'ϟ':p==='haute'?'⚠':'✓'}

async function loadDashboard(){
  const [summary,incidents] = await Promise.all([api('/api/summary'),api('/api/incidents?limit=5')]);
  $('#kpiOpen').textContent=summary.open_incidents;
  $('#kpiCritical').textContent=summary.critical_open;
  $('#kpiHours').textContent=fmtAr(summary.downtime_minutes/60);
  $('#kpiCost').textContent=fmtAr(summary.estimated_cost);
  $('#navIncidentCount').textContent=summary.open_incidents;
  $('#knowledgeCount').textContent=summary.knowledge_count;
  $('#equipmentCount').textContent=summary.equipment_count;
  $('#declCount').textContent=`${incidents.length} déclarations`;
  $('#downtimeNote').textContent=`${fmtAr(summary.downtime_minutes/60)} h d'arrêt saisi`;
  $('#recentIncidents').innerHTML=incidents.map(i=>`<div class="incident-row"><span class="incident-icon ${i.priority==='critique'?'critical':''}">${priorityIcon(i.priority)}</span><div><b>${esc(i.title)}</b><small>${esc(i.code)} · ${esc(i.equipment_name||'Sans équipement')}</small></div><span class="badge ${i.status}">${statusLabel(i.status)}</span><span class="chev">›</span></div>`).join('');
  drawCategories(summary.categories);
  drawWeek(incidents.length);
}
function drawWeek(total){
  const days=['mar','mer','jeu','ven','sam','dim','lun'];
  const vals=[1,1,1,1,1,1,Math.max(1,total-3)];
  const max=Math.max(...vals,1);
  $('#weekChart').innerHTML=days.map((d,idx)=>`<div class="week-bar"><span>${vals[idx]}</span><i style="height:${30+70*vals[idx]/max}px"></i><b>${d}</b></div>`).join('');
}
function drawCategories(items){
  const max=Math.max(...items.map(x=>x.count),1);
  $('#categoryChart').innerHTML=items.map(x=>`<div class="cat-row"><span>${esc(x.category)}</span><span class="cat-track"><i style="width:${100*x.count/max}%"></i></span><b>${x.count}</b></div>`).join('') || '<p>Aucune donnée.</p>';
}

async function loadEquipment(){
  const items=await api('/api/equipment');
  $('#equipmentSelect').innerHTML='<option value="">Sans équipement</option>'+items.map(e=>`<option value="${e.id}">${esc(e.code)} · ${esc(e.name)}</option>`).join('');
}
async function loadIncidents(){
  const items=await api('/api/incidents');
  $('#allIncidents').innerHTML=`<div class="incident-table-row head"><span>Code</span><span>Incident</span><span>Catégorie</span><span>Priorité</span><span>Statut</span></div>`+items.map(i=>`<div class="incident-table-row"><b>${esc(i.code)}</b><span><b>${esc(i.title)}</b><small>${esc(i.equipment_name||'Sans équipement')} · ${fmtAr(i.downtime_minutes)} min</small></span><span>${esc(i.category)}</span><span>${esc(i.priority)}</span><select data-incident="${i.id}"><option value="ouvert" ${i.status==='ouvert'?'selected':''}>Ouvert</option><option value="en_cours" ${i.status==='en_cours'?'selected':''}>En cours</option><option value="resolu" ${i.status==='resolu'?'selected':''}>Résolu</option><option value="annule" ${i.status==='annule'?'selected':''}>Annulé</option></select></div>`).join('');
  $$('select[data-incident]').forEach(s=>s.addEventListener('change',async()=>{try{await api(`/api/incidents/${s.dataset.incident}`,{method:'PATCH',body:JSON.stringify({status:s.value})});await loadDashboard();}catch(e){alert(e.message)}}));
}
async function loadHandover(){
  const incidentsNode=$('#handoverIncidents');
  incidentsNode.textContent='Préparation de la fiche…';
  try{
    const report=await api('/api/shift-handover');
    const generated=new Date(report.generated_at);
    $('#handoverGenerated').textContent=`Générée le ${generated.toLocaleDateString('fr-FR',{weekday:'long',day:'2-digit',month:'long',year:'numeric'})} à ${generated.toLocaleTimeString('fr-FR',{hour:'2-digit',minute:'2-digit'})}`;
    $('#handoverSummary').innerHTML=`<div><strong>${report.open_count}</strong><span>incident${report.open_count===1?'':'s'} à reprendre</span></div><div><strong>${report.critical_count}</strong><span>priorité critique</span></div>`;
    incidentsNode.innerHTML=report.incidents.length?report.incidents.map(i=>`<article class="handover-item priority-${esc(i.priority)}"><div class="handover-item-head"><div><span class="handover-code">${esc(i.code)}</span><h3>${esc(i.title)}</h3></div><span class="badge ${esc(i.status)}">${statusLabel(i.status)}</span></div><div class="handover-meta"><span>${esc(i.equipment_name||'Équipement non identifié')}</span><span>${esc(i.category)}</span><span>${esc(i.priority)}</span><span>${fmtAr(i.downtime_minutes)} min d'arrêt</span></div><p class="handover-description">${esc(i.description||'Aucun fait observé consigné.')}</p>${i.latest_update?`<p class="handover-update"><b>Dernière mise à jour :</b> ${esc(i.latest_update)} · ${formatDate(i.latest_update_at)}</p>`:''}${i.missing_information.length?`<p class="handover-missing"><b>À compléter :</b> ${i.missing_information.map(esc).join(' · ')}</p>`:''}</article>`).join(''):'<div class="handover-empty"><strong>La relève est à jour.</strong><p>Aucun incident ouvert ou en cours à transmettre.</p></div>';
  }catch(error){
    incidentsNode.textContent=`Impossible de préparer la fiche : ${error.message}`;
  }
}
$('#refreshHandover').addEventListener('click',loadHandover);
$('#printHandover').addEventListener('click',()=>window.print());
function formatDate(value){
  if(!value)return 'Date inconnue';
  const date=new Date(value);
  return Number.isNaN(date.getTime())?'Date inconnue':date.toLocaleString('fr-FR',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'});
}
$('#incidentForm').addEventListener('submit',async(e)=>{
  e.preventDefault(); const f=new FormData(e.target);
  const payload=Object.fromEntries(f.entries());
  payload.equipment_id=payload.equipment_id?Number(payload.equipment_id):null;
  payload.downtime_minutes=Number(payload.downtime_minutes||0);
  try{await api('/api/incidents',{method:'POST',body:JSON.stringify(payload)});$('#incidentFormMsg').textContent='Incident enregistré.';e.target.reset();await loadIncidents();await loadDashboard();}
  catch(err){$('#incidentFormMsg').textContent=err.message;$('#incidentFormMsg').style.color='#b6503b';}
});

async function loadKnowledge(){
  const items=await api('/api/knowledge');
  $('#knowledgeGrid').innerHTML=items.map(c=>`<article class="knowledge-card"><span class="code">${esc(c.id)} · ${esc(c.category)}</span><h3>${esc(c.title)}</h3><p>${esc(c.content)}</p><div class="safety">${esc(c.safety)}</div></article>`).join('');
}
$('#askButton').addEventListener('click',async()=>{
  const q=$('#assistantQuery').value.trim(); if(!q)return;
  try{const r=await api('/api/assistant?q='+encodeURIComponent(q));$('#assistantAnswer').className='answer-box';$('#assistantAnswer').innerHTML=`<div>${esc(r.answer)}</div>${r.references.length?`<div class="refs"><b>Références :</b> ${r.references.map(x=>`${esc(x.id)} — ${esc(x.title)}`).join(' · ')}</div>`:''}`;}catch(e){$('#assistantAnswer').textContent=e.message;}
});

$('#costButton').addEventListener('click',async()=>{try{const r=await api('/api/calculate/downtime',{method:'POST',body:JSON.stringify({minutes:Number($('#costMinutes').value),hourly_rate:Number($('#costRate').value)})});$('#costResult').textContent=`${fmtAr(r.result)} Ar`;}catch(e){$('#costResult').textContent=e.message}});
$('#trsButton').addEventListener('click',async()=>{try{const r=await api('/api/calculate/trs',{method:'POST',body:JSON.stringify({availability:Number($('#trsA').value),performance:Number($('#trsP').value),quality:Number($('#trsQ').value)})});$('#trsResult').textContent=`${fmtAr(r.result)} %`;}catch(e){$('#trsResult').textContent=e.message}});
$('#unitButton').addEventListener('click',async()=>{try{const r=await api('/api/calculate/unit',{method:'POST',body:JSON.stringify({value:Number($('#unitValue').value),from_unit:$('#unitFrom').value,to_unit:$('#unitTo').value})});$('#unitResult').textContent=`${fmtAr(r.result)} ${r.unit}`;}catch(e){$('#unitResult').textContent=e.message}});
$('#arithButton').addEventListener('click',async()=>{try{const r=await api('/api/calculate/arithmetic',{method:'POST',body:JSON.stringify({expression:$('#arithExpr').value})});$('#arithResult').textContent=fmtAr(r.result);}catch(e){$('#arithResult').textContent=e.message}});

function esc(v){return String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}
const date=new Date();
$('#todayLabel').textContent=date.toLocaleDateString('fr-FR',{weekday:'short',day:'2-digit',month:'long',year:'numeric'});
Promise.all([loadEquipment(),loadDashboard()]).catch(e=>console.error(e));
