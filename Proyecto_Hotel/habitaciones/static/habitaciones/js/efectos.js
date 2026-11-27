// Efectos de interfaz: contador de sesion, avisos y tarjeta de check-in
(function () {
    "use strict";

    var A = window.Aurora || {};
    var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function sonar() {
        try { if (window.AuroraSfx) { window.AuroraSfx.asegurar(); window.AuroraSfx.campana(); } } catch (e) {}
    }

    // Avisos que se deslizan (reemplazan al cuadro fijo)
    function aviso(texto, tipo) {
        var caja = document.getElementById("toasts");
        if (!caja) { return; }
        var t = document.createElement("div");
        t.className = "toast " + (tipo === "error" ? "toast-error" : "toast-ok");
        t.setAttribute("role", "status");
        var icono = document.createElement("span");
        icono.className = "toast-icon";
        icono.textContent = tipo === "error" ? "!" : "✓";
        var msg = document.createElement("span");
        msg.textContent = String(texto).slice(0, 160);   // textContent: nunca se interpreta como HTML
        t.appendChild(icono); t.appendChild(msg);
        caja.appendChild(t);
        function quitar() {
            if (!t.parentNode) { return; }
            t.classList.add("saliendo");
            setTimeout(function () { if (t.parentNode) { t.parentNode.removeChild(t); } }, 350);
        }
        t.addEventListener("click", quitar);
        setTimeout(quitar, 4800);
    }

    // Contador de sesion: lee el vencimiento (exp) del Access token que esta en la cookie.
    // Cuando llega a cero llama a /api/refresh/ y el contador vuelve a empezar.
    function vencimientoAccess() {
        var token = A.leerCookie ? A.leerCookie("access_token") : null;
        if (!token) { return null; }
        try {
            var carga = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
            var datos = JSON.parse(atob(carga + "===".slice((carga.length + 3) % 4)));
            return datos.exp ? datos.exp * 1000 : null;
        } catch (e) { return null; }
    }

    function iniciarContador() {
        var caja = document.getElementById("sessionTimer");
        if (!caja) { return; }
        var texto = caja.querySelector(".timer-text");
        var renovando = false;

        function pintar(ms) {
            var seg = Math.max(0, Math.round(ms / 1000));
            var m = Math.floor(seg / 60), s = seg % 60;
            texto.textContent = (m < 10 ? "0" : "") + m + ":" + (s < 10 ? "0" : "") + s;
            caja.classList.toggle("timer-low", seg <= 30);
        }

        function renovar() {
            if (renovando || !A.refrescar) { return; }
            renovando = true;
            caja.classList.add("timer-renewing");
            A.refrescar().then(function (ok) {
                renovando = false;
                caja.classList.remove("timer-renewing");
                if (!ok) { if (A.irAlLogin) { A.irAlLogin(); } return; }
                tic();
                caja.classList.add("timer-renewed");
                setTimeout(function () { caja.classList.remove("timer-renewed"); }, 1500);
                aviso("Sesión renovada: nuevo Access token.", "ok");
                sonar();
            });
        }

        function tic() {
            var exp = vencimientoAccess();
            if (exp === null) { texto.textContent = "--:--"; return; }
            var resta = exp - Date.now();
            if (resta <= 0) { pintar(0); renovar(); return; }
            pintar(resta);
        }
        tic();
        setInterval(tic, 1000);
        document.addEventListener("visibilitychange", function () { if (!document.hidden) { tic(); } });
    }

    // Tarjeta de check-in (al crear una reserva)
    function dinero(n) {
        try { return "$" + new Intl.NumberFormat("es-CL").format(n); } catch (e) { return "$" + n; }
    }
    function fecha(iso) {
        var p = String(iso).split("-");
        return p.length === 3 ? p[2] + "/" + p[1] + "/" + p[0] : iso;
    }
    function textoSelect(form, nombre) {
        var el = form.elements[nombre];
        return el && el.selectedOptions && el.selectedOptions[0] ? el.selectedOptions[0].textContent.trim() : "";
    }
    function fila(etiqueta, valor) {
        var f = document.createElement("div");
        f.className = "keycard-row";
        var a = document.createElement("span"); a.textContent = etiqueta;
        var b = document.createElement("strong"); b.textContent = valor;
        f.appendChild(a); f.appendChild(b);
        return f;
    }

    function checkin(reserva, form, destino, mensaje) {
        var capa = document.createElement("div");
        capa.className = "checkin-overlay";
        capa.setAttribute("role", "dialog");
        capa.setAttribute("aria-modal", "true");
        capa.setAttribute("aria-label", "Tarjeta de check-in");

        var tarjeta = document.createElement("div");
        tarjeta.className = "keycard";
        var marca = document.createElement("p"); marca.className = "keycard-brand"; marca.textContent = "HOTEL AURORA";
        var titulo = document.createElement("h2"); titulo.textContent = "Reserva confirmada";
        var banda = document.createElement("div"); banda.className = "keycard-stripe";
        tarjeta.appendChild(marca); tarjeta.appendChild(titulo); tarjeta.appendChild(banda);
        tarjeta.appendChild(fila("Reserva N°", "#" + reserva.id));
        tarjeta.appendChild(fila("Huésped", textoSelect(form, "huesped")));
        tarjeta.appendChild(fila("Habitación", textoSelect(form, "habitacion")));
        tarjeta.appendChild(fila("Entrada", fecha(reserva.fecha_entrada)));
        tarjeta.appendChild(fila("Salida", fecha(reserva.fecha_salida)));
        tarjeta.appendChild(fila("Noches", String(reserva.noches)));
        tarjeta.appendChild(fila("Personas", String(reserva.personas)));
        var total = fila("Total", dinero(reserva.total)); total.classList.add("keycard-total");
        tarjeta.appendChild(total);
        var boton = document.createElement("button");
        boton.type = "button"; boton.className = "button primary keycard-btn"; boton.textContent = "Ver mis reservas";
        tarjeta.appendChild(boton);
        capa.appendChild(tarjeta);
        document.body.appendChild(capa);
        requestAnimationFrame(function () { capa.classList.add("visible"); });
        sonar();
        if (window.AuroraSfx) { setTimeout(function () { try { window.AuroraSfx.golpe(1); } catch (e) {} }, 350); }

        var ido = false;
        function seguir() {
            if (ido) { return; }
            ido = true;
            window.location.href = destino + "?ok=" + encodeURIComponent(mensaje || "Reserva creada.");
        }
        boton.addEventListener("click", seguir);
        capa.addEventListener("click", function (e) { if (e.target === capa) { seguir(); } });
        document.addEventListener("keydown", function (e) { if (e.key === "Escape") { seguir(); } });
        boton.focus();
    }

    A.aviso = aviso;
    A.sonar = sonar;
    A.checkin = checkin;
    window.Aurora = A;

    document.addEventListener("DOMContentLoaded", function () {
        iniciarContador();
        // vista Puertas / Tabla de habitaciones
        var botones = document.querySelectorAll("[data-vista]");
        Array.prototype.forEach.call(botones, function (b) {
            b.addEventListener("click", function () {
                var vista = b.getAttribute("data-vista");
                Array.prototype.forEach.call(document.querySelectorAll("[data-panel-vista]"), function (p) {
                    p.hidden = p.getAttribute("data-panel-vista") !== vista;
                });
                Array.prototype.forEach.call(botones, function (x) {
                    x.classList.toggle("activo", x === b);
                    x.setAttribute("aria-pressed", x === b ? "true" : "false");
                });
            });
        });
    });
})();
