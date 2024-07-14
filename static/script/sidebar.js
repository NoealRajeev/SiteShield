const body = document.querySelector('body'),
        sidebar = body.querySelector('nav'),
        toggle = body.querySelector(".toggle"),
        searchBtn = body.querySelector(".search-box"),
        modeSwitch = body.querySelector(".toggle-switch"),
        modeText = body.querySelector(".mode-text");

        // Retrieve saved mode from localStorage
const savedMode = localStorage.getItem('mode');
if (savedMode) {
    body.classList.add(savedMode);
    modeText.innerText = savedMode === 'dark' ? 'Light mode' : 'Dark mode';
}

toggle.addEventListener("click" , () =>{
    sidebar.classList.toggle("close");
})

searchBtn.addEventListener("click" , () =>{
    sidebar.classList.remove("close");
})

// Event listener for mode switch
modeSwitch.addEventListener("click", () => {
    body.classList.toggle("dark");
    const currentMode = body.classList.contains("dark") ? "dark" : "light";
    modeText.innerText = currentMode === "dark" ? "Light mode" : "Dark mode";
    localStorage.setItem('mode', currentMode);
});