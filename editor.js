const form = document.querySelector('#record-editor');
const current = form.elements;
const records = window.guideEditor.species;
const known = new Map(records.map(r => [r.slug,r]));
const rows = (items, sep) => (items || []).map(x => x.title + sep + (x.text || x.url)).join('\n');
const trialList=document.querySelector('#trial-list');
function addTrial(trial={}) {
  const group=document.createElement('fieldset');
  group.className='trial-editor';
  const legend=document.createElement('legend');
  legend.textContent='Breeding account';
  group.append(legend);
  for(const [key,labelText] of [['title','Account title'],['text','Account text']]) {
    const label=document.createElement('label');
    const field=document.createElement(key==='title'?'input':'textarea');
    label.textContent=labelText;
    field.dataset.field=key;
    field.value=key==='text' ? (trial.text || [trial.intro,...(trial.facts||[]).map(f=>f.title+' · '+f.text),...(trial.sections||[]).map(s=>s.title+' — '+s.text)].filter(Boolean).join('\n\n')) : (trial[key] || '');
    field.required=true;
    label.append(field);
    group.append(label);
  }
  group.original=trial;
  group.initialText=group.querySelector('textarea').value;
  const remove=document.createElement('button');
  remove.type='button';remove.textContent='Remove this account from draft';
  remove.addEventListener('click',()=>group.remove());group.append(remove);
  trialList.append(group);
}
document.querySelector('#new-trial').addEventListener('click',()=>addTrial());
function setRecord(record) {
  trialList.replaceChildren();
  for(const trial of record.trials || [])addTrial(trial);
  for (const key of ['name','common','intro','group']) current[key].value = record[key] || '';
  current.sections.value = (record.sections || []).map(s => s.title + '\n' + s.text).join('\n\n');
  current.facts.value = rows(record.facts,' | ');
  current.sources.value = rows(record.sources,' | ');
  current.taxonomy.value = rows(record.classification,' | ');
  current.pictures.value = (record.additional_photos || []).map(p=>p.file+' | '+p.alt).join('\n');
}
current.existing.addEventListener('change',()=>setRecord(known.get(current.existing.value) || {}));
function pairs(text, valueKey) {
  return text.trim().split('\n').filter(Boolean).map(line => {
    const split = line.indexOf('|');
    if(split <= 0 || !line.slice(split+1).trim())throw Error('Each fact and source needs a label, a | separator, and a value.');
    return {title:line.slice(0,split).trim(),[valueKey]:line.slice(split+1).trim()};
  });
}
form.addEventListener('submit',event=>{
  event.preventDefault();
  const feedback=document.querySelector('#editor-status');
  try{
    const prior=known.get(current.existing.value);
    const name=current.name.value.trim();
    const slug=prior?.slug || name.normalize('NFKD').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
    if(!slug || (!prior && (known.has(slug)||records.some(r=>r.name.toLowerCase()===name.toLowerCase()))))throw Error('That species already has a post. Select it in the existing-post menu.');
    const sections=current.sections.value.trim().split(/\n\s*\n/).map(part=>{
      const [title,...rest]=part.split('\n');if(!rest.join('').trim())throw Error('Each section needs a heading followed by its text on the next line.');
      return {title:title.trim(),text:rest.join('\n').trim()};
    });
    const sources=pairs(current.sources.value,'url');
    const classification=pairs(current.taxonomy.value,'url');
    if([...sources,...classification].some(s=>!/^https?:\/\//i.test(s.url)))throw Error('Use a complete https:// or http:// source link.');
    const additional_photos=pairs(current.pictures.value,'text').map(p=>{
      if(!/^[a-z0-9][a-z0-9_.-]*\.(jpe?g|png|webp|avif)$/i.test(p.title))throw Error('Use a photograph filename containing letters, digits, hyphens, underscores and a supported image extension.');
      return {file:p.title,alt:p.text,caption:p.text};
    });
    const trials=[...trialList.children].map(group=>{
      const title=group.querySelector('input').value.trim();
      const value=group.querySelector('textarea').value.trim();
      if(!title || !value)throw Error('Each additional account needs a title and its observations.');
      if(value===group.initialText)return {...group.original,title};
      return {title,text:value,...(group.original.url ? {url:group.original.url} : {})};
    });
    const record={...prior,slug,name,trials,classification,additional_photos,common:current.common.value.trim(),group:current.group.value,intro:current.intro.value.trim(),facts:pairs(current.facts.value,'text'),sections,sources};
    const blob=new Blob([JSON.stringify(record,null,2)+'\n'],{type:'application/json'});
    const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='post-'+slug+'.json';a.click();
    setTimeout(()=>URL.revokeObjectURL(url),10000);
    feedback.textContent='Saved '+a.download+'. Upload the post file and any new photographs to GitHub, then choose Commit changes to publish.';
  }catch(err){feedback.textContent=err.message;}
});
