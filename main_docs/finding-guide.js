(() => {
  'use strict';

  const lab = window.FindingLab;
  const byId = id => document.getElementById(id);
  const menu = [...document.querySelectorAll('.guide-menu a')];
  const chapters = [
    { id: 'prepare', label: 'Input preparation', title: 'Prepare the supplier name.',
      summary: 'Clean both sources. Apply a whole-name alias only to the incident.' },
    { id: 'exact', label: 'Match priority 1', title: 'Do the full names agree?',
      summary: 'EXACT compares the entire cleaned names with spaces removed.' },
    { id: 'substring', label: 'Match priority 2', title: 'Where does the name appear?',
      summary: '1–4 characters require a whole word. From 5 characters, the query can appear inside or across words.' },
    { id: 'fuzzy', label: 'Match priority 3', title: 'How close is close enough?',
      summary: 'For queries of 5+ characters, compare consecutive reference words. The first score at or above 72% passes.' },
  ];
  const examples = {
    prepare: [
      ['BT', 'B.T. Ltd.', 'British Telecom plc'],
      ['Azure', 'Azure', 'Microsoft Ltd.'],
      ['GCP', 'G.C.P.', 'Google LLC'],
      ['Reverse the alias', 'British Telecom', 'B.T. Ltd.'],
    ],
    exact: [
      ['Different case', 'Cisco', 'CISCO'],
      ['Legal suffix', 'Cisco', 'Cisco Ltd.'],
      ['Different spacing', 'Cis Co', 'Cisco'],
    ],
    substring: [
      ['Whole word', 'IBM', 'IBM Cloud'],
      ['Inside a word', 'IBM', 'ibmotor'],
      ['Five characters', 'Cisco', 'Estrada Soto Francisco'],
      ['Across words', 'Cisco', 'Cis Co UK'],
    ],
    fuzzy: [
      ['One edit', 'Cisco', 'misco'],
      ['Two edits', 'Cisco', 'mitco'],
      ['Adjacent words', 'Cisco', 'UK mis co service'],
      ['Exactly 72%', 'Northbridge Digital Systems', 'NorthbridgeDigitalBanking'],
    ],
  };
  const incidentInput = byId('incident-input');
  const referenceInput = byId('reference-input');
  const panelLinks = menu.map(a => a.hash.slice(1));
  const selected = new Map();
  let chapter = 0;
  let revealed = false;

  function drawChoices(container, items, choice, onPick) {
    container.replaceChildren();
    for (const [index, item] of items.entries()) {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = item[0];
      button.setAttribute('aria-pressed', String(index === choice));
      button.addEventListener('click', () => {
        for (const other of container.children) other.setAttribute('aria-pressed', String(other === button));
        onPick(index);
      });
      container.append(button);
    }
  }

  function prepare(choice) {
    const [, raw, reference] = examples.prepare[choice];
    const result = lab.compare(raw, reference);
    const rows = [
      ['Source value', raw, reference],
      ['Shared cleaner', result.cleanIncident, result.cleanReference],
      ['Whole-name alias', result.queryName, result.cleanReference],
      ['Compare without spaces', result.query, result.compactReference],
    ];
    const tbody = byId('prep-rows');
    tbody.replaceChildren();
    rows.forEach((values, index) => {
      const row = tbody.insertRow();
      const th = document.createElement('th');
      th.scope = 'row';
      th.textContent = values[0];
      row.append(th);
      for (let side = 1; side <= 2; side++) {
        const td = row.insertCell();
        td.textContent = values[side];
        if (index === 2 && side === 1 && result.queryName !== result.cleanIncident) td.className = 'changed';
      }
    });
  }

  function conceal() {
    revealed = false;
    byId('verdict').textContent = 'Which rule will pass?';
    delete byId('verdict').dataset.revealed;
    byId('comparison-detail').hidden = true;
    byId('compare-button').firstChild.textContent = 'Reveal match ';
    byId('compare-button').setAttribute('aria-expanded', 'false');
  }

  function setComparison(id, choice) {
    const [, raw, reference] = examples[id][choice];
    incidentInput.value = raw;
    referenceInput.value = reference;
    conceal();
  }

  function printReference(result) {
    const target = byId('trace-reference');
    const source = result.cleanReference;
    target.textContent = source || '—';
    const singleFailedWord = result.reason === 'fuzzy_below' && !source.includes(' ');
    const match = singleFailedWord ? source : result.matchedText;
    if (!match) return;
    const wholeWords = result.reason === 'whole_word' || result.reason === 'fuzzy_pass';
    const start = wholeWords ? (' ' + source + ' ').indexOf(' ' + match + ' ') : source.indexOf(match);
    if (start < 0) return;
    const mark = document.createElement('span');
    const windowLetters = Array.from(match.replaceAll(' ', ''));
    const queryLetters = Array.from(result.query);
    const changes = windowLetters.filter((letter, i) => letter !== queryLetters[i]).length;
    const edits = result.score === null ? null : Math.round((1 - result.score) * Math.max(windowLetters.length, queryLetters.length));
    if (edits !== null && windowLetters.length === queryLetters.length && changes === edits) {
      // Highlight substitutions only when they form a shortest edit path.
      mark.className = 'edit-window';
      let index = 0;
      for (const letter of match) {
        if (letter !== ' ' && letter !== queryLetters[index]) {
          const changed = document.createElement('mark');
          changed.textContent = letter;
          mark.append(changed);
        } else {
          mark.append(letter);
        }
        if (letter !== ' ') index++;
      }
    } else if (result.matchedText) {
      const excerpt = document.createElement('mark');
      excerpt.textContent = match;
      mark.append(excerpt);
    } else {
      mark.textContent = match;
    }
    target.replaceChildren(source.slice(0, start), mark, source.slice(start + match.length));
  }

  function reveal() {
    const result = lab.compare(incidentInput.value, referenceInput.value);
    const percentage = result.score === null ? '' : (result.score * 100).toLocaleString('en-GB', { maximumFractionDigits: 2 }) + '%';
    const reasons = {
      skipped_blank: 'A blank incident supplier is skipped before matching.',
      skipped_unknown: 'The whole name Unknown is skipped before matching.',
      empty_query: 'Cleaning left an empty incident search name.',
      empty_reference: 'This engagement field is empty after cleaning.',
      equal: 'Both complete names are identical after spaces are removed.',
      whole_word: 'The short query is a complete reference word.',
      embedded: 'All query characters appear together after spaces are removed.',
      short_inside_word: 'The characters occur inside a longer word or across a word boundary. A short query requires one whole word.',
      short_no_match: 'No whole reference word matches. Fuzzy matching starts at five characters.',
      fuzzy_pass: percentage + ' similarity meets the 72% threshold.',
      fuzzy_below: 'Best eligible word window: ' + percentage + '. The threshold is 72%.',
      fuzzy_length: 'No adjacent word window is close enough in length to reach 72%.',
    };
    revealed = true;
    const label = result.method === 'NO_MATCH' ? 'No field match' : result.method;
    byId('verdict').textContent = label;
    byId('verdict').dataset.revealed = '';
    byId('comparison-detail').hidden = false;
    byId('compare-button').firstChild.textContent = 'Hide result ';
    byId('compare-button').setAttribute('aria-expanded', 'true');
    const length = Array.from(result.query).length;
    byId('trace-query').textContent = length ? result.query + ' · ' + length + (length === 1 ? ' character' : ' characters') : '—';
    printReference(result);
    byId('explanation').textContent = reasons[result.reason];
    byId('score-line').hidden = result.score === null;
    byId('score-line').style.setProperty('--score', percentage || '0%');
    byId('guide-live').textContent = label + '. ' + reasons[result.reason];
  }

  function render(focusTitle = false) {
    const index = panelLinks.indexOf(location.hash.slice(1));
    chapter = index < 0 ? 0 : index;
    const config = chapters[chapter];
    menu.forEach((link, i) => {
      if (i === chapter) link.setAttribute('aria-current', 'step');
      else link.removeAttribute('aria-current');
    });
    byId('chapter-label').textContent = config.label;
    byId('guide-title').textContent = config.title;
    byId('guide-summary').textContent = config.summary;
    byId('prev-rule').disabled = chapter === 0;
    byId('next-rule').firstChild.textContent = chapter === chapters.length - 1 ? 'Start again ' : 'Next rule ';
    const prep = config.id === 'prepare';
    byId('prepare-body').hidden = !prep;
    byId('match-body').hidden = prep;
    byId('fuzzy-info').hidden = config.id !== 'fuzzy';
    const choice = selected.get(config.id) ?? 0;
    const change = index => {
      selected.set(config.id, index);
      if (prep) prepare(index);
      else setComparison(config.id, index);
    };
    drawChoices(byId(prep ? 'prepare-choices' : 'match-choices'), examples[config.id], choice, change);
    change(choice);
    if (focusTitle) byId('guide-title').focus({ preventScroll: true });
  }

  byId('compare-form').addEventListener('submit', event => {
    event.preventDefault();
    if (revealed) conceal();
    else reveal();
  });
  byId('compare-form').addEventListener('input', () => {
    for (const button of byId('match-choices').children) button.setAttribute('aria-pressed', 'false');
    conceal();
  });
  byId('next-rule').addEventListener('click', () => { location.hash = chapters[(chapter + 1) % chapters.length].id; });
  byId('prev-rule').addEventListener('click', () => { if (chapter > 0) location.hash = chapters[chapter - 1].id; });
  window.addEventListener('hashchange', () => render(true));
  render();
})();
