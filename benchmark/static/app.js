// app.js - Local Benchmark Arena UI Logic

// State
let numVoters = 2;
let currentTurn = -1;
let responses = [];
let voterVotes = {}; // {voterID: alias}

// DOM Elements
const setupScreen = document.getElementById('setup-screen');
const arenaScreen = document.getElementById('arena-screen');
const resultsScreen = document.getElementById('results-screen');
const voterCountInput = document.getElementById('voter-count');
const startBtn = document.getElementById('start-btn');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const responsesGrid = document.getElementById('responses-grid');
const voterPanels = document.getElementById('voter-panels');
const turnNum = document.getElementById('turn-num');
const voteStatus = document.getElementById('vote-status');
const nextBtn = document.getElementById('next-btn');
const finishBtn = document.getElementById('finish-btn');
const resultsContent = document.getElementById('results-content');
const restartBtn = document.getElementById('restart-btn');

// Screen Switching
function showScreen(screen) {
    [setupScreen, arenaScreen, resultsScreen].forEach(s => s.classList.remove('active'));
    screen.classList.add('active');
}

// Setup
startBtn.addEventListener('click', async () => {
    numVoters = parseInt(voterCountInput.value) || 2;

    const res = await fetch('/api/setup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ num_voters: numVoters })
    });

    const data = await res.json();

    if (data.num_contestants === 0) {
        alert('No contestants configured! Please edit benchmark/benchmark_config.json');
        return;
    }

    currentTurn = 0;
    turnNum.textContent = '1';
    showScreen(arenaScreen);
    renderVoterPanels();
});

// Render Voter Panels
function renderVoterPanels() {
    voterPanels.innerHTML = '';
    voterVotes = {};

    for (let i = 1; i <= numVoters; i++) {
        const panel = document.createElement('div');
        panel.className = 'voter-panel';
        panel.id = `voter-${i}`;
        panel.innerHTML = `
            <h4>Voter ${i}</h4>
            <div class="vote-buttons" id="vote-buttons-${i}">
                <p style="color: var(--text-secondary); font-size: 0.9rem;">Waiting for responses...</p>
            </div>
        `;
        voterPanels.appendChild(panel);
    }
}

// Send Message
sendBtn.addEventListener('click', sendMessage);
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    // Show loading
    sendBtn.disabled = true;
    sendBtn.textContent = 'Generating...';
    responsesGrid.innerHTML = '<p style="text-align:center; color: var(--text-secondary);">Agents are thinking...</p>';

    try {
        const res = await fetch('/api/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });

        const data = await res.json();
        responses = data.responses;
        currentTurn = data.turn;
        turnNum.textContent = currentTurn + 1;

        // Render responses
        renderResponses();

        // Update voter panels with vote buttons
        updateVoterButtons();

        // Reset vote state
        voterVotes = {};
        updateVoteStatus();

        // Reset next button
        nextBtn.disabled = true;

    } catch (e) {
        alert('Error: ' + e.message);
    }

    sendBtn.disabled = false;
    sendBtn.textContent = 'Send';
    messageInput.value = '';
}

// Render Responses
function renderResponses() {
    responsesGrid.innerHTML = '';

    responses.forEach(resp => {
        const card = document.createElement('div');
        card.className = 'response-card';
        card.innerHTML = `
            <h3>${resp.alias}</h3>
            <p>${escapeHtml(resp.reply)}</p>
        `;
        responsesGrid.appendChild(card);
    });
}

// Update Voter Buttons
function updateVoterButtons() {
    for (let i = 1; i <= numVoters; i++) {
        const container = document.getElementById(`vote-buttons-${i}`);
        container.innerHTML = '';

        responses.forEach(resp => {
            const btn = document.createElement('button');
            btn.className = 'vote-btn';
            btn.textContent = resp.alias;
            btn.onclick = () => castVote(i, resp.alias, btn);
            container.appendChild(btn);
        });
    }
}

// Cast Vote
async function castVote(voterId, alias, btnElement) {
    // Disable all buttons for this voter
    const container = document.getElementById(`vote-buttons-${voterId}`);
    container.querySelectorAll('.vote-btn').forEach(b => b.disabled = true);
    btnElement.classList.add('selected');

    try {
        const res = await fetch('/api/vote', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ voter_id: voterId, agent_alias: alias })
        });

        const data = await res.json();
        voterVotes[voterId] = alias;

        updateVoteStatus();

        if (data.all_voted) {
            nextBtn.disabled = false;
            voteStatus.textContent = 'All voted! Ready for next turn.';
            voteStatus.style.background = 'var(--success)';
            voteStatus.style.color = '#000';
        }

    } catch (e) {
        console.error(e);
    }
}

// Update Vote Status
function updateVoteStatus() {
    const count = Object.keys(voterVotes).length;
    voteStatus.textContent = `${count}/${numVoters} votes`;
    voteStatus.style.background = 'var(--accent-primary)';
    voteStatus.style.color = 'white';
}

// Next Turn
nextBtn.addEventListener('click', () => {
    // Reset for next turn
    responsesGrid.innerHTML = '<p style="text-align:center; color: var(--text-secondary);">Send a message to start the next turn.</p>';
    renderVoterPanels();
    nextBtn.disabled = true;
    voteStatus.textContent = 'Waiting for message...';
});

// Finish
finishBtn.addEventListener('click', async () => {
    const res = await fetch('/api/results');
    const data = await res.json();

    // Render results
    resultsContent.innerHTML = `
        <p style="text-align:center; margin-bottom: 1.5rem;">
            ${data.total_turns} turns • ${data.total_votes} total votes
        </p>
    `;

    data.results.forEach((r, i) => {
        const row = document.createElement('div');
        row.className = 'result-row' + (i === 0 ? ' winner' : '');
        row.innerHTML = `
            <span class="result-name">${i === 0 ? '🏆 ' : ''}${r.name}</span>
            <span class="result-votes">${r.votes} votes</span>
        `;
        resultsContent.appendChild(row);
    });

    showScreen(resultsScreen);
});

// Restart
restartBtn.addEventListener('click', () => {
    showScreen(setupScreen);
});

// Utility
function escapeHtml(text) {
    if (!text) return '';
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
