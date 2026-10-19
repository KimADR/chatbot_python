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
  $('#knowledgeGrid').innerHTML=items.map(c=>`<article id="${esc(c.id)}" class="knowledge-card"><span class="code">${esc(c.id)} · ${esc(c.category)}</span><h3>${esc(c.title)}</h3><p>${esc(c.content)}</p><div class="safety">${esc(c.safety)}</div></article>`).join('');
  return items;
}

const chatStorageKey='orinasa.chat.v1';
let conversation=readConversation();
let chatSending=false;

function readConversation(){
  try{
    const saved=JSON.parse(sessionStorage.getItem(chatStorageKey)||'[]');
    if(!Array.isArray(saved))return [];
    return saved.filter(message=>message&&['user','assistant'].includes(message.role)&&typeof message.content==='string'&&message.content.length<=2000).slice(-40).map(message=>({
      role:message.role,
      content:message.content,
      references:Array.isArray(message.references)?message.references.filter(reference=>reference&&typeof reference.id==='string'&&typeof reference.title==='string').slice(0,5):[],
    }));
  }catch(error){
    console.warn('Historique de conversation indisponible.',error);
    return [];
  }
}
function saveConversation(){
  try{sessionStorage.setItem(chatStorageKey,JSON.stringify(conversation.slice(-40)));}
  catch(error){console.warn('Impossible de conserver la conversation dans cet onglet.',error);}
}
function scrollChatToLatest(){const node=$('#chatMessages');node.scrollTop=node.scrollHeight;}
function addChatMessage(message){
  const bubble=document.createElement('article');
  bubble.className=`chat-message ${message.role}`;
  const label=document.createElement('span');
  label.className='chat-message-label';
  label.textContent=message.role==='user'?'VOUS':'ASSISTANT ORINASA';
  const text=document.createElement('p');
  text.textContent=message.content;
  bubble.append(label,text);

  if(message.role==='assistant'&&message.references?.length){
    const references=document.createElement('div');
    references.className='chat-references';
    const title=document.createElement('span');
    title.className='chat-references-label';
    title.textContent='Fiches consultées — sélectionnez une source pour la lire';
    references.append(title);
    message.references.forEach(reference=>{
      const button=document.createElement('button');
      button.type='button';
      button.className='chat-reference';
      button.dataset.knowledgeRef=reference.id;
      button.textContent=`${reference.id} · ${reference.title}`;
      references.append(button);
    });
    bubble.append(references);
  }
  $('#chatMessages').append(bubble);
  scrollChatToLatest();
  return bubble;
}
function renderConversation(){
  const node=$('#chatMessages');
  node.replaceChildren();
  if(!conversation.length){
    const welcome=document.createElement('div');
    welcome.className='chat-welcome';
    welcome.innerHTML='<span class="chat-welcome-mark" aria-hidden="true">◌</span><h3>Comment puis-je vous aider ?</h3><p>Décrivez un incident, un équipement ou une consigne à transmettre. Je chercherai dans les fiches atelier disponibles.</p>';
    node.append(welcome);
    return;
  }
  conversation.forEach(addChatMessage);
}
async function loadChatStatus(){
  const status=await api('/api/ai/status');
  const notice=$('#chatPrivacyNotice');
  notice.textContent=status.notice;
  notice.dataset.mode=status.external?'external':'local';
}
function setChatBusy(busy){
  chatSending=busy;
  $('#chatInput').disabled=busy;
  $('#chatSendButton').disabled=busy;
  $('#newChatButton').disabled=busy;
  $$('[data-chat-prompt]').forEach(button=>button.disabled=busy);
  $('#chatSendButton').querySelector('span:first-child').textContent=busy?'Réponse…':'Envoyer';
}
function addTypingIndicator(){
  const bubble=document.createElement('article');
  bubble.className='chat-message assistant chat-loading';
  bubble.setAttribute('role','status');
  bubble.innerHTML='<span class="chat-message-label">ASSISTANT ORINASA</span><span class="chat-typing">Recherche en cours <span class="chat-typing-dots" aria-hidden="true"><i></i><i></i><i></i></span></span>';
  $('#chatMessages').append(bubble);
  scrollChatToLatest();
  return bubble;
}
function requestMessagesWith(userMessage){
  const candidate=[...conversation,{role:'user',content:userMessage}];
  const selected=[];
  let characters=0;
  for(const message of candidate.slice(-20).reverse()){
    if(characters+message.content.length>5500)break;
    selected.push({role:message.role,content:message.content});
    characters+=message.content.length;
  }
  return selected.reverse();
}
async function sendChatMessage(message){
  if(chatSending||!message.trim())return;
  const content=message.trim();
  $('#chatError').hidden=true;
  $('#chatError').textContent='';
  const welcome=$('.chat-welcome');
  if(welcome)welcome.remove();
  const pendingUser=addChatMessage({role:'user',content});
  const loading=addTypingIndicator();
  setChatBusy(true);
  try{
    const result=await api('/api/ai/chat',{
      method:'POST',
      body:JSON.stringify({messages:requestMessagesWith(content)}),
    });
    loading.remove();
    conversation.push({role:'user',content});
    conversation.push({
      role:'assistant',
      content:result.answer,
      references:result.references||[],
    });
    conversation=conversation.slice(-40);
    saveConversation();
    addChatMessage(conversation[conversation.length-1]);
    $('#chatInput').value='';
    const privacy=$('#chatPrivacyNotice');
    privacy.textContent=result.notice||`Réponse fournie par ${result.provider}. Les questions de cette conversation sont envoyées au fournisseur configuré.`;
    privacy.dataset.mode=result.fallback?'fallback':result.provider==='local'?'local':'external';
  }catch(error){
    pendingUser.remove();
    loading.remove();
    $('#chatError').textContent=error.message;
    $('#chatError').hidden=false;
    renderConversation();
  }finally{
    setChatBusy(false);
    $('#chatInput').focus();
  }
}
$('#chatForm').addEventListener('submit',event=>{
  event.preventDefault();
  sendChatMessage($('#chatInput').value);
});
$('#chatInput').addEventListener('keydown',event=>{
  if(event.key==='Enter'&&event.ctrlKey){
    event.preventDefault();
    $('#chatForm').requestSubmit();
  }
});
$$('[data-chat-prompt]').forEach(button=>button.addEventListener('click',()=>sendChatMessage(button.dataset.chatPrompt)));
$('#newChatButton').addEventListener('click',()=>{
  conversation=[];
  saveConversation();
  $('#chatError').hidden=true;
  $('#chatError').textContent='';
  $('#chatPrivacyNotice').dataset.mode='';
  loadChatStatus().catch(error=>console.error(error));
  renderConversation();
  $('#chatInput').focus();
});
$('#chatMessages').addEventListener('click',async event=>{
  const button=event.target.closest('[data-knowledge-ref]');
  if(!button)return;
  try{
    await loadKnowledge();
    showView('knowledge');
    document.getElementById(button.dataset.knowledgeRef)?.scrollIntoView({behavior:'smooth',block:'center'});
  }catch(error){
    $('#chatError').textContent=`Impossible d'ouvrir cette fiche : ${error.message}`;
    $('#chatError').hidden=false;
  }
});
renderConversation();
loadChatStatus().catch(error=>{
  $('#chatPrivacyNotice').textContent=`Impossible de vérifier le mode IA : ${error.message}`;
  $('#chatPrivacyNotice').dataset.mode='fallback';
});

