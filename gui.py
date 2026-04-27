import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import shutil
import json
import hashlib
import threading
from pathlib import Path
from typing import Dict, List

DEFAULT_MAPPING = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".svg", ".bmp"],
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".csv", ".xlsx", ".pptx"],
    "Executables": [".exe", ".msi", ".bat", ".sh", ".cmd"],
    "Archives": [".zip", ".tar", ".gz", ".rar", ".7z"],
    "Audio": [".mp3", ".wav", ".aac", ".flac"],
    "Video": [".mp4", ".mkv", ".avi", ".mov"]
}

STATE_FILE = ".organizer_state.json"

class FileOrganizerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Local File Organizer")
        self.geometry("650x550")
        
        # Grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(4, weight=1)

        # Directory selection
        self.dir_label = ctk.CTkLabel(self, text="Target Directory:", font=("Arial", 14, "bold"))
        self.dir_label.grid(row=0, column=0, padx=15, pady=(20, 5), sticky="w")
        
        self.dir_entry = ctk.CTkEntry(self, placeholder_text="Select a folder to organize...")
        self.dir_entry.grid(row=0, column=1, padx=15, pady=(20, 5), sticky="ew")
        
        self.browse_btn = ctk.CTkButton(self, text="Browse", width=90, command=self.browse_directory)
        self.browse_btn.grid(row=0, column=2, padx=15, pady=(20, 5))

        # Options
        self.dry_run_var = ctk.BooleanVar(value=False)
        self.dry_run_cb = ctk.CTkCheckBox(self, text="Dry Run (Preview Changes)", variable=self.dry_run_var)
        self.dry_run_cb.grid(row=1, column=0, columnspan=2, padx=15, pady=10, sticky="w")

        # Action Buttons
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=2, column=0, columnspan=3, padx=15, pady=15, sticky="ew")
        
        self.org_btn = ctk.CTkButton(self.btn_frame, text="Organize Files", fg_color="#28a745", hover_color="#218838", command=self.run_organize)
        self.org_btn.pack(side="left", padx=5)
        
        self.dup_btn = ctk.CTkButton(self.btn_frame, text="Find Duplicates", fg_color="#007bff", hover_color="#0069d9", command=self.run_duplicates)
        self.dup_btn.pack(side="left", padx=5)
        
        self.undo_btn = ctk.CTkButton(self.btn_frame, text="Undo Last Action", fg_color="#dc3545", hover_color="#c82333", command=self.run_undo)
        self.undo_btn.pack(side="right", padx=5)

        # Log Output
        self.log_label = ctk.CTkLabel(self, text="Output Log:", font=("Arial", 14, "bold"))
        self.log_label.grid(row=3, column=0, padx=15, pady=(10, 0), sticky="w")

        self.log_box = ctk.CTkTextbox(self, state="disabled", font=("Consolas", 12))
        self.log_box.grid(row=4, column=0, columnspan=3, padx=15, pady=(5, 20), sticky="nsew")

        self.log("Welcome to Local File Organizer!\nSelect a directory and choose an action to begin.")
        self.action_in_progress = False

    def log(self, message):
        self.after(0, self._insert_log, message)

    def _insert_log(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def browse_directory(self):
        folder = filedialog.askdirectory()
        if folder:
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, folder)

    def get_directory(self) -> Path:
        dir_path = self.dir_entry.get()
        if not dir_path:
            messagebox.showerror("Error", "Please select a directory first.")
            return None
        path = Path(dir_path)
        if not path.exists() or not path.is_dir():
            messagebox.showerror("Error", "The selected directory does not exist or is invalid.")
            return None
        return path

    def set_buttons_state(self, state):
        self.org_btn.configure(state=state)
        self.dup_btn.configure(state=state)
        self.undo_btn.configure(state=state)

    def run_organize(self):
        if self.action_in_progress: return
        directory = self.get_directory()
        if not directory: return
        
        self.clear_log()
        dry_run = self.dry_run_var.get()
        
        def organize_task():
            self.action_in_progress = True
            self.set_buttons_state("disabled")
            mapping = DEFAULT_MAPPING
            ext_to_category = {}
            for category, exts in mapping.items():
                for ext in exts:
                    ext_to_category[ext.lower()] = category

            actions = []
            self.log(f"Organizing '{directory}'...")
            if dry_run:
                self.log("[DRY RUN] No files will actually be moved.")
                
            try:
                for item in directory.iterdir():
                    if not item.is_file(): continue
                    if item.name == STATE_FILE: continue
                    
                    ext = item.suffix.lower()
                    category = ext_to_category.get(ext, "Others")
                    
                    target_dir = directory / category
                    target_path = target_dir / item.name
                    
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
                        self.log(f"[DRY RUN] Move: {item.name} -> {category}/{target_path.name}")
                    else:
                        target_dir.mkdir(exist_ok=True)
                        try:
                            shutil.move(str(item), str(target_path))
                            self.log(f"Moved: {item.name} -> {category}/{target_path.name}")
                        except Exception as e:
                            self.log(f"Error moving {item.name}: {e}")

                if not dry_run and actions:
                    state_path = directory / STATE_FILE
                    with open(state_path, "w", encoding="utf-8") as f:
                        json.dump(actions, f, indent=4)
                    self.log("\nOrganization complete!")
                elif not actions:
                    self.log("\nNo files to organize.")
                    
            except Exception as e:
                self.log(f"An unexpected error occurred: {e}")
            finally:
                self.action_in_progress = False
                self.set_buttons_state("normal")

        threading.Thread(target=organize_task, daemon=True).start()

    def run_duplicates(self):
        if self.action_in_progress: return
        directory = self.get_directory()
        if not directory: return
        
        self.clear_log()
        self.log(f"Scanning for duplicates in {directory}...")
        
        self.action_in_progress = True
        self.set_buttons_state("disabled")
        
        # Use a queue to pass results from background thread to main thread
        import queue
        self._dup_result_queue = queue.Queue()
        
        def scan_task():
            try:
                def get_file_hash(filepath: Path) -> str:
                    hasher = hashlib.sha256()
                    try:
                        with open(filepath, 'rb') as f:
                            while chunk := f.read(8192):
                                hasher.update(chunk)
                    except Exception:
                        pass
                    return hasher.hexdigest()

                self.log("Step 1: Grouping files by size...")
                size_groups: Dict[int, List[Path]] = {}
                file_count = 0
                for filepath in directory.rglob("*"):
                    if filepath.is_file() and filepath.name != STATE_FILE:
                        try:
                            size = filepath.stat().st_size
                            if size not in size_groups:
                                size_groups[size] = []
                            size_groups[size].append(filepath)
                            file_count += 1
                            if file_count % 1000 == 0:
                                self.log(f"  ...scanned {file_count} files")
                        except Exception:
                            pass
                
                self.log(f"Total files scanned: {file_count}")
                
                potential_duplicates = {s: paths for s, paths in size_groups.items() if len(paths) > 1}
                if not potential_duplicates:
                    self._dup_result_queue.put(("none", []))
                    return

                total_potential = sum(len(p) for p in potential_duplicates.values())
                self.log(f"\nStep 2: Hashing {total_potential} potential duplicates...")
                hashes: Dict[str, List[Path]] = {}
                processed = 0
                for size, paths in potential_duplicates.items():
                    for filepath in paths:
                        file_hash = get_file_hash(filepath)
                        if file_hash not in hashes:
                            hashes[file_hash] = []
                        hashes[file_hash].append(filepath)
                        processed += 1
                        if processed % 50 == 0:
                            self.log(f"  ...hashed {processed}/{total_potential} files")
                
                found = False
                duplicates_to_delete = []
                for file_hash, paths in hashes.items():
                    if len(paths) > 1:
                        found = True
                        self.log(f"\nDuplicate found ({len(paths)} copies):")
                        paths.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                        self.log(f"  - {paths[0].name} (Keeping newest: {paths[0].parent})")
                        for p in paths[1:]:
                            self.log(f"  - {p.name} (Older copy: {p.parent})")
                            duplicates_to_delete.append(p)
                
                if found:
                    self._dup_result_queue.put(("found", duplicates_to_delete))
                else:
                    self._dup_result_queue.put(("none", []))
                    
            except Exception as e:
                self.log(f"An error occurred: {e}")
                self._dup_result_queue.put(("error", []))
        
        def check_result():
            try:
                status, duplicates = self._dup_result_queue.get_nowait()
                
                if status == "none":
                    self.log("\nNo duplicates found.")
                    self.log("\nScan complete.")
                elif status == "found" and duplicates:
                    self.log("\nScan complete.")
                    # Show dialog on main thread
                    self.after(10, lambda: self._show_dup_delete_dialog(duplicates))
                    return  # Don't reset buttons yet
                elif status == "error":
                    pass
                    
            except queue.Empty:
                # Check again in 100ms
                self.after(100, check_result)
                return
            
            self.action_in_progress = False
            self.set_buttons_state("normal")
        
        # Start background scan
        threading.Thread(target=scan_task, daemon=True).start()
        # Start checking for results
        self.after(100, check_result)

    def _show_dup_delete_dialog(self, duplicates_to_delete):
        """Show delete confirmation dialog."""
        result = messagebox.askyesno(
            "Delete Duplicates", 
            f"Found {len(duplicates_to_delete)} older duplicate files.\nDo you want to delete them?"
        )
        if result:
            self.log("\nDeleting duplicates...")
            deleted_count = 0
            for p in duplicates_to_delete:
                try:
                    p.unlink()
                    self.log(f"Deleted: {p.name} from {p.parent}")
                    deleted_count += 1
                except Exception as e:
                    self.log(f"Failed to delete {p.name}: {e}")
            self.log(f"\nDeleted {deleted_count} duplicate files.")
        else:
            self.log("\nNo files were deleted.")
        
        self.action_in_progress = False
        self.set_buttons_state("normal")

    def run_undo(self):
        if self.action_in_progress: return
        directory = self.get_directory()
        if not directory: return
        
        self.clear_log()
        state_path = directory / STATE_FILE
        if not state_path.exists():
            self.log("No undo history found in this directory.")
            return
            
        def undo_task():
            self.action_in_progress = True
            self.set_buttons_state("disabled")
            try:
                with open(state_path, "r", encoding="utf-8") as f:
                    try:
                        history = json.load(f)
                    except json.JSONDecodeError:
                        self.log("Error reading undo history.")
                        return
                        
                if not history:
                    self.log("Undo history is empty.")
                    return
                    
                self.log("Reverting last organization...")
                for action in reversed(history):
                    src = Path(action["src"])
                    dst = Path(action["dst"])
                    if dst.exists():
                        self.log(f"Moving {dst.name} back to original location...")
                        try:
                            shutil.move(str(dst), str(src))
                        except Exception as e:
                            self.log(f"Error moving {dst}: {e}")
                    else:
                        self.log(f"File {dst} not found. Skipping...")
                        
                try:
                    state_path.unlink()
                except Exception as e:
                    self.log(f"Could not delete state file: {e}")
                self.log("\nUndo completed successfully!")
            except Exception as e:
                self.log(f"An unexpected error occurred: {e}")
            finally:
                self.action_in_progress = False
                self.set_buttons_state("normal")
                
        threading.Thread(target=undo_task, daemon=True).start()

if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = FileOrganizerApp()
    app.mainloop()