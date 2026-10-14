// The browser collects inputs and displays responses. All finance stays in Python.
const initial = JSON.parse(document.getElementById('initial-inputs').textContent);
let state = structuredClone(initial);
// Older saved inputs had fixed pensions; retain that behavior at 0%.
for (const person of [state.client, state.spouse, initial.client, initial.spouse]) {
  if (person && person.pension_indexation_percent === undefined) person.pension_indexation_percent = 0;
}
let spouseDraft = state.spouse && structuredClone(state.spouse);
let version = 0;
let timer;
let controller;
const aside = document.querySelector('.inputs-column');
const status = document.querySelector('.live-note');
status.setAttribute('role', 'status');
const errors = document.createElement('div');
errors.className = 'error-banner'; errors.hidden = true; errors.setAttribute('role', 'alert');
document.querySelector('.planner-layout').before(errors);
aside.querySelector('.column-heading span:last-child').textContent = 'Make it yours';
aside.setAttribute('aria-label', 'Scenario inputs');
const pdfButtons = [...document.querySelectorAll('.pdf-export')];
let validVersion = -1;
let exportingPDF = false;
function updatePDFButtons() {
  pdfButtons.forEach(button => { button.disabled = exportingPDF || validVersion !== version; });
}
const reset = document.createElement('button');
reset.className = 'button button-subtle'; reset.textContent = 'Reset example';
document.querySelector('.action-row').prepend(reset);

// The selected starting date stays in the scenario record; it is not a visible field.