$('#costButton').addEventListener('click',async()=>{try{const r=await api('/api/calculate/downtime',{method:'POST',body:JSON.stringify({minutes:Number($('#costMinutes').value),hourly_rate:Number($('#costRate').value)})});$('#costResult').textContent=`${fmtAr(r.result)} Ar`;}catch(e){$('#costResult').textContent=e.message}});
$('#trsButton').addEventListener('click',async()=>{try{const r=await api('/api/calculate/trs',{method:'POST',body:JSON.stringify({availability:Number($('#trsA').value),performance:Number($('#trsP').value),quality:Number($('#trsQ').value)})});$('#trsResult').textContent=`${fmtAr(r.result)} %`;}catch(e){$('#trsResult').textContent=e.message}});
$('#unitButton').addEventListener('click',async()=>{try{const r=await api('/api/calculate/unit',{method:'POST',body:JSON.stringify({value:Number($('#unitValue').value),from_unit:$('#unitFrom').value,to_unit:$('#unitTo').value})});$('#unitResult').textContent=`${fmtAr(r.result)} ${r.unit}`;}catch(e){$('#unitResult').textContent=e.message}});
$('#arithButton').addEventListener('click',async()=>{try{const r=await api('/api/calculate/arithmetic',{method:'POST',body:JSON.stringify({expression:$('#arithExpr').value})});$('#arithResult').textContent=fmtAr(r.result);}catch(e){$('#arithResult').textContent=e.message}});

function esc(v){return String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}
const date=new Date();
$('#todayLabel').textContent=date.toLocaleDateString('fr-FR',{weekday:'short',day:'2-digit',month:'long',year:'numeric'});
Promise.all([loadEquipment(),loadDashboard()]).catch(e=>console.error(e));
