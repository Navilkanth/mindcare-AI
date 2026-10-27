/**
 * MindCare AI — Main Chat Application (Streaming Edition)
 * Handles: SSE streaming chat, session management, UI state, breathing exercise
 */

// ─── Global Session State ──────────────────────────────────────────────────
window.mindcareSession = {
  sessionId: null,
  isTyping: false,
};

// ─── DOM References ────────────────────────────────────────────────────────
const messagesArea    = document.getElementById('messagesArea');
const messageInput    = document.getElementById('messageInput');
const sendBtn         = document.getElementById('sendBtn');
const typingIndicator = document.getElementById('typingIndicator');
const crisisBanner    = document.getElementById('crisisBanner');
const crisisBannerTxt = document.getElementById('crisisBannerText');
const crisisModal     = document.getElementById('crisisModal');
const crisisModalTxt  = document.getElementById('crisisModalText');
const charCount       = document.getElementById('charCount');
const newSessionBtn   = document.getElementById('newSessionBtn');
const closeCrisisBanner = document.getElementById('closeCrisisBanner');
const closeModal      = document.getElementById('closeModal');
const mobileSidebarBtn = document.getElementById('mobileSidebarBtn');
const sidebar         = document.getElementById('sidebar');

// ─── Initialise ────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  renderWelcome();
  bindEvents();
  initBreathing();
});

// ─── Welcome Screen ────────────────────────────────────────────────────────
function renderWelcome() {
  const prompts = [
    "I've been feeling anxious lately 😟",
    "I can't stop overthinking 💭",
    "I feel really lonely right now",
    "I need help managing stress",
    "I'm struggling with motivation",
  ];

  messagesArea.innerHTML = `
    <div class="welcome-msg">
      <div class="welcome-icon">🧠</div>
      <h2>Hello, I'm MindCare</h2>
      <p>Your compassionate AI mental health companion. I'm here to listen, support, and guide — without judgment, any time you need.</p>
      <div class="quick-prompts">
        ${prompts.map(p => `<button class="quick-prompt" data-prompt="${p.replace(/"/g, '&quot;')}">${p}</button>`).join('')}
      </div>
    </div>
  `;

  messagesArea.querySelectorAll('.quick-prompt').forEach(btn => {
    btn.addEventListener('click', () => sendQuickPrompt(btn.dataset.prompt));
  });
}

function sendQuickPrompt(text) {
  messageInput.value = text;
  messageInput.dispatchEvent(new Event('input'));
  handleSend();
}

// ─── Event Bindings ────────────────────────────────────────────────────────
function bindEvents() {
  sendBtn.addEventListener('click', handleSend);

  messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  });

  messageInput.addEventListener('input', () => {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
    const len = messageInput.value.length;
    charCount.textContent = `${len} / 4000`;
    sendBtn.disabled = len === 0 || window.mindcareSession.isTyping;
  });

  newSessionBtn?.addEventListener('click', () => {
    window.mindcareSession.sessionId = null;
    renderWelcome();
  });

  closeCrisisBanner?.addEventListener('click', () => {
    crisisBanner.style.display = 'none';
  });

  closeModal?.addEventListener('click', () => {
    crisisModal.style.display = 'none';
  });

  mobileSidebarBtn?.addEventListener('click', () => {
    sidebar?.classList.toggle('open');
  });
}

// ─── Send Message (SSE Streaming) ──────────────────────────────────────────
async function handleSend() {
  const text = messageInput.value.trim();
  if (!text || window.mindcareSession.isTyping) return;

  // Clear welcome screen on first message
  const welcome = messagesArea.querySelector('.welcome-msg');
  if (welcome) welcome.remove();

  // Append user message
  appendMessage('user', text);
  messageInput.value = '';
  messageInput.style.height = 'auto';
  charCount.textContent = '0 / 4000';
  sendBtn.disabled = true;

  // Show typing indicator
  setTyping(true);

  // Create an empty AI bubble that we'll stream into
  const aiBubble = createEmptyAIBubble();

  try {
    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: window.mindcareSession.sessionId,
        message: text,
      }),
    });

    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }

    // Hide typing indicator as soon as first token arrives
    let firstToken = true;

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Process complete SSE lines
      const lines = buffer.split('\n');
      buffer = lines.pop(); // Keep incomplete line in buffer

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const payload = JSON.parse(line.slice(6));

            if (payload.token) {
              if (firstToken) {
                setTyping(false);
                firstToken = false;
              }
              // Append token to the AI bubble in real-time
              appendTokenToBubble(aiBubble, payload.token);
              scrollToBottom();
            }
          } catch (e) {
            // Not valid JSON, skip
          }
        } else if (line.startsWith('event: done')) {
          // Next data line contains the done payload — handled on next iteration
        } else if (line.startsWith('event: crisis')) {
          // Next data line contains crisis info — handled on next iteration
        }

        // Handle crisis & done events from the data line
        if (line.startsWith('data: ') && line.includes('"type"')) {
          try {
            const payload = JSON.parse(line.slice(6));
            if (payload.type === 'crisis') {
              showCrisisAlert(payload.crisis_message || '');
            }
            if (payload.type === 'done') {
              window.mindcareSession.sessionId = payload.session_id;
              if (payload.is_crisis) {
                showCrisisAlert(payload.crisis_message || payload.full_reply);
              }
            }
          } catch (e) {
            // skip
          }
        }
      }
    }

    // Finalise the bubble (add timestamp)
    finaliseBubble(aiBubble);

  } catch (err) {
    // Fallback: try non-streaming endpoint
    console.warn('Streaming failed, trying fallback:', err.message);
    try {
      const fallbackResp = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: window.mindcareSession.sessionId,
          message: text,
        }),
      });
      const data = await fallbackResp.json();
      window.mindcareSession.sessionId = data.session_id;

      // Fill the bubble with the full response
      setBubbleContent(aiBubble, data.reply);
      finaliseBubble(aiBubble);

      if (data.is_crisis) {
        showCrisisAlert(data.crisis_message || data.reply);
      }
    } catch (fallbackErr) {
      setBubbleContent(aiBubble, `⚠️ I'm having trouble connecting right now. Please check that the server is running. (${fallbackErr.message})`);
      finaliseBubble(aiBubble);
    }
  } finally {
    setTyping(false);
    scrollToBottom();
  }
}

