# ComfyUI Archive Output Node

A custom node for ComfyUI that automatically archives output files into date-structured folders.

## Features

- **Date-based organization**: Files are organized by their modification date (YYYY-MM-DD)
- **Structure preservation**: Maintains original subdirectory structure within archives
- **Flexible filtering**: Skip hidden files and specific file extensions
- **Automatic cleanup**: Removes empty directories after archiving
- **Workflow integration**: Accepts any input type as a trigger for easy workflow integration
- **Interruption support**: Respects ComfyUI's workflow interruption signals

## Installation

### Via ComfyUI Manager (Recommended)
1. Open ComfyUI Manager
2. Search for "Archive Output"
3. Click Install

### Manual Installation
1. Navigate to your ComfyUI custom nodes directory:
   ```bash
   cd ComfyUI/custom_nodes
   ```

2. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/comfyui-archive-output.git
   ```

3. Restart ComfyUI

## Usage

### Node Inputs

**Required:**
- `trigger`: Any type - Connect any node output to trigger the archive process

**Optional:**
- `enabled`: Boolean (default: True) - Enable/disable archiving
- `archive_folder_name`: String (default: "Archive") - Name of the archive folder
- `skip_hidden_files`: Boolean (default: True) - Skip files starting with `.`
- `skip_extensions`: String (default: ".py,.js,.bat,.sh,.json,.yaml,.yml") - Comma-separated list of file extensions to skip

### Node Outputs

- `status`: String - Summary of the archive operation (files moved, skipped, errors)

### Example Workflow

1. Add the "Archive Output" node to your workflow
2. Connect any node's output to the trigger input (e.g., the output from a Save Image node)
3. Configure optional parameters as needed
4. Run your workflow

The node will move files from your output directory into a structured archive:

```
output/
  Archive/
    2025-01-15/
      image_001.png
      image_002.png
    2025-01-16/
      subfolder/
        image_003.png
```

## Configuration

### Skip Extensions

You can customize which file types to skip during archiving. By default, these extensions are skipped:
- `.py` - Python files
- `.js` - JavaScript files
- `.bat` - Batch files
- `.sh` - Shell scripts
- `.json` - JSON files
- `.yaml`, `.yml` - YAML files

To modify, edit the `skip_extensions` parameter with a comma-separated list.

### Archive Folder Location

The archive folder is created inside your ComfyUI output directory. You can customize the folder name using the `archive_folder_name` parameter.

## Notes

- Files are **moved** (not copied) to the archive
- If a file with the same name already exists in the archive, it will be skipped
- The archive folder itself is never processed to prevent recursive archiving
- Empty directories are automatically removed after archiving

## Requirements

- ComfyUI
- Python 3.8+
- No external dependencies (uses only standard library)

## License

[Your License Here]

## Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/yourusername/comfyui-archive-output).
