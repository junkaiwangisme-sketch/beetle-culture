const form=document.getElementById('filterForm');
const query=document.getElementById('query');
const group=document.getElementById('group');
const list=document.getElementById('listing');
const rows=Array.from(list.querySelectorAll('a'));
const expand=document.getElementById('show-all');
const params=new URLSearchParams(location.search);
query.value=params.get('q') || '';
group.value=params.get('group') || '';
form.hidden=false;
let showAll=false;
function update(save) {
  const tokens=query.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
  const limited=Boolean(expand) && !showAll && !tokens.length && !group.value;
  let matches=0;
  for (const row of rows) {
    const match=(!group.value || row.dataset.group===group.value) && tokens.every(t=>row.dataset.terms.includes(t));
    if(match)matches++;
    row.hidden=!match || (limited && matches>Number(list.dataset.initialLimit));
  }
  document.getElementById('count').textContent=matches+(matches===1?' species guide':' species guides');
  document.getElementById('empty').hidden=matches>0;
  if(expand)expand.hidden=!limited || matches<=Number(list.dataset.initialLimit);
  if(save && location.protocol!=='file:') {
    const url=new URL(location.href);
    for(const [name,value] of [['q',query.value.trim()],['group',group.value]]){
      if(value)url.searchParams.set(name,value);else url.searchParams.delete(name);
    }
    history.replaceState(null,'',url);
  }
}
form.addEventListener('input',()=>update(true));
form.addEventListener('submit',event=>{event.preventDefault();update(true);});
if(expand)expand.addEventListener('click',()=>{showAll=true;update(false);});
document.getElementById('clear').addEventListener('click',()=>{query.value='';group.value='';update(true);query.focus();});
update(false);
if(location.hash==='#query')query.focus();
