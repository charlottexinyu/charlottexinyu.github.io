(() => {
  'use strict';
  const form = document.querySelector('#filters');
  if (form) {
    const rows = [...document.querySelectorAll('.paper-row')];
    const controls = [...form.querySelectorAll('[name]')];
    const query = new URLSearchParams(location.search);
    controls.forEach(control => { control.value = query.get(control.name) || ''; });
    const render = persist => {
      const selected = controls.filter(control => control.value.trim());
      let count = 0;
      for (const row of rows) {
        const match = selected.every(({name, value}) => name === 'q'
          ? (row.dataset.title + ' ' + row.dataset.author).includes(value.trim().toLowerCase())
          : row.dataset[name] === value);
        row.hidden = !match;
        if (match) count++;
      }
      document.querySelector('#matches').textContent = '当前筛选 ' + count + ' 篇 · 共 ' + rows.length + ' 篇已收录论文';
      document.querySelector('#noMatches').hidden = count > 0;
      if (persist) {
        const params = new URLSearchParams(selected.map(c => [c.name, c.value]));
        const url = new URL(location.href);
        url.search = params.toString();
        try { history.replaceState(null, '', url); } catch { /* File previews may restrict history changes. */ }
      }
    };
    form.addEventListener('input', () => render(true));
    form.addEventListener('submit', event => { event.preventDefault(); render(true); });
    form.addEventListener('reset', () => setTimeout(() => render(true), 0));
    render(false);
  }
  // Keep shared links from the previous prototype usable.
  if (!document.querySelector('.year-chart')) return;
  const hash = location.hash.slice(1);
  if (hash.startsWith('paper/')) {
    const id = hash.slice(6).split('?')[0];
    if (/^[a-z0-9-]+$/.test(id)) location.replace('papers/' + id + '.html');
  } else if (/^library(?:\?|$)/.test(hash)) {
    const params = new URLSearchParams(hash.split('?')[1] || '');
    const category = {FIN:'finance', ACC:'accounting', MKT:'marketing', IS:'information-systems',
      'MGT/STRAT/ENT':'management', 'OM/SC':'operations', 'ECON/POLICY':'economics', CS_ECON:'cs-econ'}[params.get('domain')];
    if (category) params.set('category', category);
    params.delete('domain');
    location.replace('papers/index.html?' + params.toString());
  } else if (hash === 'methods' || hash === 'journals') {
    location.replace('about.html' + (hash === 'journals' ? '#journals' : ''));
  } else if (hash === 'domains') {
    location.replace('fields/index.html');
  }
})();
