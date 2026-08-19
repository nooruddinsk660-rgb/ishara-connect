/**
 * Dashboard client script. Two independent concerns on one file:
 *   1. Alert acknowledge buttons -- plain fetch(), works on every dashboard
 *      page regardless of whether a live Socket.IO connection exists (an
 *      alert on an already-ended session still needs to be acknowledgeable).
 *   2. Live feed -- Socket.IO, only set up when this page actually has
 *      somewhere to put live data (#live-feed on the home page, or a live
 *      .transcript-timeline on a session detail page). Guarded so this file
 *      never assumes socket.io's `io()` is even loaded.
 */
(function () {
    const csrfToken = (document.querySelector('meta[name="csrf-token"]') || {}).content || '';

    function getCsrf() { return csrfToken; }

    // --- 1. Acknowledge buttons (always wired, no socket dependency) ---
    function wireAckButtons(scope) {
        (scope || document).querySelectorAll('.ack-btn').forEach((btn) => {
            if (btn.dataset.wired) return;
            btn.dataset.wired = '1';
            btn.addEventListener('click', async () => {
                const alertId = btn.dataset.alertId;
                btn.disabled = true;
                btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
                try {
                    const res = await fetch(`/dashboard/alerts/${alertId}/acknowledge`, {
                        method: 'POST',
                        headers: { 'X-CSRFToken': getCsrf() },
                    });
                    if (!res.ok) throw new Error('request failed');
                    const data = await res.json();
                    markAcknowledged(alertId, data.acknowledged_by_name, data.acknowledged_at);
                } catch (e) {
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fa-solid fa-check"></i> Acknowledge';
                    alert('Could not acknowledge -- check your connection and try again.');
                }
            });
        });
    }

    function markAcknowledged(alertId, byName, atIso) {
        document.querySelectorAll(`[data-alert-id="${alertId}"]`).forEach((card) => {
            card.classList.add('ack-done');
            const btn = card.querySelector('.ack-btn');
            if (btn) btn.remove();
            const status = card.querySelector('.ack-status');
            if (status) status.textContent = `Acknowledged${byName ? ' by ' + byName : ''}`;
        });
        // On the home page, the whole banner card should disappear once acknowledged.
        const bannerCard = document.querySelector(`#alerts-banner [data-alert-id="${alertId}"]`);
        if (bannerCard) {
            bannerCard.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            bannerCard.style.opacity = '0';
            bannerCard.style.transform = 'translateX(20px)';
            setTimeout(() => bannerCard.remove(), 400);
        }
    }

    wireAckButtons(document);

    // --- 2. Live feed (Socket.IO, only if this page has one) ---
    const feedEl = document.getElementById('live-feed');
    const timelineEl = document.querySelector('.transcript-timeline');
    const statusEl = document.getElementById('monitor-status');
    const alertsBanner = document.getElementById('alerts-banner');
    const targetSessionId = window.ISHARA_SESSION_ID || null;
    const needsLiveFeed = typeof io !== 'undefined' && (feedEl || (timelineEl && targetSessionId));

    if (!needsLiveFeed) return;

    const socket = io('/dashboard');

    socket.on('connect', () => {
        socket.emit('dashboard_join');
        if (statusEl) { statusEl.textContent = 'live'; statusEl.classList.add('is-live'); }
    });

    socket.on('disconnect', () => {
        if (statusEl) { statusEl.textContent = 'reconnecting…'; statusEl.classList.remove('is-live'); }
    });

    function confBand(conf) {
        if (conf === null || conf === undefined) return 'low';
        if (conf >= 0.75) return 'high';
        if (conf >= 0.5) return 'mid';
        return 'low';
    }

    function fmtTime(iso) {
        try { return new Date(iso).toLocaleTimeString('en-GB', { hour12: false }); }
        catch (e) { return ''; }
    }

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str == null ? '' : String(str);
        return div.innerHTML;
    }

    // Short beep via Web Audio -- no audio file to ship or fail to load.
    // Two-tone so it reads as "alert" rather than a generic notification click.
    function playAlertBeep() {
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            [880, 660].forEach((freq, i) => {
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = 'sine';
                osc.frequency.value = freq;
                gain.gain.setValueAtTime(0.0001, ctx.currentTime + i * 0.18);
                gain.gain.exponentialRampToValueAtTime(0.2, ctx.currentTime + i * 0.18 + 0.02);
                gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + i * 0.18 + 0.16);
                osc.connect(gain).connect(ctx.destination);
                osc.start(ctx.currentTime + i * 0.18);
                osc.stop(ctx.currentTime + i * 0.18 + 0.17);
            });
        } catch (e) { /* Web Audio unavailable -- silently skip, banner still shows */ }
    }

    socket.on('new_transcript_event', (payload) => {
        if (feedEl) {
            const empty = feedEl.querySelector('.feed-empty');
            if (empty) empty.remove();
            const row = document.createElement('div');
            row.className = 'feed-line feed-line-new';
            row.dataset.conf = confBand(payload.confidence);
            row.innerHTML =
                `<span class="feed-ts">${fmtTime(payload.ts)}</span>` +
                `<span class="feed-dot"></span>` +
                `<span class="feed-phrase">${escapeHtml(payload.decoded_phrase)}</span>` +
                `<span class="feed-conf">${payload.confidence != null ? Math.round(payload.confidence * 100) + '%' : '—'}</span>`;
            feedEl.appendChild(row);
            feedEl.scrollTop = feedEl.scrollHeight;
            while (feedEl.children.length > 200) feedEl.removeChild(feedEl.firstChild);
            requestAnimationFrame(() => row.classList.add('feed-line-settled'));
        }
        if (timelineEl && targetSessionId && payload.session_id === targetSessionId) {
            const empty = timelineEl.querySelector('.feed-empty');
            if (empty) empty.remove();
            const row = document.createElement('div');
            row.className = 'timeline-row timeline-row-new';
            row.dataset.conf = confBand(payload.confidence);
            row.innerHTML =
                `<span class="timeline-ts">${fmtTime(payload.ts)}</span>` +
                `<span class="timeline-dot"></span>` +
                `<span class="timeline-phrase">${escapeHtml(payload.decoded_phrase)}</span>` +
                `<span class="timeline-conf">${payload.confidence != null ? Math.round(payload.confidence * 100) + '%' : '—'}</span>`;
            timelineEl.appendChild(row);
            requestAnimationFrame(() => row.classList.add('timeline-row-settled'));
        }
    });

    // Stage 3: emergency alerts arrive on their own event, independent of
    // which page/session is open -- any connected caregiver in the
    // institution should see it, not just someone looking at that session.
    socket.on('emergency_alert', (payload) => {
        playAlertBeep();
        document.title = '🚨 ALERT — ' + document.title.replace(/^🚨 ALERT — /, '');

        if (alertsBanner) {
            const card = document.createElement('div');
            card.className = `alert-card sev-${payload.severity} alert-card-new`;
            card.dataset.alertId = payload.id;
            card.innerHTML =
                `<div class="alert-icon"><i class="fa-solid fa-triangle-exclamation"></i></div>` +
                `<div class="alert-body">` +
                `<span class="alert-title">${payload.severity.toUpperCase()} — "${escapeHtml(payload.trigger_phrase)}" signed</span>` +
                `<span class="alert-meta">${fmtTime(payload.ts)} · <a href="/dashboard/sessions/${payload.session_id}">Session #${payload.session_id}</a></span>` +
                `</div>` +
                `<button class="ack-btn" data-alert-id="${payload.id}"><i class="fa-solid fa-check"></i> Acknowledge</button>`;
            alertsBanner.prepend(card);
            alertsBanner.classList.add('has-alerts');
            wireAckButtons(card);
            requestAnimationFrame(() => card.classList.add('alert-card-settled'));
        }
    });

    // Another caregiver (or this one, in another tab) acknowledged an alert --
    // reflect it everywhere live rather than leaving a stale "unacknowledged"
    // state up for anyone else watching.
    socket.on('alert_acknowledged', (payload) => {
        markAcknowledged(payload.id, payload.acknowledged_by_name, payload.acknowledged_at);
    });
})();