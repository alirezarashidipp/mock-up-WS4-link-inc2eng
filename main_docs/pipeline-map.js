(() => {
  // Synthetic engagements in the order of the whiteboard's assessment column.
  const engagements = [
    {
      id: 'ENG40', name: 'Cisco Systems', method: 'SUBSTRING', decision: 'LINKED',
      scope: 'Firmware maintenance for Cisco routers at the Leeds branch.',
      reason: 'The supplier, router firmware and branch all match the incident.',
    },
    {
      id: 'ENG20', name: 'Cisco', method: 'EXACT', decision: 'LINKED',
      scope: 'Restore Cisco WAN router service after outages at the Leeds branch.',
      reason: 'The Leeds router outage falls within the contracted recovery service.',
    },
    {
      id: 'ENG31', name: 'Estrada Soto Francisco', method: 'SUBSTRING', decision: 'POSSIBLY_LINKED',
      scope: 'Cisco provides WAN router support as a subcontractor. Covered sites are unspecified.',
      reason: 'The service fits the failure. Leeds coverage still needs confirmation.',
    },
    {
      id: 'ENG41', name: 'Cisco', method: 'EXACT', decision: 'NOT_LINKED',
      scope: 'Video conferencing licences only. Network hardware is excluded.',
      reason: 'The licence agreement explicitly excludes the failed router.',
    },
    {
      id: 'ENG60', name: 'misco', method: 'FUZZY', decision: 'NOT_LINKED',
      scope: 'Supply of desktop monitors only for the Leeds branch.',
      reason: 'The failed router falls outside the monitor contract.',
    },
  ];

  const get = id => document.getElementById(id);
  const panel = get('map-panel');
  const journey = get('journey-panel');
  const candidates = get('map-candidates');
  const other = get('map-others');
  const evidence = get('map-evidence');
  const wires = get('map-wires');
  const compact = window.matchMedia('(max-width: 760px)');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const nodes = new Map();
  let selected = engagements[0];
  let wireFrame;

  function tone(decision) {
    if (decision === 'LINKED') return 'linked';
    if (decision === 'POSSIBLY_LINKED') return 'possible';
    return 'other';
  }

  function makeNode(record, kind) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'map-node map-' + kind;
    button.setAttribute('aria-controls', 'map-evidence');
    button.addEventListener('click', () => selectEngagement(record, true));
    const id = document.createElement('span');
    id.className = 'map-node-id';
    id.textContent = record.id;
    button.append(id);
    return button;
  }

  function supplierLabel(record) {
    const name = document.createElement('span');
    name.className = 'map-name';
    if (record.method === 'EXACT') {
      name.textContent = record.name;
      return name;
    }
    const start = record.method === 'SUBSTRING' ? record.name.toLowerCase().indexOf('cisco') : 0;
    const length = record.method === 'SUBSTRING' ? 'Cisco'.length : 1;
    const clue = document.createElement('mark');
    clue.textContent = record.name.slice(start, start + length);
    name.append(record.name.slice(0, start), clue, record.name.slice(start + length));
    return name;
  }

  function setVerdict(label, record) {
    label.className = 'map-tone';
    label.dataset.tone = tone(record.decision);
    label.textContent = record.decision;
  }

  function buildMap() {
    for (const record of engagements) {
      const result = makeNode(record, 'result');
      const verdict = document.createElement('span');
      setVerdict(verdict, record);
      result.append(verdict);
      const group = tone(record.decision) === 'other' ? get('map-other-results') : get('map-results');
      group.append(result);
      nodes.set(record.id, { result });
    }

    const findingOrder = [...engagements].sort((a, b) => a.id.localeCompare(b.id, 'en', { numeric: true }));
    for (const record of findingOrder) {
      const candidate = makeNode(record, 'candidate');
      const method = document.createElement('span');
      method.className = 'map-method';
      method.textContent = record.method;
      candidate.append(supplierLabel(record), method);
      candidates.append(candidate);
      const pin = document.createElement('i');
      pin.className = 'map-pin';
      get('map-field').append(pin);
      Object.assign(nodes.get(record.id), { candidate, pin });
    }
    get('map-found-count').textContent = engagements.length;
    get('map-result-count').textContent = get('map-results').childElementCount;
    const linked = engagements.filter(record => record.decision === 'LINKED').length;
    const possible = engagements.filter(record => record.decision === 'POSSIBLY_LINKED').length;
    get('map-breakdown').textContent = linked + ' linked · ' + possible + ' possible';
    get('map-other-count').textContent = get('map-other-results').childElementCount;
  }

  function drawWires() {
    if (panel.hidden || compact.matches) return;
    const bounds = wires.getBoundingClientRect();
    const scale = window.devicePixelRatio || 1;
    wires.width = Math.round(bounds.width * scale);
    wires.height = Math.round(bounds.height * scale);
    const pen = wires.getContext('2d');
    if (!pen) return;
    pen.scale(scale, scale);

    function connect(from, to, colour, active, dashed = false) {
      const a = from.getBoundingClientRect();
      const b = to.getBoundingClientRect();
      const x1 = a.right - bounds.left;
      const x2 = b.left - bounds.left;
      const y1 = a.top + a.height / 2 - bounds.top;
      const y2 = b.top + b.height / 2 - bounds.top;
      const middle = (x1 + x2) / 2;
      pen.beginPath();
      pen.moveTo(x1, y1);
      pen.bezierCurveTo(middle, y1, middle, y2, x2, y2);
      pen.strokeStyle = active ? colour : '#bdc6c8';
      pen.lineWidth = active ? 2.6 : 1.2;
      pen.setLineDash(dashed ? [4, 4] : []);
      pen.stroke();
      if (active) {
        pen.beginPath();
        pen.arc(x2 - 2, y2, 2.6, 0, 2 * Math.PI);
        pen.fillStyle = colour;
        pen.fill();
      }
    }

    // Paint the selected path last so it stays visible where paths cross.
    const traceOrder = engagements.filter(record => record !== selected).concat(selected);
    const colours = { linked: '#106047', possible: '#865100', other: '#54616a' };
    for (const record of traceOrder) {
      const { candidate, result } = nodes.get(record.id);
      const active = record === selected;
      const status = tone(record.decision);
      const target = status === 'other' && !other.open ? get('map-others-label') : result;
      connect(get('map-register'), candidate, '#bd0824', active);
      connect(candidate, target, colours[status], active, status !== 'linked');
    }
  }

  function scheduleWires() {
    cancelAnimationFrame(wireFrame);
    wireFrame = requestAnimationFrame(drawWires);
  }

  function selectEngagement(record, activated = false) {
    selected = record;
    if (activated && tone(record.decision) === 'other') other.open = true;
    for (const [id, { candidate, result, pin }] of nodes) {
      const active = id === record.id;
      candidate.setAttribute('aria-pressed', String(active));
      result.setAttribute('aria-pressed', String(active));
      pin.classList.toggle('is-selected', active);
    }
    get('map-evidence-id').textContent = record.id;
    get('map-evidence-supplier').textContent = record.name;
    get('map-scope').textContent = record.scope;
    get('map-reason').textContent = record.reason;
    setVerdict(get('map-verdict'), record);
    scheduleWires();
    if (!activated) return;
    get('map-announcement').textContent = record.id + ', ' + record.decision.replaceAll('_', ' ') + '. ' + record.reason;
    if (compact.matches) {
      evidence.focus({ preventScroll: true });
      evidence.scrollIntoView({ block: 'nearest', behavior: reducedMotion.matches ? 'instant' : 'smooth' });
    } else if (!reducedMotion.matches) {
      evidence.animate([{ opacity: .55 }, { opacity: 1 }], { duration: 190 });
    }
  }

  const tabs = [get('journey-tab'), get('map-tab')];

  function showView() {
    const showMap = location.hash === '#pipeline-map';
    const previous = showMap ? journey : panel;
    const moveFocus = previous.contains(document.activeElement);
    journey.hidden = showMap;
    panel.hidden = !showMap;
    const current = showMap ? tabs[1] : tabs[0];
    for (const tab of tabs) {
      tab.setAttribute('aria-selected', String(tab === current));
      tab.tabIndex = tab === current ? 0 : -1;
    }
    if (moveFocus) current.focus();
    if (showMap) scheduleWires();
  }

  function activateTab(tab) {
    const hash = tab === tabs[1] ? '#pipeline-map' : '#case-journey';
    if (location.hash !== hash) location.hash = hash;
    showView();
  }

  for (const tab of tabs) {
    tab.addEventListener('click', () => activateTab(tab));
    tab.addEventListener('keydown', event => {
      let next;
      if (event.key === 'Home') next = tabs[0];
      else if (event.key === 'End') next = tabs[1];
      else if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') next = tabs.find(item => item !== tab);
      else return;
      event.preventDefault();
      next.focus();
      activateTab(next);
    });
  }
  other.addEventListener('toggle', scheduleWires);
  get('map-return').addEventListener('click', () => {
    const button = nodes.get(selected.id).candidate;
    button.focus({ preventScroll: true });
    button.scrollIntoView({ block: 'center', behavior: reducedMotion.matches ? 'instant' : 'smooth' });
  });
  new ResizeObserver(scheduleWires).observe(get('map-board'));
  window.addEventListener('hashchange', showView);
  buildMap();
  selectEngagement(selected);
  showView();
})();
