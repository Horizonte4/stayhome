/**
 * Widget de chat con asistente IA.
 *
 * - Persiste session_id en localStorage para mantener la conversación
 *   entre páginas y entre visitas.
 * - Carga historial del backend al abrir el panel por primera vez.
 * - Para usuarios anónimos, redirige a login al hacer click.
 */
(function () {
    'use strict';

    const STORAGE_KEY = 'aichat_session_id';
    const ENDPOINT_MESSAGE = '/ai/message/';

    const widget = document.getElementById('aichat-widget');
    if (!widget) return;

    const toggleBtn = document.getElementById('aichat-toggle');
    const isAuthenticated = widget.dataset.authenticated === '1';
    const loginUrl = widget.dataset.loginUrl;
    const historyUrl = widget.dataset.historyUrl;

    // Para anónimos: el botón redirige a login. Nada más se monta.
    if (!isAuthenticated) {
        toggleBtn.addEventListener('click', () => {
            window.location.href = loginUrl;
        });
        return;
    }

    const closeBtn = document.getElementById('aichat-close');
    const panel = document.getElementById('aichat-panel');
    const form = document.getElementById('aichat-form');
    const input = document.getElementById('aichat-input');
    const messagesEl = document.getElementById('aichat-messages');
    const sendBtn = form.querySelector('.aichat-send');

    let historyLoaded = false;

    // ----- UI helpers ------------------------------------------------------

    function openPanel() {
        panel.classList.add('is-open');
        input.focus();
        if (!historyLoaded) loadHistory();
    }

    function closePanel() {
        panel.classList.remove('is-open');
    }

    function appendMessage(text, variant) {
        const div = document.createElement('div');
        div.className = `aichat-message aichat-message--${variant}`;
        div.textContent = text;
        messagesEl.appendChild(div);
        messagesEl.scrollTop = messagesEl.scrollHeight;
        return div;
    }

    function showTyping() {
        const div = document.createElement('div');
        div.className = 'aichat-message aichat-message--typing';
        div.textContent = '...';
        div.id = 'aichat-typing';
        messagesEl.appendChild(div);
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function hideTyping() {
        const t = document.getElementById('aichat-typing');
        if (t) t.remove();
    }

    function setSending(sending) {
        sendBtn.disabled = sending;
        input.disabled = sending;
    }

    // ----- Session & history ----------------------------------------------

    function getSessionId() {
        return localStorage.getItem(STORAGE_KEY) || null;
    }

    function setSessionId(id) {
        if (id) localStorage.setItem(STORAGE_KEY, id);
    }

    async function loadHistory() {
        historyLoaded = true;  // marcamos antes para no duplicar fetch
        const sid = getSessionId();
        if (!sid) return;

        try {
            const url = `${historyUrl}?session_id=${encodeURIComponent(sid)}`;
            const response = await fetch(url, { credentials: 'same-origin' });
            if (!response.ok) return;
            const data = await response.json();
            const messages = data.messages || [];
            if (messages.length === 0) return;

            // Borramos el mensaje de bienvenida solo si vamos a poner historial
            messagesEl.innerHTML = '';
            for (const m of messages) {
                appendMessage(m.content, m.role === 'user' ? 'user' : 'assistant');
            }
        } catch (err) {
            // historial es nice-to-have; si falla, mantenemos UI vacía sin error
            console.warn('No se pudo cargar el historial', err);
        }
    }

    // ----- Network ---------------------------------------------------------

    function getCsrfToken() {
        const inp = form.querySelector('input[name="csrfmiddlewaretoken"]');
        return inp ? inp.value : '';
    }

    async function sendMessage(text) {
        const response = await fetch(ENDPOINT_MESSAGE, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
            },
            credentials: 'same-origin',
            body: JSON.stringify({
                session_id: getSessionId(),
                message: text,
            }),
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            if (response.status === 404) localStorage.removeItem(STORAGE_KEY);
            throw new Error(data.error || 'Error desconocido');
        }
        return data;
    }

    // ----- Event handlers --------------------------------------------------

    toggleBtn.addEventListener('click', () => {
        if (panel.classList.contains('is-open')) closePanel();
        else openPanel();
    });

    closeBtn.addEventListener('click', closePanel);

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && panel.classList.contains('is-open')) {
            closePanel();
        }
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const text = input.value.trim();
        if (!text) return;

        appendMessage(text, 'user');
        input.value = '';
        setSending(true);
        showTyping();

        try {
            const data = await sendMessage(text);
            setSessionId(data.session_id);
            hideTyping();
            appendMessage(data.reply, 'assistant');
        } catch (err) {
            hideTyping();
            appendMessage(err.message, 'error');
        } finally {
            setSending(false);
            input.focus();
        }
    });
})();