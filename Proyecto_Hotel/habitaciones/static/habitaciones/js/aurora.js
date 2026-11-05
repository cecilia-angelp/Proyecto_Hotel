/* HOTEL AURORA · ambiente: música, sonidos, polvo flotante y puertas de transición.
   Todo es decorativo: si algo aquí falla, el sistema (login, CRUD, API) sigue funcionando. */
(function () {
    "use strict";

    // ---------- Utilidades seguras (el navegador puede bloquear el almacenamiento) ----------
    function lsGet(k) { try { return window.localStorage.getItem(k); } catch (e) { return null; } }
    function lsSet(k, v) { try { window.localStorage.setItem(k, v); } catch (e) { /* nada */ } }
    function ssGet(k) { try { return window.sessionStorage.getItem(k); } catch (e) { return null; } }
    function ssSet(k, v) { try { window.sessionStorage.setItem(k, v); } catch (e) { /* nada */ } }
    function ssDel(k) { try { window.sessionStorage.removeItem(k); } catch (e) { /* nada */ } }

    var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var isLogin = document.body.classList.contains("login-page");

    // ---------- Sonido ----------
    var bgm = document.getElementById("bgm");
    var toggle = document.getElementById("soundToggle");
    var MUSIC_VOLUME = 0.32;
    var muted = lsGet("aurora_muted") === "1";
    var unlocked = false;
    var ctx = null;                       // Web Audio (efectos sintetizados, sin archivos)
    var track = bgm ? (bgm.dataset.track || "hotel") : "hotel";
    var timeKey = "aurora_t_" + track;

    function paintToggle() {
        if (!toggle) return;
        toggle.classList.toggle("is-muted", muted);
        toggle.classList.toggle("is-waiting", !unlocked && !muted);
        toggle.setAttribute("aria-pressed", muted ? "true" : "false");
    }

    function fadeTo(target, ms) {
        if (!bgm) return;
        var start = bgm.volume, t0 = performance.now();
        (function step(now) {
            var p = Math.min(1, (now - t0) / ms);
            bgm.volume = Math.max(0, Math.min(1, start + (target - start) * p));
            if (p < 1) requestAnimationFrame(step);
        })(t0);
    }

    function restorePosition() {
        if (!bgm) return;
        var saved = parseFloat(ssGet(timeKey));
        if (!isFinite(saved) || saved < 1) return;
        var apply = function () {
            try {
                if (bgm.duration && saved < bgm.duration - 2 && Math.abs(bgm.currentTime - saved) > 1.5) {
                    bgm.currentTime = saved;
                }
            } catch (e) { /* algunos servidores no permiten saltar: se ignora */ }
        };
        if (bgm.readyState >= 1) apply(); else bgm.addEventListener("loadedmetadata", apply, { once: true });
        bgm.addEventListener("canplaythrough", apply, { once: true });
    }

    function playMusic() {
        if (!bgm || muted) return;
        bgm.volume = 0;
        var p = bgm.play();
        if (p && p.then) {
            p.then(function () { unlocked = true; paintToggle(); fadeTo(MUSIC_VOLUME, 1800); })
             .catch(function () { /* el navegador exige un clic primero: se reintenta con el primer gesto */ });
        }
    }

    function ensureContext() {
        var AC = window.AudioContext || window.webkitAudioContext;
        if (!AC) return;
        if (!ctx) { try { ctx = new AC(); } catch (e) { ctx = null; } }
        if (ctx && ctx.state === "suspended") { ctx.resume(); }
    }

    function unlock() {
        ensureContext();
        if (!unlocked && !muted) { playMusic(); }
        if (ctx && ctx.state === "running" && (unlocked || muted)) {
            ["pointerdown", "keydown", "touchstart"].forEach(function (ev) { document.removeEventListener(ev, unlock); });
        }
    }

    function savePosition() { if (bgm && bgm.currentTime > 0) ssSet(timeKey, String(bgm.currentTime)); }

    if (bgm) {
        bgm.volume = 0;
        restorePosition();
        playMusic();                                         // intento inmediato (a veces el navegador lo permite)
        ["pointerdown", "keydown", "touchstart"].forEach(function (ev) { document.addEventListener(ev, unlock, { passive: true }); });
        setInterval(savePosition, 1000);
        window.addEventListener("pagehide", savePosition);
        document.addEventListener("visibilitychange", function () {
            if (document.hidden) { bgm.pause(); } else if (unlocked && !muted) { bgm.play().catch(function () {}); }
        });
    }

    if (toggle) {
        toggle.addEventListener("click", function () {
            muted = !muted;
            lsSet("aurora_muted", muted ? "1" : "0");
            if (muted) { fadeTo(0, 300); setTimeout(function () { if (muted && bgm) bgm.pause(); }, 320); }
            else { ensureContext(); playMusic(); }
            paintToggle();
        });
    }
    paintToggle();

    // ---------- Efectos de sonido sintetizados ----------
    function canSfx() { return ctx && ctx.state === "running" && !muted; }

    function tick() {                       // roce suave al pasar el mouse sobre un botón
        if (!canSfx()) return;
        var t = ctx.currentTime;
        var o = ctx.createOscillator(), f = ctx.createBiquadFilter(), g = ctx.createGain();
        o.type = "triangle";
        o.frequency.setValueAtTime(540, t);
        o.frequency.exponentialRampToValueAtTime(250, t + 0.07);
        f.type = "lowpass"; f.frequency.value = 1500;
        g.gain.setValueAtTime(0.0001, t);
        g.gain.exponentialRampToValueAtTime(0.05, t + 0.006);
        g.gain.exponentialRampToValueAtTime(0.0001, t + 0.1);
        o.connect(f); f.connect(g); g.connect(ctx.destination);
        o.start(t); o.stop(t + 0.12);
    }

    function thump(at, strength) {          // un golpe de madera
        var t = at;
        var o = ctx.createOscillator(), g = ctx.createGain();
        o.type = "sine";
        o.frequency.setValueAtTime(130, t);
        o.frequency.exponentialRampToValueAtTime(48, t + 0.16);
        g.gain.setValueAtTime(0.0001, t);
        g.gain.exponentialRampToValueAtTime(strength, t + 0.008);
        g.gain.exponentialRampToValueAtTime(0.0001, t + 0.2);
        o.connect(g); g.connect(ctx.destination);
        o.start(t); o.stop(t + 0.22);

        var len = Math.floor(ctx.sampleRate * 0.05);
        var buf = ctx.createBuffer(1, len, ctx.sampleRate), d = buf.getChannelData(0);
        for (var i = 0; i < len; i++) { d[i] = (Math.random() * 2 - 1) * (1 - i / len); }
        var n = ctx.createBufferSource(); n.buffer = buf;
        var lp = ctx.createBiquadFilter(); lp.type = "lowpass"; lp.frequency.value = 520;
        var ng = ctx.createGain(); ng.gain.value = strength * 0.7;
        n.connect(lp); lp.connect(ng); ng.connect(ctx.destination);
        n.start(t);
    }

    function knock(times) {                 // toc, toc
        if (!canSfx()) return;
        var n = times || 2, t = ctx.currentTime + 0.01;
        for (var i = 0; i < n; i++) { thump(t + i * 0.16, 0.45); }
    }

    var HOVER_SELECTOR = "a.button, button, .nav-links a, .action, .brand, .text-link, .room-card, .stat-card, .door-card";
    var lastHover = null, lastTick = 0;
    document.addEventListener("mouseover", function (e) {
        var el = e.target.closest ? e.target.closest(HOVER_SELECTOR) : null;
        if (!el || el === lastHover) return;
        lastHover = el;
        var now = performance.now();
        if (now - lastTick > 70) { lastTick = now; tick(); }
    });
    document.addEventListener("mouseout", function (e) {
        if (lastHover && !lastHover.contains(e.relatedTarget)) { lastHover = null; }
    });
    document.addEventListener("pointerdown", function (e) {
        var el = e.target.closest ? e.target.closest("a.button, button.button, .login-btn, .nav-button, .action") : null;
        if (el && canSfx()) { thump(ctx.currentTime + 0.005, 0.28); }
    });

    // ---------- Puertas de transición: se cierran al entrar y se abren en el hotel ----------
    var doors = document.getElementById("doorTransition");
    var DOOR_FLAG = "aurora_door";

    if (isLogin) {
        ssDel(DOOR_FLAG);                   // si estás viendo el login, no hay entrada pendiente
        var form = document.getElementById("loginForm");
        if (form) {
            var sending = false;
            form.addEventListener("submit", function (e) {
                if (sending || reduceMotion || !doors || !form.checkValidity()) { return; }   // envío normal
                sending = true;
                e.preventDefault();
                try { ensureContext(); knock(2); } catch (err) { /* nada */ }
                ssSet(DOOR_FLAG, "1");
                doors.classList.add("is-active");
                void doors.offsetWidth;
                doors.classList.add("closing");
                var sent = false;
                function go() {
                    if (sent) return;
                    sent = true;
                    HTMLFormElement.prototype.submit.call(form);
                }
                setTimeout(go, 950);
                setTimeout(go, 2500);       // seguro anti-bloqueo: nunca se queda sin enviar
            });
        }
    } else if (doors && ssGet(DOOR_FLAG) === "1" && !reduceMotion) {
        ssDel(DOOR_FLAG);
        doors.classList.add("is-active", "start-closed");
        void doors.offsetWidth;
        requestAnimationFrame(function () {
            doors.classList.remove("start-closed");          // al soltar, las hojas se abren
            setTimeout(function () { doors.classList.remove("is-active"); }, 1100);
        });
    }

    // ---------- Polvo flotante en la luz ----------
    var canvas = document.getElementById("dustCanvas");
    if (canvas && canvas.getContext && !reduceMotion) {
        var c = canvas.getContext("2d");
        var dpr = Math.min(window.devicePixelRatio || 1, 1.5);
        var W = 0, H = 0, motes = [];
        var COUNT = window.innerWidth < 700 ? 28 : 64;

        function resize() {
            W = window.innerWidth; H = window.innerHeight;
            canvas.width = Math.floor(W * dpr); canvas.height = Math.floor(H * dpr);
            c.setTransform(dpr, 0, 0, dpr, 0, 0);
        }
        function spawn(randomY) {
            return {
                x: Math.random() * W,
                y: randomY ? Math.random() * H : H + 10,
                r: Math.random() * 1.7 + 0.4,
                vx: (Math.random() - 0.5) * 0.15,
                vy: -(Math.random() * 0.22 + 0.04),
                a: Math.random() * 0.5 + 0.12,
                tw: Math.random() * Math.PI * 2,
                ts: Math.random() * 0.02 + 0.006
            };
        }
        resize();
        for (var i = 0; i < COUNT; i++) { motes.push(spawn(true)); }
        window.addEventListener("resize", resize);

        var running = true;
        document.addEventListener("visibilitychange", function () {
            running = !document.hidden;
            if (running) requestAnimationFrame(frame);
        });
        function frame() {
            if (!running) return;
            c.clearRect(0, 0, W, H);
            for (var k = 0; k < motes.length; k++) {
                var m = motes[k];
                m.x += m.vx + Math.sin(m.tw) * 0.08; m.y += m.vy; m.tw += m.ts;
                if (m.y < -10 || m.x < -10 || m.x > W + 10) { motes[k] = spawn(false); continue; }
                var alpha = m.a * (0.55 + 0.45 * Math.sin(m.tw * 3));
                var grad = c.createRadialGradient(m.x, m.y, 0, m.x, m.y, m.r * 4);
                grad.addColorStop(0, "rgba(255,214,150," + alpha + ")");
                grad.addColorStop(1, "rgba(255,214,150,0)");
                c.fillStyle = grad;
                c.beginPath(); c.arc(m.x, m.y, m.r * 4, 0, Math.PI * 2); c.fill();
            }
            requestAnimationFrame(frame);
        }
        requestAnimationFrame(frame);
    }
})();
