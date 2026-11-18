const form = document.getElementById('filterForm');
const query = document.getElementById('query');
const group = document.getElementById('group');
const rows = Array.from(document.querySelectorAll('#listing a'));
const params = new URLSearchParams(location.search);
query.value = params.get('q') || '';
group.value = params.get('group') || '';
form.hidden = false;
function update(save) {
  const tokens = query.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
  let n = 0;
  for (const row of rows) {
    row.hidden = Boolean(group.value && row.dataset.group !== group.value) || !tokens.every(t => row.dataset.terms.includes(t));
    if (!row.hidden) n++;
  }
  document.getElementById('count').textContent = n + (n === 1 ? ' species guide' : ' species guides');
  document.getElementById('empty').hidden = n > 0;
  if (save && location.protocol !== 'file:') {
    const url = new URL(location.href);
    for (const [name,value] of [['q',query.value.trim()],['group',group.value]]) {
      if (value) url.searchParams.set(name,value); else url.searchParams.delete(name);
    }
    history.replaceState(null,'',url);
  }
}
form.addEventListener('input', () => update(true));
form.addEventListener('submit', event => { event.preventDefault(); update(true); });
document.getElementById('clear').addEventListener('click', () => { form.reset(); update(true); query.focus(); });
update(false);
if (location.hash === '#query') query.focus();
