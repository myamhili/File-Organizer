# Local File Organizer

A tool to organize files in a directory by their extensions. Available as both CLI and GUI applications.

## Features

- **Organize Files** - Automatically sort files into subdirectories by file type
- **Find Duplicates** - Detect duplicate files using SHA256 hash comparison
- **Remove Duplicates** - Delete old duplicate files (keeps newest)
- **Undo** - Revert organization changes
- **Dry Run** - Preview changes without actually moving files

## Setup

```powershell
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

## Building the Executables (Optional)

To easily build standalone `.exe` files without manually setting up a Python environment, you can simply run the provided batch script:

1. Double-click the `build.bat` file in the project folder.
2. The script will automatically create a virtual environment, install dependencies, and build the executables.

Alternatively, if you prefer to build them manually:

```powershell
# Build the CLI executable
pyinstaller file-organizer.spec

# Build the GUI executable
pyinstaller file-organizer-gui.spec
```

The generated executables will be placed in a new `dist/` folder. The temporary `build/` folder will also be created during this process.

## Usage

### CLI Version

```powershell
python main.py <directory> [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--dry-run` | Preview changes without moving files |
| `--config <path>` | Use a custom mapping JSON file |
| `--duplicates` | Find duplicate files based on content |
| `--remove` | Remove old duplicates (requires --duplicates) |
| `--undo` | Revert the last organization action |

**Examples:**
```powershell
# Organize files
python main.py C:\Downloads

# Preview without moving
python main.py C:\Downloads --dry-run

# Find duplicates
python main.py C:\Downloads --duplicates

# Find and remove duplicates
python main.py C:\Downloads --duplicates --remove

# Undo last organization
python main.py C:\Downloads --undo
```

### GUI Version

```powershell
python gui.py
```

Or run `file-organizer-gui.exe` from the `dist` folder.

**GUI Controls:**
- **Browse** - Select a directory to organize
- **Dry Run** - Checkbox to preview changes
- **Organize Files** - Start organization
- **Find Duplicates** - Scan for duplicates (prompts to delete old copies)
- **Undo Last Action** - Revert last organization

## File Categories

| Category | Extensions |
|----------|------------|
| Images | .jpg, .jpeg, .png, .gif, .svg, .bmp |
| Documents | .pdf, .doc, .docx, .txt, .csv, .xlsx, .pptx |
| Executables | .exe, .msi, .bat, .sh, .cmd |
| Archives | .zip, .tar, .gz, .rar, .7z, .jar, .iso |
| Audio | .mp3, .wav, .aac, .flac |
| Video | .mp4, .mkv, .avi, .mov |

## Custom Configuration

Create a JSON file to define custom categories:

```json
{
  "Photos": [".jpg", ".png"],
  "Videos": [".mp4", ".mov"],
  "Documents": [".pdf", ".docx"]
}
```

Use with CLI: `python main.py <directory> --config custom.json`
