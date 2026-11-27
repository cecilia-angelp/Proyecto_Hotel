// Formularios y botones que usan la API con POST, PUT y DELETE
(function () {
    "use strict";

    function api() { return window.Aurora; }

    // Aviso de exito que llega en la URL (?ok=...) despues de guardar o eliminar
    function mostrarMensaje() {
        var params = new URLSearchParams(window.location.search);
        var ok = params.get("ok");
        if (!ok) { return; }
        if (api().aviso) { api().aviso(ok, "ok"); }
        params.delete("ok");
        var resto = params.toString();
        window.history.replaceState(null, "", window.location.pathname + (resto ? "?" + resto : ""));
    }

    function mostrarErrores(caja, lista) {
        if (!caja) { return; }
        var ul = caja.querySelector("ul");
        ul.textContent = "";
        lista.forEach(function (texto) {
            var li = document.createElement("li");
            li.textContent = texto;
            ul.appendChild(li);
        });
        caja.hidden = false;
        caja.scrollIntoView({ behavior: "smooth", block: "center" });
    }

    function textosDeError(resp) {
        var d = resp.datos || {};
        if (d.errores && d.errores.length) { return d.errores; }
        if (d.error) { return [d.error]; }
        return ["No se pudo completar la operación (código " + resp.status + ")."];
    }

    function recoger(form) {
        var numericos = (form.getAttribute("data-numericos") || "").split(",");
        var datos = {};
        Array.prototype.forEach.call(form.elements, function (el) {
            if (!el.name || el.disabled || el.type === "submit" || el.type === "button") { return; }
            if (el.type === "checkbox") { datos[el.name] = el.checked; return; }
            var valor = el.value;
            if (numericos.indexOf(el.name) !== -1 && /^\d+$/.test(valor)) { valor = Number(valor); }
            datos[el.name] = valor;
        });
        return datos;
    }

    // Suena la campanita y, un instante despues, se muestra la lista con el aviso
    function irA(destino, mensaje) {
        if (api().sonar) { api().sonar(); }
        setTimeout(function () {
            window.location.href = destino + "?ok=" + encodeURIComponent(mensaje || "Listo.");
        }, 450);
    }

    // POST (crear) o PUT (modificar)
    function iniciarFormulario(form) {
        var caja = document.getElementById("erroresForm");
        var boton = form.querySelector("[data-boton-guardar]");
        var enviando = false;
        form.addEventListener("submit", function (e) {
            e.preventDefault();
            if (enviando) { return; }
            if (!form.noValidate && !form.checkValidity()) { form.reportValidity(); return; }
            enviando = true;
            if (boton) { boton.disabled = true; }
            if (caja) { caja.hidden = true; }
            api().apiFetch(form.getAttribute("data-metodo"), form.getAttribute("data-api"), recoger(form))
                .then(function (resp) {
                    if (resp.ok) {
                        var datos = resp.datos || {};
                        if (form.hasAttribute("data-checkin") && datos.reserva && api().checkin) {
                            api().checkin(datos.reserva, form, form.getAttribute("data-destino"), datos.mensaje);
                        } else {
                            irA(form.getAttribute("data-destino"), datos.mensaje);
                        }
                        return;
                    }
                    mostrarErrores(caja, textosDeError(resp));
                    enviando = false;
                    if (boton) { boton.disabled = false; }
                })
                .catch(function () {
                    mostrarErrores(caja, ["No hay conexión con el servidor."]);
                    enviando = false;
                    if (boton) { boton.disabled = false; }
                });
        });
    }

    // DELETE
    function iniciarEliminar(boton) {
        var caja = document.getElementById("erroresForm");
        boton.addEventListener("click", function () {
            boton.disabled = true;
            if (caja) { caja.hidden = true; }
            api().apiFetch("DELETE", boton.getAttribute("data-api"))
                .then(function (resp) {
                    if (resp.ok) { irA(boton.getAttribute("data-destino"), resp.datos && resp.datos.mensaje); return; }
                    mostrarErrores(caja, textosDeError(resp));
                    boton.disabled = false;
                })
                .catch(function () {
                    mostrarErrores(caja, ["No hay conexión con el servidor."]);
                    boton.disabled = false;
                });
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        mostrarMensaje();
        Array.prototype.forEach.call(document.querySelectorAll("form[data-api]"), iniciarFormulario);
        Array.prototype.forEach.call(document.querySelectorAll("button[data-eliminar]"), iniciarEliminar);
    });
})();
