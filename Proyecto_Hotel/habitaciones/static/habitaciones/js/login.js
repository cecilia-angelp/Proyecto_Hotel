// Login: POST /api/login/ -> el servidor responde con los tokens y los guarda en cookies
(function () {
    "use strict";

    var form = document.getElementById("loginForm");
    if (!form) { return; }
    var error = document.getElementById("loginError");
    var boton = form.querySelector("button[type=submit]");
    var enviando = false;

    function mostrarError(texto) {
        error.textContent = texto;
        error.hidden = false;
        error.style.animation = "none";
        void error.offsetWidth;
        error.style.animation = "";
    }

    function liberar() {
        enviando = false;
        boton.disabled = false;
    }

    form.addEventListener("submit", function (e) {
        e.preventDefault();
        if (enviando) { return; }
        if (!form.checkValidity()) { form.reportValidity(); return; }
        enviando = true;
        boton.disabled = true;
        error.hidden = true;
        var clave = document.getElementById("id_password");
        var cuerpo = { username: document.getElementById("id_username").value.trim(), password: clave.value };

        // la puerta se cierra apenas se aprieta el boton; la API decide si se puede entrar
        var puertas = new Promise(function (resolver) {
            if (window.AuroraDoors) { window.AuroraDoors.cerrar(resolver); } else { resolver(); }
        });

        function fallo(texto) {
            puertas.then(function () {
                if (window.AuroraDoors) { window.AuroraDoors.abrir(); }
                mostrarError(texto);
                clave.value = "";
                clave.focus();
                liberar();
            });
        }

        fetch("/api/login/", {
            method: "POST", credentials: "same-origin",
            headers: { "Content-Type": "application/json" }, body: JSON.stringify(cuerpo)
        }).then(function (r) {
            console.log("[API] POST /api/login/ -> " + r.status);
            return r.json().catch(function () { return {}; }).then(function (datos) {
                if (r.ok) {
                    puertas.then(function () { window.location.href = "/"; });
                    return;
                }
                fallo(datos.error || "No se pudo ingresar.");
            });
        }).catch(function () {
            fallo("No hay conexión con el servidor.");
        });
    });
})();
