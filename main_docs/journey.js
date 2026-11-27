(() => {
  const candidates = [
    { id: 'E01', name: 'Cisco', method: 'EXACT', clue: 'Same full name',
      scope: 'WAN router support for the Leeds branch.', decision: 'LINKED', tone: 'linked' },
    { id: 'E02', name: 'Cisco', method: 'EXACT', clue: 'Same full name',
      scope: 'Video conferencing licences only.', decision: 'NOT_LINKED', tone: 'excluded' },
    { id: 'E03', name: 'Estrada Soto Francisco', method: 'SUBSTRING', clue: 'Five letters inside Francisco',
      scope: 'Cisco provides WAN router support as a subcontractor. Covered branches unspecified.', decision: 'POSSIBLY_LINKED', tone: 'possible' },
    { id: 'E04', name: 'misco', method: 'FUZZY', clue: 'C → m · 80% similarity',
      scope: 'Desktop hardware supply only.', decision: 'NOT_LINKED', tone: 'excluded' },
  ];
  const scenes = [...document.querySelectorAll('.scene')];
  const stops = [...document.querySelectorAll('.route button')];
  const element = id => document.getElementById(id);
  const dialog = element('rules-dialog');
  const guesses = new Set();
  let step = 0;
  let phase = 0;
  let revealed = false;
  let seenRegister = false;
  let removeRegister;
  let flyingWord;

  function carrySupplier(from, to) {
    if (!from || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const target = to.getBoundingClientRect();
    const word = document.createElement('span');
    word.className = 'word-flight';
    word.setAttribute('aria-hidden', 'true');
    word.textContent = 'Cisco';
    document.body.append(word);
    const position = rect => 'translate(' + Math.round(rect.left - 5) + 'px,' + Math.round(rect.top) + 'px)';
    const flight = word.animate([
      { transform: position(from), opacity: 0, offset: 0 },
      { transform: position(from), opacity: 1, offset: 0.16 },
      { transform: position(target), opacity: 1, offset: 0.83 },
      { transform: position(target), opacity: 0, offset: 1 },
    ], { duration: 600, easing: 'cubic-bezier(.25,.65,.28,1)' });
    flyingWord = flight;
    flight.onfinish = flight.oncancel = () => {
      word.remove();
      if (flyingWord === flight) flyingWord = undefined;
    };
  }

  function nameClue(candidate) {
    if (candidate.id === 'E03') return 'Estrada Soto Fran<mark class="letter-clue">cisco</mark>';
    if (candidate.id === 'E04') return '<mark>m</mark>isco';
    return candidate.name;
  }

  function openRegister() {
    const table = document.querySelector('.finding-records');
    table.classList.add('scanning');
    element('finding-rows').innerHTML = candidates.map((row, index) => `
      <tr class="found-row" style="--delay:${index * 75}ms">
        <th scope="row">${row.id}</th><td class="supplier-text">${nameClue(row)}</td>
        <td class="match">${row.method}</td><td class="clue">${row.clue}</td>
      </tr>`).join('');
    removeRegister = window.mountRegister(element('register-graphic'), () => {
      table.classList.remove('scanning');
      seenRegister = true;
      element('announcement').textContent = 'Four candidate engagements found.';
    }, !seenRegister);
  }

  function drawLinks() {
    element('linking-prompt').textContent = revealed
      ? 'Each engagement is assessed independently.'
      : 'Mark any leads before revealing the evidence.';
    element('linking-rows').innerHTML = candidates.map((row, index) => {
      const selected = guesses.has(row.id) ? 'checked' : '';
      const id = `<label class="pick"><input type="checkbox" value="${row.id}" aria-label="Mark ${row.id} as a lead" ${selected} ${revealed ? 'disabled' : ''}>${row.id}</label>`;
      const evidence = revealed
        ? `<td class="scope">${row.scope}</td><td><span class="decision ${row.tone}">${row.decision}</span></td>`
        : '<td class="sealed"><span class="sr-only">Scope hidden</span><i class="sealed-line"></i></td><td class="sealed"><span class="sr-only">Decision hidden</span><i class="sealed-line"></i></td>';
      return `<tr class="${revealed ? 'unsealed' : 'guess-row'}" style="--delay:${index * 100}ms"><th scope="row">${id}</th><td class="supplier-text">${row.name}</td>${evidence}</tr>`;
    }).join('');
  }

  function drawControls() {
    const classActions = ['Classify incident', 'Extract supplier name', 'Find candidates'];
    const actions = [classActions[phase], 'Assess candidates', revealed ? 'Trace the evidence' : 'Reveal evidence', 'Replay case'];
    element('previous').disabled = step === 0 && phase === 0;
    element('next-text').textContent = actions[step];
    element('next-arrow').textContent = step === 3 ? '↺' : '→';
    element('page-count').textContent = '0' + (step + 1) + ' / 04';
  }

  function drawPhase() {
    const hero = document.querySelector('.hero');
    hero.classList.toggle('is-classified', step === 0 && phase >= 1);
    hero.classList.toggle('is-named', step === 1 || (step === 0 && phase === 2));
    hero.classList.toggle('is-comparing', step === 3);
    element('class-flow').dataset.phase = phase;
    element('supplier-value').textContent = phase === 2 ? 'Cisco' : '—';
    drawControls();
  }

  function goTo(index) {
    flyingWord?.cancel();
    const queryOrigin = step === 0 && phase === 2 && index === 1
      ? element('supplier-value').getBoundingClientRect() : null;
    if (removeRegister) {
      removeRegister();
      removeRegister = undefined;
    }
    step = index;
    if (index > 0) phase = 2;
    if (index === 3) revealed = true;
    scenes.forEach((scene, i) => { scene.hidden = i !== step; });
    stops.forEach((button, i) => {
      if (i === step) button.setAttribute('aria-current', 'step');
      else button.removeAttribute('aria-current');
      button.classList.toggle('passed', i < step);
    });
    document.querySelector('.route').style.setProperty('--step', step);
    element('announcement').textContent = stops[step].textContent.trim();
    if (step === 1) openRegister();
    if (step === 2) drawLinks();
    if (step === 3) window.mountEvidence(element('evidence-view'));
    drawPhase();
    if (queryOrigin) carrySupplier(queryOrigin, document.querySelector('.register-query strong'));
  }

  function next() {
    if (step === 0 && phase < 2) {
      phase++;
      drawPhase();
      if (phase === 2) carrySupplier(element('subject').getBoundingClientRect(), element('supplier-value'));
      element('announcement').textContent = phase === 1 ? 'Class: supplier.' : 'Supplier name: Cisco.';
    } else if (step === 2 && !revealed) {
      revealed = true;
      drawLinks();
      drawControls();
      element('announcement').textContent = 'Four assessments revealed.';
    } else if (step === 3) {
      phase = 0;
      revealed = false;
      seenRegister = false;
      guesses.clear();
      goTo(0);
    } else {
      goTo(step + 1);
    }
  }

  function back() {
    flyingWord?.cancel();
    if (step === 0 && phase > 0) {
      phase--;
      drawPhase();
    } else if (step === 2 && revealed) {
      revealed = false;
      drawLinks();
      drawControls();
    } else if (step > 0) {
      goTo(step - 1);
    }
  }

  stops.forEach((button, index) => button.addEventListener('click', () => {
    if (step !== index) goTo(index);
  }));
  element('linking-rows').addEventListener('change', event => {
    const input = event.target;
    if (!input.matches('input[type="checkbox"]')) return;
    if (input.checked) guesses.add(input.value);
    else guesses.delete(input.value);
  });
  element('next').addEventListener('click', next);
  element('previous').addEventListener('click', back);
  element('rules-open').addEventListener('click', () => dialog.showModal());
  element('rules-close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const rect = dialog.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
  });
  document.addEventListener('keydown', event => {
    if (element('journey-panel').hidden || event.target.closest?.('[role="tablist"]')) return;
    if (dialog.open || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey || event.repeat) return;
    if (event.key !== 'ArrowRight' && event.key !== 'ArrowLeft') return;
    event.preventDefault();
    if (event.key === 'ArrowRight') next();
    else back();
  });
  goTo(0);
})();
