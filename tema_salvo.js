
document.addEventListener("DOMContentLoaded", () => {
    const theme = localStorage.getItem("theme") || "light";
    document.documentElement.setAttribute("data-theme", theme);

    document.getElementById("toggleThemeBtn").addEventListener("click", () => {
        const current = document.documentElement.getAttribute("data-theme");
        const newTheme = current === "dark" ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", newTheme);
        localStorage.setItem("theme", newTheme);
    });
});
