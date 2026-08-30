const chatLog = document.getElementById('chatLog');
const chatForm = document.getElementById('chatForm');
const messageInput = document.getElementById('messageInput');
const micBtn = document.getElementById('micBtn');
const speakToggle = document.getElementById('speakToggle');
const receiptToggle = document.getElementById('receiptToggle');
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const pendingBox = document.getElementById('pendingBox');
const pendingText = document.getElementById('pendingText');
const approveBtn = document.getElementById('approveBtn');
const rejectBtn = document.getElementById('rejectBtn');
const correctionInput = document.getElementById('correctionInput');
const correctBtn = document.getElementById('correctBtn');
const interpretation = document.getElementById('interpretation');
const receiptSummary = document.getElementById('receiptSummary');
const voiceSupport = document.getElementById('voiceSupport');

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;

function appendMessage(role, text, meta = '') {
  const item = document.createElement('div');
  item.className = `msg ${role}`;
  item.textContent = text;
  if (meta) {
    const small = document.createElement('span');
    small.className = 'meta';
    small.textContent = meta;
    item.appendChild(small);
  }
  chatLog.appendChild(item);
  chatLog.scrollTop = chatLog.scrollHeight;
}

function speak(text) {
  if (!speakToggle.checked || !('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 0.96;
  utterance.pitch = 1.02;
  window.speechSynthesis.speak(utterance);
}

async function postJSON(path, payload) {
  const response = await fetch(path, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload)
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `Request failed: ${response.status}`);
  return data;
}

async function sendText(text, mode = 'text', confidence = null, alternatives = []) {
  appendMessage('user', text, mode === 'voice' ? 'voice transcript' : 'typed');
  try {
    const data = await postJSON('/api/chat', {text, mode, confidence, alternatives});
    renderTurn(data);
  } catch (error) {
    appendMessage('assistant', `I could not process that: ${error.message}`);
  }
}

function renderTurn(data) {
  const turn = data.turn;
  appendMessage('assistant', data.assistant_text, `status: ${turn.status}, intent: ${turn.intent.kind}`);
  speak(data.assistant_text);
  updateInterpretation(turn, data.snapshot);
  pendingBox.classList.toggle('hidden', !data.needs_confirmation);
  if (data.needs_confirmation) pendingText.textContent = data.assistant_text;
}

function updateInterpretation(turn, snapshot) {
  interpretation.innerHTML = '';
  const pairs = [
    ['Heard', turn.transcript.text],
    ['Intent', turn.intent.kind],
    ['Status', turn.status],
    ['Confidence', `${Math.round(turn.intent.confidence * 100)}%`],
    ['Risk', turn.plan.risk],
    ['Policy', turn.policy.outcome],
    ['Brain route', turn.brain_packet ? turn.brain_packet.route.route : 'unavailable'],
    ['Brain status', turn.brain_packet ? turn.brain_packet.decision.status : 'unavailable'],
    ['LLM layer', turn.brain_packet && turn.brain_packet.llm ? turn.brain_packet.llm.provider_mode : 'unavailable'],
    ['LLM reason', turn.brain_packet && turn.brain_packet.llm ? turn.brain_packet.llm.reason : 'unavailable']
  ];
  for (const [label, value] of pairs) {
    const dt = document.createElement('dt');
    const dd = document.createElement('dd');
    dt.textContent = label;
    dd.textContent = value;
    interpretation.appendChild(dt);
    interpretation.appendChild(dd);
  }
  if (receiptToggle.checked) {
    receiptSummary.textContent = `${snapshot.receipt_count} receipt events, ${snapshot.memory_count} memory records, ${snapshot.local_action_count} local actions.`;
  }
}

chatForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const text = messageInput.value.trim();
  if (!text) return;
  messageInput.value = '';
  await sendText(text);
});

approveBtn.addEventListener('click', async () => {
  try { renderTurn(await postJSON('/api/confirm', {approved: true})); }
  catch (error) { appendMessage('assistant', error.message); }
});

rejectBtn.addEventListener('click', async () => {
  try { renderTurn(await postJSON('/api/confirm', {approved: false})); }
  catch (error) { appendMessage('assistant', error.message); }
});

correctBtn.addEventListener('click', async () => {
  const text = correctionInput.value.trim();
  if (!text) return;
  correctionInput.value = '';
  try { renderTurn(await postJSON('/api/correct', {text})); }
  catch (error) { appendMessage('assistant', error.message); }
});

function setupVoice() {
  if (!SpeechRecognition) {
    voiceSupport.textContent = 'This browser does not expose speech recognition. Type instead, or use Chrome/Edge.';
    micBtn.disabled = true;
    return;
  }
  recognition = new SpeechRecognition();
  recognition.lang = 'en-US';
  recognition.interimResults = false;
  recognition.maxAlternatives = 3;
  recognition.onstart = () => {
    micBtn.classList.add('listening');
    micBtn.textContent = '●';
    statusText.textContent = 'Listening...';
  };
  recognition.onend = () => {
    micBtn.classList.remove('listening');
    micBtn.textContent = '🎙';
    statusText.textContent = 'Ready';
  };
  recognition.onerror = (event) => {
    appendMessage('assistant', `Microphone recognition error: ${event.error}`);
  };
  recognition.onresult = async (event) => {
    const results = Array.from(event.results[0]);
    const transcript = results[0].transcript;
    const confidence = results[0].confidence || null;
    const alternatives = results.slice(1).map(item => item.transcript);
    await sendText(transcript, 'voice', confidence, alternatives);
  };
  voiceSupport.textContent = 'Voice input is available. Click the microphone, speak, then review what Gabriella heard.';
}

micBtn.addEventListener('click', () => {
  if (!recognition) return;
  recognition.start();
});

async function boot() {
  try {
    const health = await fetch('/api/health').then(r => r.json());
    statusDot.classList.add('ready');
    statusText.textContent = 'Ready';
    appendMessage('assistant', `${health.assistant} is ready. Brain: ${health.brain}. LLM layer: ${health.llm_layer}. Try: Hey Gabriella, set a timer for 5 minutes.`);
    setupVoice();
  } catch (error) {
    statusDot.classList.add('error');
    statusText.textContent = 'Backend unavailable';
  }
}

boot();
