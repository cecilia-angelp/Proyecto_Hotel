// Cliente de la API: envia el Access token y lo renueva con el Refresh cuando da 401
(function () {
    "use strict";

    var COOKIE_ACCESS = "access_token";
    var refrescando = null;

    function leerCookie(nombre) {
        var m = document.cookie.match(new RegExp("(?:^|; )" + nombre + "=([^;]*)"));
        return m ? decodeURIComponent(m[1]) : null;
    }

    // Muestra en la consola que verbo se uso y que codigo respondio la API
    function registrar(metodo, url, codigo) {
        if (window.console && console.log) { console.log("[API] " + metodo + " " + url + " -> " + codigo); }
    }

    function irAlLogin() {
        window.location.href = "/ingreso/?expirada=1";
    }

    // POST /api/refresh/ (el refresh token viaja en su cookie HttpOnly)
    function refrescar() {
        if (refrescando) { return refrescando; }
        refrescando = fetch("/api/refresh/", {
            method: "POST", credentials: "same-origin",
            headers: { "Content-Type": "application/json" }, body: "{}"
        }).then(function (r) {
            registrar("POST", "/api/refresh/", r.status);
            if (!r.ok) { return false; }
            return r.json().then(function () { return true; });
        }).catch(function () { return false; }).then(function (ok) {
            refrescando = null;
            return ok;
        });
        return refrescando;
    }

    // apiFetch("PUT", "/api/habitaciones/3/", {...}) -> {ok, status, datos}
    function apiFetch(metodo, url, cuerpo) {
        function intentar() {
            var cabeceras = { "Accept": "application/json" };
            var token = leerCookie(COOKIE_ACCESS);
            if (token) { cabeceras["Authorization"] = "Bearer " + token; }
            var opciones = { method: metodo, headers: cabeceras, credentials: "same-origin" };
            if (cuerpo !== undefined) {
                cabeceras["Content-Type"] = "application/json";
                opciones.body = JSON.stringify(cuerpo);
            }
            return fetch(url, opciones).then(function (r) { registrar(metodo, url, r.status); return r; });
        }
        return intentar().then(function (r) {
            if (r.status !== 401) { return r; }
            // Access ausente, expirado o invalido: se intenta renovar y repetir una vez
            return refrescar().then(function (ok) {
                if (!ok) { irAlLogin(); return r; }
                return intentar().then(function (r2) { if (r2.status === 401) { irAlLogin(); } return r2; });
            });
        }).then(function (r) {
            return r.json().catch(function () { return null; }).then(function (datos) {
                return { ok: r.ok, status: r.status, datos: datos };
            });
        });
    }

    // Boton "Salir": POST /api/logout/ revoca la sesion y borra las cookies
    function salir() {
        var cabeceras = {};
        var token = leerCookie(COOKIE_ACCESS);
        if (token) { cabeceras["Authorization"] = "Bearer " + token; }
        var llamada = fetch("/api/logout/", { method: "POST", headers: cabeceras, credentials: "same-origin" })
            .then(function (r) { registrar("POST", "/api/logout/", r.status); })
            .catch(function () {});
        // las puertas se cierran mientras la API revoca la sesion
        var puertas = new Promise(function (resolver) {
            if (window.AuroraDoors) { window.AuroraDoors.cerrar(resolver); } else { resolver(); }
        });
        return Promise.all([llamada, puertas]).then(function () { window.location.href = "/ingreso/"; });
    }

    document.addEventListener("DOMContentLoaded", function () {
        var btnSalir = document.getElementById("btnSalir");
        if (btnSalir) { btnSalir.addEventListener("click", function () { btnSalir.disabled = true; salir(); }); }
    });

    window.Aurora = { apiFetch: apiFetch, leerCookie: leerCookie, registrar: registrar,
                      refrescar: refrescar, irAlLogin: irAlLogin };
})();
