(() => {
  const svgNamespace = 'http://www.w3.org/2000/svg';
  let instanceNumber = 0;

  function svgElement(tag, attributes = {}) {
    const element = document.createElementNS(svgNamespace, tag);
    for (const [name, value] of Object.entries(attributes)) {
      element.setAttribute(name, value);
    }
    return element;
  }

  function createRegister() {
    const svg = svgElement('svg', {
      viewBox: '0 0 1024 94',
      preserveAspectRatio: 'none',
      'aria-hidden': 'true',
      focusable: 'false'
    });
    svg.style.cssText = 'display:block;width:100%;height:100%;overflow:hidden';

    // The marks represent the shape of the register. They are not a record count.
    const columns = 92;
    const rows = 8;
    const targets = [[14, 2], [36, 5], [60, 1], [80, 4]];
    const x = column => 14 + column * 10.9;
    const y = row => 12 + row * 10;
    const segments = [[], [], []];
    for (let column = 0; column < columns; column++) {
      for (let row = 0; row < rows; row++) {
        if (targets.some(([c, r]) => c === column && r === row)) continue;
        const pattern = (column * 17 + row * 13 + column * row) % 19;
        const length = 2 + pattern % 5;
        segments[pattern % 3].push('M' + x(column).toFixed(1) + ' ' + y(row) + 'h' + length);
      }
    }
    const tones = ['#c8cdce', '#b2babb', '#d2d6d6'];
    segments.forEach((segment, index) => {
      svg.append(svgElement('path', {
        d: segment.join(' '), fill: 'none', stroke: tones[index],
        'stroke-width': 2, 'stroke-linecap': 'round'
      }));
    });

    const gradientId = 'register-scan-' + ++instanceNumber;
    const definitions = svgElement('defs');
    const gradient = svgElement('linearGradient', { id: gradientId });
    gradient.append(
      svgElement('stop', { offset: '0%', 'stop-color': '#db0011', 'stop-opacity': 0 }),
      svgElement('stop', { offset: '100%', 'stop-color': '#db0011', 'stop-opacity': 0.12 })
    );
    definitions.append(gradient);
    svg.append(definitions);
    const sweep = svgElement('g', { transform: 'translate(-5 0)' });
    sweep.append(
      svgElement('rect', { x: -74, y: 1, width: 74, height: 92, fill: 'url(#' + gradientId + ')' }),
      svgElement('path', { d: 'M0 3V91', stroke: 'var(--red, #db0011)', 'stroke-width': 1.25 })
    );
    svg.append(sweep);

    const signals = targets.map(([column, row]) => {
      const left = x(column);
      const signal = svgElement('g', { transform: 'translate(' + left + ' ' + y(row) + ')', opacity: 0 });
      signal.append(
        svgElement('rect', { x: -4, y: -5, width: 15, height: 10, rx: 2, fill: '#fbe1e3' }),
        svgElement('path', { d: 'M0 0h7', stroke: 'var(--red, #db0011)', 'stroke-width': 3, 'stroke-linecap': 'round' })
      );
      svg.append(signal);
      return { left, signal };
    });
    return { svg, sweep, signals };
  }

  window.mountRegister = function mountRegister(container, onComplete, animate = true) {
    const { svg, sweep, signals } = createRegister();
    container.replaceChildren(svg);
    let frame = 0;
    let finished = false;

    function finish() {
      if (finished) return;
      finished = true;
      sweep.remove();
      for (const { signal } of signals) signal.setAttribute('opacity', '1');
      if (typeof onComplete === 'function') onComplete();
    }

    function cleanup() {
      finished = true;
      cancelAnimationFrame(frame);
      svg.remove();
    }

    if (!animate || document.hidden || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      finish();
      return cleanup;
    }

    const start = performance.now();
    function scan(time) {
      if (finished) return;
      const progress = Math.min(1, (time - start) / 1050);
      const position = 1040 * progress;
      sweep.setAttribute('transform', 'translate(' + position + ' 0)');
      for (const { left, signal } of signals) {
        if (position >= left) signal.setAttribute('opacity', '1');
      }
      if (progress >= 1) finish();
      else frame = requestAnimationFrame(scan);
    }
    frame = requestAnimationFrame(scan);
    return cleanup;
  };
})();
