async function archiveOutputFiles() {
    const response = await fetch('/archive-output', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    });

    const data = await response.json();
    alert(data.message);  // Show a pop-up with the result
}

// Wait for the UI to load, then add the button
window.addEventListener("DOMContentLoaded", () => {
    const settingsPanel = document.querySelector("#settings-panel");  // Find the settings panel
    if (!settingsPanel) return;

    const archiveButton = document.createElement("button");
    archiveButton.innerText = "Archive Output Files";
    archiveButton.style.marginTop = "10px";
    archiveButton.style.padding = "10px";
    archiveButton.style.cursor = "pointer";
    archiveButton.onclick = archiveOutputFiles;

    settingsPanel.appendChild(archiveButton);
});
