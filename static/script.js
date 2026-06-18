document.addEventListener("DOMContentLoaded", () => {
    const menuButton = document.querySelector(".mobile-menu-btn");
    const navigation = document.querySelector("header nav");

    if (menuButton && navigation) {
        menuButton.addEventListener("click", () => {
            const open = navigation.classList.toggle("is-open");
            menuButton.setAttribute("aria-expanded", String(open));
            menuButton.textContent = open ? "✕" : "☰";
        });
    }

    const activeCount = document.getElementById("active-player-count");
    if (activeCount) {
        const refreshPlayers = async () => {
            try {
                const response = await fetch("/api/active-players");
                const data = await response.json();
                activeCount.textContent = data.count;
            } catch {
                activeCount.textContent = "0";
            }
        };
        refreshPlayers();
        window.setInterval(refreshPlayers, 15000);
    }
});