function blankSpouse() {
  // Empty fields require user input. Do not invent a spouse's financial assumptions.
  return {dob: '', retirement_age: null, plan_end: '', income: null, pension: null,
    pension_indexation_percent: 0,
    cpp_percent: null, cpp_age: null, oas_percent: null, oas_deferral: null,
    accounts: Object.fromEntries(['Cash', 'RRSP', 'TFSA'].map(name => [name,
      {balance: null, contribution: null, indexation_percent: null}]))};
}
function readPath(record, path) { return path.reduce((value, name) => value?.[name], record); }
function updateAgeDisplays() {
  function ageAt(birth, on) {
    if (!birth || !on) return '—';
    const [year, month, day] = birth.split('-').map(Number);
    const [endYear, endMonth, endDay] = on.split('-').map(Number);
    if (![year, month, day, endYear, endMonth, endDay].every(Number.isFinite)) return '—';
    return endYear - year - Number(endMonth < month || (endMonth === month && endDay < day));
  }
  aside.querySelectorAll('[data-age]').forEach(input => {
    const [who, kind] = input.dataset.age.split('.');
    const person = who === 'spouse' ? state.spouse || spouseDraft : state.client;
    input.value = person ? ageAt(person.dob, kind === 'current_age' ? state.as_of : person.plan_end) : '—';
  });
}
function setField(path, value) {
  const parts = path.split('.'); const last = parts.pop();
  const record = parts.reduce((value, name) => value[name], state);
  record[last] = value;
}
function updateIndexationLabels() {
  aside.querySelectorAll('.indexation-edit').forEach(editor => {
    const input = editor.querySelector('[data-input]');
    editor.querySelector('summary').textContent = input.value !== '' && Number(input.value) !== 0
      ? `Edit indexation · ${input.value}%/year` : 'Edit indexation';
  });
}
function fillFields() {
  const values = {...state, spouse: state.spouse || spouseDraft || blankSpouse()};
  aside.querySelectorAll('[data-input]').forEach(input => {
    const value = readPath(values, input.dataset.input.split('.'));
    input.value = Array.isArray(value) ? value.join(',') : value ?? '';
  });
  updateSpouse();
  updateAgeDisplays();
  updateIndexationLabels();
}
function updateSpouse() {
  const active = state.spouse !== null;
  const button = document.getElementById('include-spouse');
  button.classList.toggle('checked', active); button.setAttribute('aria-checked', String(active));
  document.querySelector('.person-tabs').hidden = !active;
  if (!active) document.querySelector('[data-person-tab="client"]').click();
}
function invalidate() {
  version++; clearTimeout(timer); controller?.abort();
  validVersion = -1;
  updatePDFButtons();
  errors.hidden = true;
  document.querySelector('.results-column').hidden = true;
  document.querySelector('.annual-section').hidden = true;
  status.textContent = 'Updating…';
  timer = setTimeout(recalculate, 350);
}
aside.addEventListener('input', event => {
  const input = event.target.closest('[data-input]');
  if (!input) return;
  let value = input.value;
  if (input.type === 'number') value = value.trim() === '' ? null : Number(value);
  if (input.dataset.input === 'withdrawal_order') value = value.split(',');
  setField(input.dataset.input, value);
  if (state.spouse) spouseDraft = structuredClone(state.spouse);
  updateAgeDisplays();
  updateIndexationLabels();
  // Keep the explanatory OAS age synchronized as well as the calculations.
  if (input.dataset.input.endsWith('.oas_deferral')) {
    const note = input.closest('[data-person]').querySelector('.field-note:last-of-type');
    if (note) note.textContent = 'OAS starts at age ' + (65 + Number(value)) + '. Start-year payments are prorated by birthday.';
  }
  invalidate();
});
document.getElementById('include-spouse').addEventListener('click', () => {
  if (state.spouse) { spouseDraft = structuredClone(state.spouse); state.spouse = null; }
  else state.spouse = structuredClone(spouseDraft || blankSpouse());
  fillFields();
  if (state.spouse) document.querySelector('[data-person-tab="spouse"]').click();
  invalidate();
});
reset.addEventListener('click', () => {
  state = structuredClone(initial); spouseDraft = state.spouse && structuredClone(state.spouse);
  fillFields(); document.querySelector('[data-person-tab="client"]').click(); invalidate();
});
async function recalculate() {
  const requestedVersion = version;
  controller = new AbortController();
  try {
    const response = await fetch('/api/project', {method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(state), signal: controller.signal});
    const result = await response.json();
    if (requestedVersion !== version) return;
    if (!response.ok) throw new Error(result.error || 'Please check your inputs.');
    const incoming = new DOMParser().parseFromString(result.html, 'text/html');
    const open = document.querySelector('.annual-toggle').getAttribute('aria-expanded') === 'true';
    const basis = document.getElementById('dollar-basis').value;
    ['.results-column', '.annual-section'].forEach(selector => {
      document.querySelector(selector).replaceWith(incoming.querySelector(selector));
    });
    if (open) document.querySelector('.annual-toggle').click();
    document.getElementById('dollar-basis').value = basis;
    document.getElementById('dollar-basis').dispatchEvent(new Event('change', {bubbles: true}));
    initCharts();
    status.textContent = 'Up to date · changes calculate automatically';
    validVersion = requestedVersion;
    updatePDFButtons();
    errors.hidden = true;
  } catch (error) {
    if (error.name === 'AbortError' || requestedVersion !== version) return;
    errors.textContent = error instanceof TypeError ? 'Cannot reach Python. Keep the terminal running and try changing a field again.' : error.message;
    errors.style.whiteSpace = 'pre-line'; errors.hidden = false;
    status.textContent = 'Check your inputs';
  }
}
pdfButtons.forEach(button => button.addEventListener('click', async () => {
  if (button.disabled || validVersion !== version) return;
  const snapshot = structuredClone(state);
  const basis = button.dataset.pdf === 'advisor' && document.getElementById('dollar-basis').value === 'real' ? 'today_cad' : 'nominal_cad';
  const requestedVersion = version;
  const originalLabel = button.innerHTML;
  exportingPDF = true; updatePDFButtons();
  reset.disabled = true;
  // Lock inputs briefly so the screen and downloaded PDF refer to one scenario.
  aside.inert = true;
  button.textContent = 'Preparing PDF…';
  errors.hidden = true;
  try {
    const response = await fetch('/api/pdf/' + button.dataset.pdf, {
      method:'POST', headers:{'Content-Type':'application/json','X-FRESH-Dollar-Basis':basis}, body:JSON.stringify(snapshot)
    });
    if (!response.ok) {
      const result = await response.json(); throw new Error(result.error || 'Unable to export PDF.');
    }
    const blob = await response.blob();
    if (requestedVersion !== version) throw new Error('Inputs changed. Please export again after updating.');
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    const disposition = response.headers.get('Content-Disposition') || '';
    anchor.download = disposition.match(/filename="([^"]+)"/)?.[1] || ('fresh-' + button.dataset.pdf + '.pdf');
    anchor.href = url; document.body.append(anchor); anchor.click(); anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  } catch (error) {
    errors.textContent = error.message; errors.hidden = false;
  } finally {
    button.innerHTML = originalLabel;
    exportingPDF = false; reset.disabled = false; aside.inert = false; updatePDFButtons();
  }
}));
fillFields();
invalidate();
