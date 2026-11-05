(function () {
    const secretButton = document.getElementById("secretButton");
    const overlay = document.getElementById("secretOverlay");
    const closeSecret = document.getElementById("closeSecret");

    function openSecret() {
        if (!overlay) return;
        overlay.classList.add("show");
        overlay.setAttribute("aria-hidden", "false");
        document.body.classList.add("no-scroll");
    }

    function closeSecretDoor() {
        if (!overlay) return;
        overlay.classList.remove("show");
        overlay.setAttribute("aria-hidden", "true");
        document.body.classList.remove("no-scroll");
    }

    secretButton?.addEventListener("click", openSecret);
    closeSecret?.addEventListener("click", closeSecretDoor);
    overlay?.addEventListener("click", function (event) {
        if (event.target === overlay) closeSecretDoor();
    });

    // Easter egg: Konami Code.
    const code = ["ArrowUp", "ArrowUp", "ArrowDown", "ArrowDown", "ArrowLeft", "ArrowRight", "ArrowLeft", "ArrowRight"];
    let progress = 0;

    document.addEventListener("keydown", function (event) {
        if (event.key === code[progress]) {
            progress += 1;
            if (progress === code.length) {
                openSecret();
                progress = 0;
            }
        } else {
            progress = event.key === code[0] ? 1 : 0;
        }
    });
})();
