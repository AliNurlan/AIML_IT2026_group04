const $ = (selector) => document.querySelector(selector);
const form = $('#generator-form');
const promptInput = $('#prompt');
const generateButton = $('#generate');
const frame = $('#preview-frame');
const errorBox = $('#error');
const examples = {
  coffee: 'A warm and welcoming coffee shop website for an independent cafe called Sunday Brew. Include a hero, a menu with prices, opening hours, and a working button to view the menu. Use an earthy color palette.',
  portfolio: 'A minimal portfolio for an independent graphic designer named Alex. Include an introduction, three sample projects, an about section, and a contact button. Use an editorial style with soft colors.',
  habit: 'A cheerful habit tracker where I can add a habit, mark it completed, and see my progress. Use a calm green palette and make it work on mobile without any external services.'
};
let currentHtml = '';
let staticChecks = [];
let previewToken = '';
let previewTimer;

function switchTab(name) {
  document.querySelectorAll('[data-tab]').forEach((tab) => tab.setAttribute('aria-selected', String(tab.dataset.tab === name)));
  ['preview', 'code', 'checks'].forEach((panel) => { $(`#panel-${panel}`).hidden = panel !== name; });
}

document.querySelectorAll('[data-tab]').forEach((tab) => tab.addEventListener('click', () => switchTab(tab.dataset.tab)));
document.querySelectorAll('[data-example]').forEach((button) => button.addEventListener('click', () => {
  promptInput.value = examples[button.dataset.example];
  promptInput.dispatchEvent(new Event('input'));
  promptInput.focus();
}));
promptInput.addEventListener('input', () => { $('#character-count').textContent = promptInput.value.length.toLocaleString(); });

function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = !message;
}

function renderChecks(items) {
  const list = $('#checks-list');
  list.replaceChildren();
  $('#test-count').textContent = items.length;
  if (!items.length) {
    const empty = document.createElement('div');
    empty.className = 'checks-empty';
    empty.textContent = 'Checks will appear after you generate a website.';
    list.append(empty);
    return;
  }
  items.forEach((item) => {
    const row = document.createElement('div');
    row.className = `check-row ${item.status}`;
    const icon = document.createElement('span');
    icon.className = 'check-icon';
    icon.textContent = item.status === 'passed' ? '✓' : item.status === 'failed' ? '!' : '–';
    const text = document.createElement('div');
    const title = document.createElement('strong');
    title.textContent = `${item.name} · ${item.status}`;
    const detail = document.createElement('small');
    detail.textContent = item.detail;
    text.append(title, detail);
    row.append(icon, text);
    list.append(row);
  });
}

function previewSite(html) {
  clearTimeout(previewTimer);
  previewToken = crypto.randomUUID();
  const token = previewToken;
  const policy = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; font-src data:; connect-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'";
  const harness = `<meta http-equiv="Content-Security-Policy" content="${policy}"><script>(()=>{const token=${JSON.stringify(token)};const errors=[];addEventListener('error', e=>errors.push(String(e.message||'Resource error')));addEventListener('unhandledrejection',()=>errors.push('Unhandled promise rejection'));addEventListener('load',()=>setTimeout(()=>parent.postMessage({type:'canvas-check',token,errors:errors.slice(0,5),hasContent:!!document.body&&document.body.innerText.trim().length>0},'*'),350));})();<\/script>`;
  const instrumented = /<head(?:\s[^>]*)?>/i.test(html)
    ? html.replace(/<head(?:\s[^>]*)?>/i, (match) => match + harness)
    : harness + html;
  $('#empty-state').hidden = true;
  frame.hidden = false;
  frame.srcdoc = instrumented;
  renderChecks([...staticChecks, {name: 'Browser runtime', status: 'skipped', detail: 'Waiting for the preview to load.'}]);
  previewTimer = setTimeout(() => {
    if (previewToken === token) renderChecks([...staticChecks, {name: 'Browser runtime', status: 'failed', detail: 'Preview did not report readiness within 8 seconds.'}]);
  }, 8000);
}

window.addEventListener('message', (event) => {
  if (event.source !== frame.contentWindow || !event.data || event.data.type !== 'canvas-check' || event.data.token !== previewToken) return;
  clearTimeout(previewTimer);
  const errors = Array.isArray(event.data.errors) ? event.data.errors : ['Invalid preview result'];
  const content = event.data.hasContent === true;
  renderChecks([...staticChecks,
    {name: 'Browser runtime', status: errors.length ? 'failed' : 'passed', detail: errors.length ? errors.join('; ').slice(0, 300) : 'The preview loaded without a reported JavaScript error.'},
    {name: 'Visible text', status: content ? 'passed' : 'failed', detail: content ? 'The page contains text.' : 'No text was found in the page body.'}
  ]);
});

async function request(path, body) {
  const response = await fetch(path, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Something went wrong. Please try again.');
  return data;
}

function setBusy(busy) {
  generateButton.disabled = busy;
  $('#generate-label').textContent = busy ? 'Generating your website…' : 'Generate website';
  $('#loading').hidden = !busy;
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!form.reportValidity()) return;
  showError('');
  setBusy(true);
  switchTab('preview');
  try {
    const data = await request('/api/generate', {prompt: promptInput.value, model: $('#model').value});
    currentHtml = data.html;
    staticChecks = data.tests;
    $('#code-output').textContent = currentHtml;
    $('#address-label').textContent = (data.title || 'your-idea').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 40) + '.preview';
    $('#download').disabled = false;
    $('#test-button').disabled = false;
    previewSite(currentHtml);
  } catch (error) {
    showError(error.message);
  } finally {
    setBusy(false);
  }
});

$('#test-button').addEventListener('click', async () => {
  if (!currentHtml) return;
  showError('');
  $('#test-button').disabled = true;
  try {
    const result = await request('/api/validate', {html: currentHtml});
    staticChecks = result.tests;
    previewSite(currentHtml);
    switchTab('checks');
  } catch (error) {
    showError(error.message);
  } finally {
    $('#test-button').disabled = false;
  }
});

$('#download').addEventListener('click', () => {
  if (!currentHtml) return;
  const url = URL.createObjectURL(new Blob([currentHtml], {type: 'text/html;charset=utf-8'}));
  const link = document.createElement('a');
  link.href = url;
  link.download = 'index.html';
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});

$('#copy').addEventListener('click', async () => {
  if (!currentHtml) return;
  try {
    await navigator.clipboard.writeText(currentHtml);
    $('#copy').textContent = 'Copied!';
    setTimeout(() => { $('#copy').textContent = 'Copy code'; }, 1500);
  } catch {
    showError('Could not copy to the clipboard. You can select the code manually.');
  }
});
