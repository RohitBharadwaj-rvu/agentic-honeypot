// app.js - Live Arena Logic

// State
let sessionID = localStorage.getItem('arena_session_id') || `sess-${Math.random().toString(36).substr(2, 9)}`;
localStorage.setItem('arena_session_id', sessionID);

// Default mode is 'voter' (Spectator). User can switch to 'tester'.
let mode = 'voter';
let userHash = localStorage.getItem('user_hash') || Math.random().toString(36);
localStorage.setItem('user_hash', userHash);

// DOM Elements
const msgContainer = document.getElementById('chat-container');
const inputArea = document.getElementById('input-area');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const headerTitle = document.querySelector('.header h1');
const toggleBtn = document.getElementById('toggle-mode-btn');

// Supabase
let supabase = null;
const SUPABASE_URL_DEFAULT = "https://enffvlctgfipttakqzzh.supabase.co";

function init() {
    // Mode UI Initialization
    updateModeUI();

    // Init Supabase
    let url = localStorage.getItem('supabase_url') || SUPABASE_URL_DEFAULT;
    let key = localStorage.getItem('supabase_key');

    if (url && key) {
        if (window.createClient) {
            supabase = window.createClient(url, key);
            console.log("Supabase connected");
            subscribeToMessages();
        } else {
            console.error("Supabase SDK not loaded");
        }
    } else {
        // Show modal or alert?
        console.log("Supabase key missing");
        // We will prompt user if they try to send, or just let them read instructions
    }
}

function updateModeUI() {
    // Remove old badges
    const existingBadge = document.querySelector('.badge');
    if (existingBadge) existingBadge.remove();

    const badge = document.createElement('span');
    badge.className = 'badge';

    if (mode === 'tester') {
        inputArea.classList.remove('hidden');
        toggleBtn.textContent = 'Switch to Spectator Mode';
        badge.textContent = 'TESTER';
    } else {
        inputArea.classList.add('hidden');
        toggleBtn.textContent = 'Switch to Tester Mode';
        badge.textContent = 'SPECTATOR';
    }

    headerTitle.appendChild(badge);
}

// Toggle Mode Event
if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
        mode = (mode === 'voter') ? 'tester' : 'voter';
        updateModeUI();
    });
}

// Realtime Subscription
async function subscribeToMessages() {
    if (!supabase) return;

    // Load initial history
    const { data, error } = await supabase
        .from('messages')
        .select('*')
        .order('timestamp', { ascending: true })
        .limit(50);

    if (data) {
        msgContainer.innerHTML = ''; // Clear sys msg
        data.forEach(renderMessage);
        scrollToBottom();
    }

    // Realtime subscription
    supabase
        .channel('arena-chat')
        .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'messages' }, payload => {
            renderMessage(payload.new);
            scrollToBottom();
        })
        .subscribe();
}

function renderMessage(msg) {
    // Check if duplicate (simple check based on ID)
    if (document.querySelector(`[data-id="${msg.id}"]`)) return;

    const div = document.createElement('div');
    div.dataset.id = msg.id;

    // Determine style
    const isBot = msg.is_bot;
    div.className = `message ${isBot ? 'bot-msg' : 'user-msg'}`;

    let senderName = msg.sender || 'Unknown';

    div.innerHTML = `
        <div class="msg-header">${senderName}</div>
        <div class="msg-content">${escapeHtml(msg.content)}</div>
    `;

    msgContainer.appendChild(div);
}

function scrollToBottom() {
    msgContainer.scrollTop = msgContainer.scrollHeight;
}

function escapeHtml(text) {
    if (!text) return '';
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Sending (Tester Only)
async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;
    if (!supabase) {
        alert("Please set Supabase Key first (Double-click header)");
        return;
    }

    // Optimistic UI? No, let's wait for Realtime to confirm echo
    // But we can clear input
    chatInput.value = '';

    // Send to DB
    const { error } = await supabase
        .from('messages')
        .insert({
            session_id: sessionID,
            content: text,
            sender: "Tester", // Or prompt for name
            is_bot: false,
            timestamp: new Date().toISOString()
        });

    if (error) {
        console.error("Send failed", error);
        alert("Failed to send: " + error.message);
    }
}

if (sendBtn) {
    sendBtn.addEventListener('click', sendMessage);
}
if (chatInput) {
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
}

// Settings Modal Logic
const modalEl = document.getElementById('config-modal');
const saveConfigBtn = document.getElementById('save-config-btn');
const closeConfigBtn = document.getElementById('close-config-btn');
const supabaseUrlInput = document.getElementById('supabase-url');
const supabaseKeyInput = document.getElementById('supabase-key');

document.querySelector('.header').addEventListener('dblclick', (e) => {
    if (e.target === toggleBtn) return;
    modalEl.classList.remove('hidden');
    supabaseUrlInput.value = localStorage.getItem('supabase_url') || SUPABASE_URL_DEFAULT;
    supabaseKeyInput.value = localStorage.getItem('supabase_key') || '';
});

saveConfigBtn.addEventListener('click', () => {
    localStorage.setItem('supabase_url', supabaseUrlInput.value);
    localStorage.setItem('supabase_key', supabaseKeyInput.value);
    location.reload();
});

closeConfigBtn.addEventListener('click', () => {
    modalEl.classList.add('hidden');
});

// Start
init();