// ─── Streaming Bubble Helpers ──────────────────────────────────────────────

/** Create an empty AI message bubble and append it to the messages area. */
function createEmptyAIBubble() {
  const row = document.createElement('div');
  row.className = 'message-row ai-row';

  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble streaming-bubble';
  bubble.innerHTML = '';

  // Track raw text for proper formatting at the end
  bubble._rawText = '';

  row.innerHTML = `<div class="msg-avatar">🧠</div>`;
  const wrapper = document.createElement('div');
  wrapper.appendChild(bubble);
  row.appendChild(wrapper);

  messagesArea.appendChild(row);
  return bubble;
}

/** Append a token (text chunk) to the streaming bubble using smooth animation frame rendering. */
function appendTokenToBubble(bubble, token) {
  bubble._rawText = (bubble._rawText || '') + token;
  if (!bubble._renderPending) {
    bubble._renderPending = true;
    requestAnimationFrame(() => {
      bubble.innerHTML = formatMessage(bubble._rawText);
      bubble._renderPending = false;
    });
  }
}

/** Replace the entire bubble content. */
function setBubbleContent(bubble, text) {
  bubble._rawText = text;
  bubble.innerHTML = formatMessage(text);
}

/** Finalise the bubble: remove streaming class, add timestamp. */
function finaliseBubble(bubble) {
  bubble.classList.remove('streaming-bubble');
  bubble.innerHTML = formatMessage(bubble._rawText || '');
  const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const timeDiv = document.createElement('div');
  timeDiv.className = 'msg-time';
  timeDiv.textContent = now;
  bubble.parentElement.appendChild(timeDiv);
}

// ─── Append Message Bubble ─────────────────────────────────────────────────
function appendMessage(role, content) {
  const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const isUser = role === 'user';

  const row = document.createElement('div');
  row.className = `message-row ${isUser ? 'user-row' : 'ai-row'}`;

  row.innerHTML = `
    ${!isUser ? `<div class="msg-avatar">🧠</div>` : ''}
    <div>
      <div class="msg-bubble">${formatMessage(content)}</div>
      <div class="msg-time">${now}</div>
    </div>
    ${isUser ? `<div class="msg-avatar" style="background:var(--purple-dim)">👤</div>` : ''}
  `;

  messagesArea.appendChild(row);
  scrollToBottom();
}

