import { app } from "../../scripts/app.js";

// Register the archive function directly in ComfyUI
app.registerExtension({
    name: "Archive Output Extension",
    settings: [
        {
            id: "archive_output.trigger",
            name: "Archive Output Files",
            type: "button",
            onClick: async () => {
                try {
                    console.log("📂 Archiving output files...");
                    window.pywebview.api.execute_archive().then((message) => {
                        alert(message);
                    });
                } catch (error) {
                    alert('Error archiving output files.');
                }
            },
            tooltip: "Click to archive all output files into dated folders."
        },
    ],
});
