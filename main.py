import typer
import os
import shutil
import json
import hashlib
from typing import Optional, Dict, List
from pathlib import Path

app = typer.Typer(help="Local File Organizer CLI")

DEFAULT_MAPPING = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".svg", ".bmp"],
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".csv", ".xlsx", ".pptx"],
    "Executables": [".exe", ".msi", ".bat", ".sh", ".cmd"],
    "Archives": [".zip", ".tar", ".gz", ".rar", ".7z", ".jar", ".iso"],
    "Audio": [".mp3", ".wav", ".aac", ".flac"],
    "Video": [".mp4", ".mkv", ".avi", ".mov"]
}

STATE_FILE = ".organizer_state.json"

def get_file_hash(filepath: Path) -> str:
    hasher = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
    except Exception:
        pass
    return hasher.hexdigest()

def find_duplicates(directory: Path, remove: bool = False):
    typer.echo(f"Scanning for duplicates in {directory}...")
    hashes: Dict[str, List[Path]] = {}
    for filepath in directory.rglob("*"):
        if filepath.is_file():
            file_hash = get_file_hash(filepath)
            if file_hash not in hashes:
                hashes[file_hash] = []
            hashes[file_hash].append(filepath)
    
    found = False
    duplicates_to_remove = []
    
    for file_hash, paths in hashes.items():
        if len(paths) > 1:
            found = True
            typer.echo(f"\nDuplicate found ({len(paths)} copies):")
            # Sort by modification time (oldest first) to identify which to remove
            sorted_paths = sorted(paths, key=lambda p: p.stat().st_mtime)
            for i, p in enumerate(sorted_paths):
                mtime = p.stat().st_mtime
                marker = " [NEWEST - KEEP]" if i == len(sorted_paths) - 1 else " [OLD - REMOVE]" if i == 0 else ""
                typer.echo(f"  {i+1}. {p} (modified: {mtime}){marker}")
            
            if remove:
                # Ask user which to remove (keep the newest by default)
                typer.echo(f"\n  Oldest file will be removed, newest will be kept.")
                # Use input() to ensure we always get a prompt
                typer.echo("  Do you want to remove old duplicates? [y/N]: ", nl=False)
                response = input().strip().lower()
                confirm = response in ['y', 'yes']
                if confirm:
                    # Keep the newest (last in sorted list), remove the rest
                    for p in sorted_paths[:-1]:
                        duplicates_to_remove.append(p)
                        typer.echo(f"  Marked for removal: {p}")
    
    if not found:
        typer.echo("No duplicates found.")
        return
    
    # Remove the duplicates if user confirmed
    if duplicates_to_remove:
        typer.echo(f"\nRemoving {len(duplicates_to_remove)} old duplicate(s)...")
        for filepath in duplicates_to_remove:
            try:
                filepath.unlink()
                typer.echo(f"  Removed: {filepath}")
            except Exception as e:
                typer.echo(f"  Error removing {filepath}: {e}")
        typer.echo("Duplicate removal complete!")
    elif remove:
        typer.echo("\nNo duplicates removed.")

def perform_undo(directory: Path):
    state_path = directory / STATE_FILE
    if not state_path.exists():
        typer.echo("No undo history found.")
        raise typer.Exit()
    
    with open(state_path, "r", encoding="utf-8") as f:
        try:
            history = json.load(f)
        except json.JSONDecodeError:
            typer.echo("Error reading undo history.")
            raise typer.Exit(1)
            
    if not history:
        typer.echo("Undo history is empty.")
        raise typer.Exit()
        
    typer.echo("Reverting last organization...")
    for action in reversed(history):
        src = Path(action["src"])
        dst = Path(action["dst"])
        if dst.exists():
            typer.echo(f"Moving {dst.name} back to original location...")
            try:
                shutil.move(str(dst), str(src))
            except Exception as e:
                typer.echo(f"Error moving {dst}: {e}")
        else:
            typer.echo(f"File {dst} not found. Skipping...")
            
    try:
        state_path.unlink()
    except Exception as e:
        typer.echo(f"Could not delete state file: {e}")
    typer.echo("Undo completed successfully!")

@app.command()
def organize(
    directory: Path = typer.Argument(..., help="The directory to organize"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview changes without moving files"),
    config: Optional[Path] = typer.Option(None, "--config", help="Use a custom mapping file (JSON) instead of defaults"),
    duplicates: bool = typer.Option(False, "--duplicates", help="Find duplicate files based on content"),
    remove: bool = typer.Option(False, "--remove", help="Remove old duplicates (requires --duplicates)"),
    undo: bool = typer.Option(False, "--undo", help="Revert the last organization action in the directory")
):
    if not directory.exists() or not directory.is_dir():
        typer.echo(f"Error: Directory '{directory}' does not exist or is not a directory.")
        raise typer.Exit(1)

    if duplicates:
        find_duplicates(directory, remove=remove)
        return

    if undo:
        perform_undo(directory)
        return

    # Load mapping
    mapping = DEFAULT_MAPPING
    if config:
        if not config.exists():
            typer.echo(f"Error: Config file '{config}' not found.")
            raise typer.Exit(1)
        with open(config, "r", encoding="utf-8") as f:
            try:
                mapping = json.load(f)
            except json.JSONDecodeError:
                typer.echo("Error: Invalid JSON in config file.")
                raise typer.Exit(1)

    # Reverse mapping for quick lookup: { ".jpg": "Images", ... }
    ext_to_category = {}
    for category, exts in mapping.items():
        for ext in exts:
            ext_to_category[ext.lower()] = category

    actions = []
    
    typer.echo(f"Organizing '{directory}'...")
    if dry_run:
        typer.echo("[DRY RUN] No files will actually be moved.")
        
    for item in directory.iterdir():
        if not item.is_file():
            continue
        if item.name == STATE_FILE:
            continue
            
        ext = item.suffix.lower()
        category = ext_to_category.get(ext, "Others")
        
        target_dir = directory / category
        target_path = target_dir / item.name
        
        # Handle collisions
        if target_path.exists():
            base = item.stem
            counter = 1
            while target_path.exists():
                target_path = target_dir / f"{base}_{counter}{item.suffix}"
                counter += 1
                
        actions.append({
            "src": str(item),
            "dst": str(target_path)
        })
        
        if dry_run:
            typer.echo(f"[DRY RUN] Move: {item.name} -> {category}/{target_path.name}")
        else:
            target_dir.mkdir(exist_ok=True)
            try:
                shutil.move(str(item), str(target_path))
                typer.echo(f"Moved: {item.name} -> {category}/{target_path.name}")
            except Exception as e:
                typer.echo(f"Error moving {item.name}: {e}")

    if not dry_run and actions:
        state_path = directory / STATE_FILE
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(actions, f, indent=4)
        typer.echo("Organization complete!")
    elif not actions:
        typer.echo("No files to organize.")

if __name__ == "__main__":
    app()