// ─── Format Message (Enhanced Markdown & Clinical References) ──────────────
function formatMessage(text) {
  if (!text) return '';
  let formatted = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Markdown links: [Title](url)
  formatted = formatted.replace(
    /\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer" class="chat-link">$1 🔗</a>'
  );

  // Raw URLs (avoid double-wrapping href)
  formatted = formatted.replace(
    /(^|[^"'])(https?:\/\/[^\s<]+)/g,
    '$1<a href="$2" target="_blank" rel="noopener noreferrer" class="chat-link">$2</a>'
  );

  // Headings
  formatted = formatted.replace(/^### (.*$)/gim, '<h4 class="msg-heading">$1</h4>');
  formatted = formatted.replace(/^## (.*$)/gim, '<h3 class="msg-heading">$1</h3>');
  formatted = formatted.replace(/^# (.*$)/gim, '<h3 class="msg-heading">$1</h3>');

  // Bold & Italic
  formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');

  // Bullet items
  formatted = formatted.replace(/^[•\-\*]\s+(.*$)/gim, '<div class="msg-bullet">• $1</div>');

  // Line breaks
  formatted = formatted.replace(/\n/g, '<br>');

  return formatted;
}

// ─── Typing Indicator ──────────────────────────────────────────────────────
function setTyping(active) {
  window.mindcareSession.isTyping = active;
  if (typingIndicator) {
    if (active) {
      typingIndicator.style.display = 'flex';
      messagesArea.appendChild(typingIndicator);
      scrollToBottom();
    } else {
      typingIndicator.style.display = 'none';
    }
  }
  sendBtn.disabled = active;
  if (!active && messageInput.value.trim()) sendBtn.disabled = false;
}

// ─── Crisis Alert ──────────────────────────────────────────────────────────
function showCrisisAlert(message) {
  if (crisisBanner) {
    crisisBannerTxt.textContent = ' Please reach out to a crisis helpline immediately.';
    crisisBanner.style.display = 'flex';
  }
  if (crisisModal && crisisModalTxt) {
    crisisModalTxt.textContent = message;
    crisisModal.style.display = 'grid';
  }
}

// ─── Scroll ────────────────────────────────────────────────────────────────
function scrollToBottom() {
  messagesArea.scrollTop = messagesArea.scrollHeight;
}

// ─── Breathing Exercise ────────────────────────────────────────────────────
function initBreathing() {
  const breatheBtn      = document.getElementById('breatheBtn');
  const breathingCircle = document.getElementById('breathingCircle');
  const ring            = breathingCircle?.querySelector('.breathing-ring');
  const textEl          = document.getElementById('breathingText');

  if (!breatheBtn || !ring || !textEl) return;

  let running = false;
  let timer   = null;

  function toggleBreathing() {
    if (running) {
      clearTimeout(timer);
      running = false;
      ring.className = 'breathing-ring';
      void ring.offsetWidth;
      textEl.textContent = 'Tap to begin';
      breatheBtn.textContent = 'Start 4-7-8 Breathing';
    } else {
      running = true;
      breatheBtn.textContent = 'Stop';
      runCycle();
    }
  }

  breatheBtn.addEventListener('click', toggleBreathing);
  breathingCircle.addEventListener('click', toggleBreathing);

  function applyPhase(phaseClass, label, duration, next) {
    if (!running) return;
    ring.className = 'breathing-ring';
    void ring.offsetWidth;
    ring.className = `breathing-ring ${phaseClass}`;
    textEl.textContent = label;
    timer = setTimeout(next, duration);
  }

  function runCycle() {
    if (!running) return;
    applyPhase('inhale', '🌬 Inhale… 4s', 4000, () =>
      applyPhase('hold',   '🤐 Hold… 7s',   7000, () =>
        applyPhase('exhale', '💨 Exhale… 8s', 8000, runCycle)
      )
    );
  }
}
