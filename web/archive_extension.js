/**
 * ComfyUI Archive Output Extension
 * Adds archive and compression functionality to the ComfyUI Settings panel
 */

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

class ArchiveOutputExtension {
    constructor() {
        this.isArchiving = false;
        this.isCompressing = false;
    }

    /**
     * Execute the archive operation
     */
    async executeArchive() {
        if (this.isArchiving) {
            this.showCustomAlert("Archive operation is already in progress.", "Already Running");
            return;
        }

        this.isArchiving = true;

        try {
            // Show status message
            const statusElement = this.createStatusElement("Archiving files...");
            document.body.appendChild(statusElement);

            // Get settings from ComfyUI settings system
            const archiveFolderName = app.ui.settings.getSettingValue("Archive Output.Archive.FolderName", "Archive");
            const skipHiddenFiles = app.ui.settings.getSettingValue("Archive Output.Archive.SkipHiddenFiles", true);
            const skipExtensions = app.ui.settings.getSettingValue("Archive Output.Archive.SkipExtensions", ".py,.js,.bat,.sh,.json,.yaml,.yml");

            // Call API
            const response = await api.fetchApi("/archive/execute", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    archive_folder_name: archiveFolderName,
                    skip_hidden_files: skipHiddenFiles,
                    skip_extensions: skipExtensions
                })
            });

            const result = await response.json();

            // Remove status element
            statusElement.remove();

            if (result.success) {
                const message = `Moved: ${result.moved} files\n` +
                    `Skipped: ${result.skipped} files\n` +
                    `Errors: ${result.errors}\n` +
                    `Empty directories removed: ${result.removed_dirs}\n\n` +
                    `Location: ${result.archive_location}`;

                this.showCustomAlert(message, "Archive Complete");
            } else {
                this.showCustomAlert(result.error, "Archive Failed");
            }
        } catch (error) {
            console.error("[Archive Output] Error executing archive:", error);
            this.showCustomAlert(error.message, "Archive Error");
        } finally {
            this.isArchiving = false;
        }
    }

    /**
     * Execute the compression operation with progress tracking
     */
    async executeCompress() {
        if (this.isCompressing) {
            this.showCustomAlert("Compression operation is already in progress.", "Already Running");
            return;
        }

        this.isCompressing = true;
        let progressDialog = null;
        let progressInterval = null;
        let cancelled = false;

        try {
            // Get settings from ComfyUI settings system
            const targetFolder = app.ui.settings.getSettingValue("Archive Output.Compression.TargetFolder", "");
            const recursive = app.ui.settings.getSettingValue("Archive Output.Compression.Recursive", true);
            const quality = app.ui.settings.getSettingValue("Archive Output.Compression.Quality", 90);
            const format = app.ui.settings.getSettingValue("Archive Output.Compression.Format", "WEBP");
            const deleteOriginal = app.ui.settings.getSettingValue("Archive Output.Compression.DeleteOriginal", false);

            // Debug logging
            console.log("[Archive Output] Compression settings:", {
                targetFolder,
                recursive,
                quality,
                format,
                deleteOriginal
            });

            // Validate quality
            let qualityInt = parseInt(quality) || 90;
            if (qualityInt < 1 || qualityInt > 100) {
                this.showCustomAlert(`Invalid quality value: ${quality}. Using default: 90`, "Invalid Setting");
                qualityInt = 90;
            }

            // Build request body
            const requestBody = {
                quality: qualityInt,
                output_format: format,
                delete_original: deleteOriginal,
                recursive: recursive
            };

            // Add target directory if specified
            if (targetFolder && targetFolder.trim() !== "") {
                requestBody.target_directory = targetFolder.trim();
            }

            // Start compression
            const response = await api.fetchApi("/compress/execute", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(requestBody)
            });

            const startResult = await response.json();

            if (!startResult.success || !startResult.poll_progress) {
                this.showCustomAlert(startResult.error || "Unknown error", "Compression Failed");
                return;
            }

            // Create progress dialog
            progressDialog = this.createProgressDialog();
            document.body.appendChild(progressDialog);

            // Poll for progress
            progressInterval = setInterval(async () => {
                try {
                    const progressResponse = await api.fetchApi("/compress/progress");
                    const progress = await progressResponse.json();

                    if (!progress.success) {
                        clearInterval(progressInterval);
                        return;
                    }

                    // Update progress dialog
                    this.updateProgressDialog(progressDialog, progress);

                    // Check if complete
                    if (!progress.is_running && progress.current > 0) {
                        clearInterval(progressInterval);
                        progressDialog.remove();

                        // Show final results
                        this.showCompressionResults(progress, cancelled);
                    }
                } catch (error) {
                    console.error("[Archive Output] Error polling progress:", error);
                }
            }, 500); // Poll every 500ms

            // Setup cancel handler
            const cancelBtn = progressDialog.querySelector(".cancel-btn");
            cancelBtn.onclick = async () => {
                try {
                    await api.fetchApi("/compress/cancel", { method: "POST" });
                    cancelled = true;
                    cancelBtn.disabled = true;
                    cancelBtn.textContent = "Cancelling...";
                } catch (error) {
                    console.error("[Archive Output] Error cancelling:", error);
                }
            };

        } catch (error) {
            console.error("[Archive Output] Error executing compression:", error);
            this.showCustomAlert(error.message, "Compression Error");
            if (progressInterval) clearInterval(progressInterval);
            if (progressDialog) progressDialog.remove();
        } finally {
            this.isCompressing = false;
        }
    }

    /**
     * Create progress dialog with cancel button
     */
    createProgressDialog() {
        const dialog = document.createElement("div");
        dialog.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: #1e1e1e;
            color: #fff;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
            z-index: 10000;
            font-family: sans-serif;
            min-width: 400px;
            border: 2px solid #ff9f43;
        `;

        dialog.innerHTML = `
            <h3 style="margin: 0 0 20px 0; color: #ff9f43;">Compressing Images...</h3>
            <div class="progress-info" style="margin-bottom: 15px;">
                <div class="progress-text" style="margin-bottom: 5px;">Initializing...</div>
                <div class="progress-bar-container" style="background: #333; height: 20px; border-radius: 4px; overflow: hidden;">
                    <div class="progress-bar" style="background: linear-gradient(90deg, #ff9f43, #ffa94d); height: 100%; width: 0%; transition: width 0.3s;"></div>
                </div>
                <div class="progress-percent" style="margin-top: 5px; font-size: 14px; color: #aaa;">0%</div>
            </div>
            <div class="stats" style="margin-bottom: 20px; font-size: 14px; color: #ccc;">
                <div class="current-file" style="margin-bottom: 8px; color: #ff9f43;"></div>
                <div class="stats-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                    <div>Compressed: <span class="stat-compressed">0</span></div>
                    <div>Errors: <span class="stat-errors">0</span></div>
                    <div>Saved: <span class="stat-saved">0 MB</span></div>
                    <div>Progress: <span class="stat-progress">0/0</span></div>
                </div>
            </div>
            <button class="cancel-btn" style="
                width: 100%;
                padding: 10px;
                background: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
            ">Cancel</button>
        `;

        return dialog;
    }

    /**
     * Update progress dialog with current progress
     */
    updateProgressDialog(dialog, progress) {
        const progressBar = dialog.querySelector(".progress-bar");
        const progressText = dialog.querySelector(".progress-text");
        const progressPercent = dialog.querySelector(".progress-percent");
        const currentFile = dialog.querySelector(".current-file");
        const statCompressed = dialog.querySelector(".stat-compressed");
        const statErrors = dialog.querySelector(".stat-errors");
        const statSaved = dialog.querySelector(".stat-saved");
        const statProgress = dialog.querySelector(".stat-progress");

        // Update progress bar
        const percent = progress.percent || 0;
        progressBar.style.width = `${percent}%`;
        progressPercent.textContent = `${percent.toFixed(1)}%`;

        // Update text
        if (progress.cancel_requested) {
            progressText.textContent = "Cancelling...";
        } else if (progress.is_running) {
            progressText.textContent = `Processing image ${progress.current} of ${progress.total}`;
        } else {
            progressText.textContent = "Complete!";
        }

        // Update current file
        if (progress.current_file) {
            currentFile.textContent = `Current: ${progress.current_file}`;
        }

        // Update stats
        statCompressed.textContent = progress.compressed || 0;
        statErrors.textContent = progress.errors || 0;
        const savedMB = ((progress.savings_bytes || 0) / (1024 * 1024)).toFixed(2);
        statSaved.textContent = `${savedMB} MB (${(progress.savings_percent || 0).toFixed(1)}%)`;
        statProgress.textContent = `${progress.current}/${progress.total}`;
    }

    /**
     * Show final compression results
     */
    showCompressionResults(progress, cancelled) {
        const sizeMB = (size) => (size / (1024 * 1024)).toFixed(2);

        let message = cancelled ?
            `Compression Cancelled!\n\nPartial results:\n` :
            `Compression Complete!\n\n`;

        message += `Files compressed: ${progress.compressed}\n` +
            `Errors: ${progress.errors}\n\n` +
            `Space Savings:\n` +
            `  Before: ${sizeMB(progress.total_original_size)} MB\n` +
            `  After: ${sizeMB(progress.total_compressed_size)} MB\n` +
            `  Saved: ${sizeMB(progress.savings_bytes)} MB (${progress.savings_percent.toFixed(1)}%)\n\n` +
            `Metadata Preservation:\n` +
            `  Full workflow: ${progress.metadata_full} files\n` +
            `  Workflow only: ${progress.metadata_partial} files\n` +
            `  No metadata: ${progress.metadata_none} files\n\n` +
            `📌 To restore workflows from compressed images:\n` +
            `Install ComfyUI-Image-Saver extension:\n` +
            `https://github.com/alexopus/ComfyUI-Image-Saver`;

        this.showCustomAlert(message, cancelled ? "Compression Cancelled" : "Compression Complete");
    }

    /**
     * Show custom alert dialog with high z-index to appear above settings panel
     */
    showCustomAlert(message, title = "Alert") {
        // Create overlay
        const overlay = document.createElement("div");
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.7);
            z-index: 99999;
            display: flex;
            align-items: center;
            justify-content: center;
        `;

        // Create dialog
        const dialog = document.createElement("div");
        dialog.style.cssText = `
            background: #1e1e1e;
            color: #fff;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
            font-family: sans-serif;
            max-width: 600px;
            border: 2px solid #4a9eff;
        `;

        dialog.innerHTML = `
            <h3 style="margin: 0 0 20px 0; color: #4a9eff;">${title}</h3>
            <pre style="white-space: pre-wrap; margin: 0 0 20px 0; font-family: monospace; line-height: 1.6;">${message}</pre>
            <button class="ok-btn" style="
                width: 100%;
                padding: 10px;
                background: #4a9eff;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
            ">OK</button>
        `;

        overlay.appendChild(dialog);
        document.body.appendChild(overlay);

        // Close on button click or overlay click
        const closeDialog = () => overlay.remove();
        dialog.querySelector(".ok-btn").onclick = closeDialog;
        overlay.onclick = (e) => {
            if (e.target === overlay) closeDialog();
        };

        // Close on Escape key
        const handleEscape = (e) => {
            if (e.key === "Escape") {
                closeDialog();
                document.removeEventListener("keydown", handleEscape);
            }
        };
        document.addEventListener("keydown", handleEscape);
    }

    /**
     * Create a status element for showing progress
     */
    createStatusElement(message) {
        const element = document.createElement("div");
        element.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: #1e1e1e;
            color: #fff;
            padding: 20px 40px;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
            z-index: 10000;
            font-family: sans-serif;
            font-size: 16px;
            border: 2px solid #4a9eff;
        `;
        element.textContent = message;
        return element;
    }
}

