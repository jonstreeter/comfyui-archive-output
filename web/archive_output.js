import { app } from "../../scripts/app.js";

// Register the archive function in ComfyUI settings
app.registerExtension({
    name: "Archive Output Extension",
    settings: [
        {
            id: "archive_output.trigger",
            name: "Archive Output Files",
            type: "button",
            onClick: async () => {
                try {
                    const response = await fetch('/archive-output', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' }
                    });
                    const data = await response.json();
                    alert(data.message);
                } catch (error) {
                    alert('Error archiving output files.');
                }
            },
            tooltip: "Click to archive all output files into dated folders."
        },
    ],
});
