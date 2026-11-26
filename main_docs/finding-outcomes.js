(() => {
  const fields = ['THIRD_PARTY_NAME', 'THIRD_PARTY_NORMALISED_NAME'];
  const examples = [
    {
      label: 'Stronger match',
      rows: [
        [['Cisco UK', 'SUBSTRING'], ['Cisco UK', 'SUBSTRING']],
        [['Cisco UK', 'SUBSTRING'], ['Cisco Ltd.', 'EXACT']],
      ],
      winner: [1, 1],
      explanation: 'The later exact match wins.',
    },
    {
      label: 'Tied methods',
      rows: [
        [['Cisco Ltd.', 'EXACT'], ['CISCO', 'EXACT']],
        [['Cisco', 'EXACT'], ['Cisco Inc.', 'EXACT']],
      ],
      winner: [0, 0],
      explanation: 'First source row, then first configured field.',
    },
  ];

  const outcomes = [
    { name: 'Cisco', query: 'cisco', id: 'INC-01', engagement: 'E01', status: 'MATCHED',
      reason: 'Cisco Ltd. cleans to cisco.' },
    { name: 'Northstar', query: 'northstar', id: 'INC-02', engagement: '', status: 'NO_MATCH',
      reason: 'The query is usable. No engagement matches.' },
    { name: 'Limited', query: '', id: 'INC-03', engagement: '', status: 'INVALID_NAME',
      reason: 'Cleaning removes the only word.' },
    { name: 'Unknown', reason: 'Unknown is skipped before cleaning.' },
  ];

  function exampleButtons(items, label) {
    return `<div class="fo-options" role="group" aria-label="${label}">
      ${items.map((item, i) => `<button type="button" data-example="${i}" aria-pressed="${i === 0}">${item}</button>`).join('')}
    </div>`;
  }

  function watchExamples(root, render) {
    for (const button of root.querySelectorAll('[data-example]')) {
      button.addEventListener('click', () => {
        for (const option of root.querySelectorAll('[data-example]')) {
          option.setAttribute('aria-pressed', String(option === button));
        }
        render(Number(button.dataset.example));
      });
    }
    render(0);
  }

  function showDedup(root) {
    root.innerHTML = `
      <div class="fo-bar">
        ${exampleButtons(examples.map(item => item.label), 'Deduplication example')}
        <span class="fo-context">Query <b>Cisco</b> · Incident <b>INC-01</b></span>
      </div>
      <div class="fo-body"></div>`;
    const body = root.querySelector('.fo-body');
    watchExamples(root, index => {
      const example = examples[index];
      const [winningRow, winningField] = example.winner;
      body.innerHTML = `
        <table class="fo-table fo-rank-table" aria-label="Choose the source field Finding keeps">
          <thead><tr><th scope="col">Source row</th><th scope="col">ENGAGEMENT_ID</th>
            ${fields.map(field => `<th scope="col">${field}</th>`).join('')}</tr></thead>
          <tbody>${example.rows.map((row, r) => `<tr>
            <th scope="row">${r+1}</th><td class="fo-id">E01</td>
            ${row.map(([name, method], c) => `<td class="fo-choice-cell"><button type="button" class="fo-choice" data-row="${r}" data-col="${c}"
              aria-label="Choose row ${r+1}, ${fields[c]}, ${name}, ${method}"><b>${name}</b><span>${method}</span></button></td>`).join('')}</tr>`).join('')}</tbody>
        </table>
        <div class="fo-result" aria-live="polite"><span class="fo-result-label">Your pick</span><span>Which field is saved? Choose a cell.</span></div>
        <p class="fo-note">One row per incident and engagement. Priority: EXACT → SUBSTRING → FUZZY.</p>`;
      const result = body.querySelector('.fo-result');
      const choices = body.querySelectorAll('.fo-choice');
      for (const choice of choices) {
        choice.addEventListener('click', () => {
          for (const candidate of choices) {
            const kept = Number(candidate.dataset.row) === winningRow && Number(candidate.dataset.col) === winningField;
            candidate.classList.toggle('fo-kept', kept);
            candidate.classList.toggle('fo-picked', candidate === choice && !kept);
          }
          const correct = choice.classList.contains('fo-kept');
          const value = example.rows[winningRow][winningField][0];
          result.innerHTML = `<strong class="fo-result-label">${correct ? 'Correct' : 'Saved field'}</strong><span>Row ${winningRow+1} · <b>${fields[winningField]}</b> · ${value}<small>${example.explanation}</small></span>`;
        });
      }
    });
  }

  function fieldCell(value) {
    return value ? `<td>${value}</td>` : '<td class="fo-blank" aria-label="Empty"></td>';
  }

  function showStatus(root) {
    root.innerHTML = `
      <div class="fo-bar">
        ${exampleButtons(outcomes.map(item => item.name), 'Supplier incident name')}
        <span class="fo-context">Register <b>E01 · Cisco Ltd.</b></span>
      </div>
      <div class="fo-body"></div>`;
    const body = root.querySelector('.fo-body');
    watchExamples(root, index => {
      const item = outcomes[index];
      const count = item.status ? 1 : 0;
      const query = item.query ? `<b>${item.query}</b>` : '<i>empty</i>';
      body.innerHTML = `
        <div class="fo-trace" role="status">
          <span><small>Raw name</small><b>${item.name}</b></span><span class="fo-arrow" aria-hidden="true">→</span>
          ${item.status ? `<span><small>Search name</small>${query}</span><span class="fo-arrow" aria-hidden="true">→</span>` : ''}
          <span><small>Finding outcome</small><b class="fo-status">${item.status || 'Skipped'}</b></span>
          <span class="fo-reason">${item.reason}</span>
        </div>
        <div class="fo-file"><code>engagement_candidates.csv</code><b>${count} ${count === 1 ? 'row' : 'rows'}</b></div>
        <table class="fo-table fo-snapshot" aria-label="Selected output columns for ${item.name}">
          <thead><tr><th scope="col">incident_id</th><th scope="col">classified_supplier_name</th><th scope="col">ENGAGEMENT_ID</th><th scope="col">standardised_supplier_name</th><th scope="col">finding_status</th></tr></thead>
          <tbody>${item.status ? `<tr><th scope="row">${item.id}</th><td>${item.name}</td>${fieldCell(item.engagement)}${fieldCell(item.query)}<td>${item.status}</td></tr>` : ''}</tbody>
        </table>
        <p class="fo-note">Only class <b>SUPPLIER</b> is selected. Blank names and the whole name <b>Unknown</b> are skipped.</p>`;
    });
  }

  window.mountFindingOutcomes = function mountFindingOutcomes(container, mode) {
    const root = document.createElement('div');
    root.className = 'fo-demo';
    container.replaceChildren(root);
    if (mode === 'dedup') showDedup(root);
    else if (mode === 'status') showStatus(root);
  };
})();