// Create extension instance
const archiveExtension = new ArchiveOutputExtension();

// Define settings array with proper three-level structure
// Level 1: Archive Output (sidebar category - with space!)
// Level 2: Archive / Compression (section headers)
// Level 3: Setting name
const SETTINGS = [
    // ARCHIVE SECTION
    {
        id: "Archive Output.Archive.FolderName",
        name: "Archive folder name",
        type: "text",
        defaultValue: "Archive"
    },
    {
        id: "Archive Output.Archive.SkipHiddenFiles",
        name: "Skip hidden files",
        type: "boolean",
        defaultValue: true
    },
    {
        id: "Archive Output.Archive.SkipExtensions",
        name: "Skip file extensions",
        type: "text",
        defaultValue: ".py,.js,.bat,.sh,.json,.yaml,.yml"
    },
    {
        id: "Archive Output.Archive.ExecuteButton",
        name: "📦 Archive files",
        type: (name) => {
            const button = document.createElement("button");
            button.textContent = name;
            button.style.cssText = "padding: 8px 16px; background: #4a9eff; color: white; border: none; border-radius: 4px; cursor: pointer;";
            button.onclick = () => archiveExtension.executeArchive();
            return button;
        },
        defaultValue: ""
    },
    // COMPRESSION SECTION
    {
        id: "Archive Output.Compression.TargetFolder",
        name: "Compression target folder",
        type: "text",
        defaultValue: ""
    },
    {
        id: "Archive Output.Compression.Recursive",
        name: "Include subdirectories",
        type: "boolean",
        defaultValue: true
    },
    {
        id: "Archive Output.Compression.Quality",
        name: "Compression quality",
        type: "slider",
        defaultValue: 90,
        attrs: {
            min: 70,
            max: 100,
            step: 5
        }
    },
    {
        id: "Archive Output.Compression.Format",
        name: "Compression format",
        type: "combo",
        defaultValue: "WEBP",
        options: ["WEBP", "JPEG"]
    },
    {
        id: "Archive Output.Compression.DeleteOriginal",
        name: "⚠️ Delete original PNG",
        type: "boolean",
        defaultValue: false
    },
    {
        id: "Archive Output.Compression.ExecuteButton",
        name: "🗜️ Compress images",
        type: (name) => {
            const button = document.createElement("button");
            button.textContent = name;
            button.style.cssText = "padding: 8px 16px; background: #ff9f43; color: white; border: none; border-radius: 4px; cursor: pointer;";
            button.onclick = () => archiveExtension.executeCompress();
            return button;
        },
        defaultValue: ""
    }
];

// Register with ComfyUI
app.registerExtension({
    name: "Comfy.ArchiveOutput",
    settings: SETTINGS,

    async setup() {
        console.log("[Archive Output] Extension loaded");
    }
});
