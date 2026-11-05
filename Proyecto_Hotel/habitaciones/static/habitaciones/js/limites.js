/* Límites físicos de los formularios: no deja escribir de más ni caracteres no permitidos.
   (El servidor igual valida todo; esto solo ayuda a que el usuario no se equivoque.)
   Atributos usados en los <input>:
     data-solo-digitos      -> solo números (respeta maxlength, sin ceros a la izquierda)
     data-solo-letras       -> letras, espacios, guion y apóstrofe
     data-tipo-habitacion   -> letras, números, espacios y guion
     data-rut               -> dígitos, K, puntos y guion
     data-telefono          -> dígitos, + y espacios
     data-contador          -> muestra "n/máx" bajo el campo
*/
(function () {
    "use strict";

    var REGLAS = {
        "data-solo-digitos": /[^0-9]/g,
        "data-solo-letras": /[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ '\-]/g,
        "data-tipo-habitacion": /[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 \-]/g,
        "data-rut": /[^0-9kK.\-]/g,
        "data-telefono": /[^0-9+ ]/g
    };

    function limpiar(input) {
        var valor = input.value;
        Object.keys(REGLAS).forEach(function (attr) {
            if (input.hasAttribute(attr)) { valor = valor.replace(REGLAS[attr], ""); }
        });
        if (input.hasAttribute("data-solo-digitos")) { valor = valor.replace(/^0+(?=\d)/, ""); }
        if (input.hasAttribute("data-rut")) { valor = valor.toUpperCase(); }
        valor = valor.replace(/ {2,}/g, " ");
        var max = parseInt(input.getAttribute("maxlength"), 10);
        if (max > 0 && valor.length > max) { valor = valor.slice(0, max); }
        if (valor !== input.value) { input.value = valor; }
    }

    function actualizarContador(input, contador) {
        var max = parseInt(input.getAttribute("maxlength"), 10);
        contador.textContent = input.value.length + "/" + max;
        contador.classList.toggle("lleno", input.value.length >= max);
    }

    function iniciar(input) {
        limpiar(input);
        input.addEventListener("input", function () { limpiar(input); });
        input.addEventListener("blur", function () {
            if (input.hasAttribute("data-tipo-habitacion") || input.hasAttribute("data-solo-letras")) {
                input.value = input.value.trim();
            }
        });
        if (input.hasAttribute("data-solo-digitos")) {
            input.addEventListener("keydown", function (e) {
                if (e.key && e.key.length === 1 && !e.ctrlKey && !e.metaKey && !/[0-9]/.test(e.key)) {
                    e.preventDefault();
                }
            });
        }
        if (input.hasAttribute("data-contador")) {
            var contador = document.createElement("span");
            contador.className = "contador-caracteres";
            input.insertAdjacentElement("afterend", contador);
            actualizarContador(input, contador);
            input.addEventListener("input", function () { actualizarContador(input, contador); });
        }
    }

    document.querySelectorAll(
        "[data-solo-digitos],[data-solo-letras],[data-tipo-habitacion],[data-rut],[data-telefono],[data-contador]"
    ).forEach(iniciar);

    /* Fechas: la salida no puede ser anterior a la entrada */
    var entrada = document.getElementById("id_fecha_entrada");
    var salida = document.getElementById("id_fecha_salida");
    if (entrada && salida) {
        var ajustar = function () {
            if (entrada.value) {
                var d = new Date(entrada.value + "T00:00:00");
                d.setDate(d.getDate() + 1);
                salida.min = d.toISOString().slice(0, 10);
                if (salida.value && salida.value < salida.min) { salida.value = ""; }
            }
        };
        entrada.addEventListener("change", ajustar);
        ajustar();
    }
})();
