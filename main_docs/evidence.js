(() => {
  const cases = {
    E01: {
      decision: 'LINKED',
      scope: '<mark>WAN router</mark> support for the <mark>Leeds branch</mark>.',
      service: 'WAN router support',
      branch: 'Leeds branch',
    },
    E03: {
      decision: 'POSSIBLY_LINKED',
      scope: 'Cisco provides <mark>WAN router</mark> support as a subcontractor. Covered branches unspecified.',
      service: 'WAN router support',
      branch: 'Unspecified',
    },
  };

  function lane(label, incident, engagement, uncertain = false) {
    return `
      <tr class="ev-lane${uncertain ? ' ev-lane-open' : ''}">
        <td class="ev-term">${incident}</td>
        <th scope="row" class="ev-connection">
          <span class="ev-path"><i aria-hidden="true"></i><span>${label}</span><i aria-hidden="true"></i></span>
        </th>
        <td class="ev-term">${engagement}</td>
      </tr>`;
  }

  window.mountEvidence = function mountEvidence(container) {
    container.innerHTML = `
      <div class="evidence-scene">
        <div class="ev-controls">
          <div class="ev-switch" role="group" aria-label="Compare engagement evidence">
            <button type="button" data-case="E01" aria-pressed="true"><b>E01</b> Cisco</button>
            <button type="button" data-case="E03" aria-pressed="false"><b>E03</b> Estrada Soto Francisco</button>
          </div>
          <output class="ev-outcome" aria-label="Link decision"></output>
        </div>
        <div class="ev-comparison"></div>
      </div>`;

    const scene = container.querySelector('.evidence-scene');
    const buttons = scene.querySelectorAll('[data-case]');
    const outcome = scene.querySelector('.ev-outcome');
    const comparison = scene.querySelector('.ev-comparison');

    function select(id) {
      const record = cases[id];
      const uncertain = id === 'E03';
      for (const button of buttons) {
        button.setAttribute('aria-pressed', String(button.dataset.case === id));
      }
      outcome.classList.toggle('ev-uncertain', uncertain);
      outcome.textContent = record.decision;
      comparison.innerHTML = `
        <div class="ev-sources">
          <div class="ev-record">
            <div class="ev-label">Incident finding</div>
            <p>Cisco confirmed its firmware defect took the <mark>Leeds branch</mark> <mark>router</mark> offline.</p>
          </div>
          <div class="ev-record">
            <div class="ev-label">Engagement scope · ${id}</div>
            <p>${record.scope}</p>
          </div>
        </div>
        <table class="ev-map" aria-label="Incident and ${id} engagement evidence by service and branch">
          <colgroup><col><col class="ev-path-column"><col></colgroup>
          <thead class="ev-sr-only"><tr><th scope="col">Incident</th><th scope="col">Evidence type</th><th scope="col">Engagement</th></tr></thead>
          <tbody>
            ${lane('Service', 'router', record.service)}
            ${lane('Branch', 'Leeds branch', record.branch, uncertain)}
          </tbody>
        </table>`;
    }

    for (const button of buttons) {
      button.addEventListener('click', () => select(button.dataset.case));
    }
    select('E01');
  };
})();
