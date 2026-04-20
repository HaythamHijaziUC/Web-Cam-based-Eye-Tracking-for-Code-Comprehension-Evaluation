"""User selection and management for eye-tracking system"""

import tkinter as tk
from tkinter import messagebox
import os
import pickle
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

CALIBRATIONS_DIR = Path("calibrations")

class UserManager:
    """Manage user selection, creation, and validation"""
    
    def __init__(self):
        self.calibrations_dir = CALIBRATIONS_DIR
        self.calibrations_dir.mkdir(exist_ok=True)
        
    def get_existing_users(self) -> list:
        """Get list of existing user IDs from calibration files"""
        users = []
        for pkl_file in self.calibrations_dir.glob("*.pkl"):
            user_id = pkl_file.stem
            if user_id != "metadata":
                users.append(user_id)
        return sorted(users)
    
    def user_exists(self, user_id: str) -> bool:
        """Check if user calibration exists"""
        return (self.calibrations_dir / f"{user_id}.pkl").exists()
    
    def load_user_calibration(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Load user calibration data"""
        calib_file = self.calibrations_dir / f"{user_id}.pkl"
        if not calib_file.exists():
            return None
        
        try:
            with open(calib_file, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Error loading calibration for user {user_id}: {e}")
            return None
    
    def save_user_calibration(self, user_id: str, data: Dict[str, Any]) -> bool:
        """Save user calibration data"""
        calib_file = self.calibrations_dir / f"{user_id}.pkl"
        try:
            with open(calib_file, 'wb') as f:
                pickle.dump(data, f)
            return True
        except Exception as e:
            print(f"Error saving calibration for user {user_id}: {e}")
            return False
    
    def get_calibration_age_days(self, user_id: str) -> Optional[int]:
        """Get age of calibration in days"""
        calib_data = self.load_user_calibration(user_id)
        if not calib_data or 'timestamp' not in calib_data:
            return None
        
        calib_time = datetime.fromisoformat(calib_data['timestamp'])
        age = (datetime.now() - calib_time).days
        return age
    
    def get_next_user_id(self) -> str:
        """Auto-generate next user ID"""
        existing = self.get_existing_users()
        
        # Extract numeric IDs
        numeric_ids = []
        for user_id in existing:
            if user_id.startswith("user_"):
                try:
                    num = int(user_id.split("_")[1])
                    numeric_ids.append(num)
                except (ValueError, IndexError):
                    pass
        
        next_num = max(numeric_ids) + 1 if numeric_ids else 1
        return f"user_{next_num:03d}"


def show_user_selection_screen() -> Optional[Dict[str, Any]]:
    """
    Display user selection/creation screen on app launch.
    LARGE UI with auto-generated user IDs and calibration loading.
    
    Returns:
        Dictionary with 'user_id', 'is_new_user', 'recalibrate', or None if cancelled
    """
    root = tk.Tk()
    root.title("Eye-Tracking System - User Selection")
    root.geometry("900x600")
    root.resizable(False, False)
    
    # Center on screen
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{max(0, x)}+{max(0, y)}")
    
    result = {"user_id": None, "is_new_user": False, "recalibrate": False}
    manager = UserManager()
    
    # ========================
    # NEW USER DIALOG
    # ========================
    def on_new_user():
        """Create new user with auto-generated ID"""
        dialog = tk.Toplevel(root)
        dialog.title("New User - Auto Generated ID")
        dialog.geometry("600x300")
        dialog.resizable(False, False)
        dialog.grab_set()
        
        # Auto-generate ID
        auto_id = manager.get_next_user_id()
        
        tk.Label(dialog, text="New User", font=("Arial", 20, "bold")).pack(pady=20)
        
        tk.Label(dialog, text="Your User ID (auto-generated):", font=("Arial", 16)).pack(pady=10)
        
        # Display the auto-generated ID in large text
        id_frame = tk.Frame(dialog, bg="#E3F2FD", relief=tk.SUNKEN, bd=2)
        id_frame.pack(pady=15, padx=30, fill=tk.BOTH, expand=True)
        
        tk.Label(id_frame, text=auto_id, font=("Arial", 32, "bold"), bg="#E3F2FD", fg="#1976D2").pack(pady=20)
        
        info_label = tk.Label(dialog, text="Remember this ID for future sessions", font=("Arial", 12), fg="gray")
        info_label.pack(pady=10)
        
        def confirm():
            """Confirm new user creation"""
            result["user_id"] = auto_id
            result["is_new_user"] = True
            result["recalibrate"] = False
            dialog.destroy()
            root.quit()
        
        def cancel():
            """Cancel new user creation"""
            dialog.destroy()
        
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="Confirm", command=confirm, 
                 bg="#4CAF50", fg="white", font=("Arial", 14, "bold"),
                 width=15, height=2).pack(side=tk.LEFT, padx=10)
        
        tk.Button(button_frame, text="Cancel", command=cancel,
                 bg="#9E9E9E", fg="white", font=("Arial", 14, "bold"),
                 width=15, height=2).pack(side=tk.LEFT, padx=10)
    
    # ========================
    # EXISTING USER DIALOG
    # ========================
    def on_existing_user():
        """Select existing user and load calibration"""
        users = manager.get_existing_users()
        
        if not users:
            messagebox.showinfo("Info", "No existing users found\n\nCreate a new user first.", parent=root)
            return
        
        dialog = tk.Toplevel(root)
        dialog.title("Select Existing User")
        dialog.geometry("700x500")
        dialog.resizable(False, False)
        dialog.grab_set()
        
        tk.Label(dialog, text="Select Your User ID", font=("Arial", 18, "bold")).pack(pady=15)
        
        # Listbox with scrollbar
        frame = tk.Frame(dialog, relief=tk.SUNKEN, bd=2)
        frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        listbox = tk.Listbox(frame, font=("Arial", 14), height=10, width=40)
        scrollbar = tk.Scrollbar(frame, command=listbox.yview)
        listbox.config(yscrollcommand=scrollbar.set)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate with user info
        for user_id in users:
            age = manager.get_calibration_age_days(user_id)
            if age is not None:
                if age > 7:
                    display_text = f"{user_id}  ({age}d old) ⚠️ STALE"
                else:
                    display_text = f"{user_id}  ({age}d old)"
            else:
                display_text = f"{user_id}  (age unknown)"
            listbox.insert(tk.END, display_text)
        
        # Auto-select first user
        listbox.selection_set(0)
        listbox.see(0)
        
        def select():
            """Select user and load calibration"""
            if not listbox.curselection():
                messagebox.showerror("Error", "Please select a user", parent=dialog)
                return
            
            selected_idx = listbox.curselection()[0]
            selected_user = users[selected_idx]
            
            # Load calibration for selected user
            calib_data = manager.load_user_calibration(selected_user)
            
            if calib_data:
                print(f"✓ Loaded calibration for user {selected_user}")
                result["user_id"] = selected_user
                result["is_new_user"] = False
                result["calibration_data"] = calib_data  # Store loaded calibration
                
                # Check age and ask for recalibration
                age = manager.get_calibration_age_days(selected_user)
                if age and age > 7:
                    response = messagebox.askyesno(
                        "Calibration Stale",
                        f"Calibration is {age} days old.\n\nRecalibrate now?",
                        parent=dialog
                    )
                    result["recalibrate"] = response
            else:
                # User exists but no calibration loaded - require new calibration
                print(f"⚠️ Could not load calibration for user {selected_user}")
                result["user_id"] = selected_user
                result["is_new_user"] = False
                result["recalibrate"] = True
            
            dialog.destroy()
            root.quit()
        
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=15)
        
        tk.Button(button_frame, text="Select", command=select,
                 bg="#2196F3", fg="white", font=("Arial", 14, "bold"),
                 width=20, height=2).pack(side=tk.LEFT, padx=10)
        
        tk.Button(button_frame, text="Cancel", command=dialog.destroy,
                 bg="#9E9E9E", fg="white", font=("Arial", 14, "bold"),
                 width=20, height=2).pack(side=tk.LEFT, padx=10)
    
    # ========================
    # MAIN SCREEN
    # ========================
    
    # Title
    title_frame = tk.Frame(root, bg="#1565C0")
    title_frame.pack(fill=tk.X)
    
    tk.Label(title_frame, text="👁️ Eye-Tracking System", 
            font=("Arial", 28, "bold"), bg="#1565C0", fg="white").pack(pady=20)
    
    # Subtitle
    tk.Label(root, text="Welcome to the Eye-Tracking Experiment", 
            font=("Arial", 16), fg="#555").pack(pady=10)
    
    # Button frame
    button_frame = tk.Frame(root)
    button_frame.pack(pady=60, expand=True)
    
    # NEW USER BUTTON
    new_user_btn = tk.Button(
        button_frame, 
        text="👤 New User",
        command=on_new_user,
        font=("Arial", 18, "bold"),
        bg="#4CAF50", 
        fg="white",
        width=25, 
        height=4,
        relief=tk.RAISED,
        bd=3
    )
    new_user_btn.pack(pady=20)
    
    # EXISTING USER BUTTON
    existing_user_btn = tk.Button(
        button_frame,
        text="🔄 Returning User",
        command=on_existing_user,
        font=("Arial", 18, "bold"),
        bg="#2196F3",
        fg="white",
        width=25,
        height=4,
        relief=tk.RAISED,
        bd=3
    )
    existing_user_btn.pack(pady=20)
    
    # Info text
    info_frame = tk.Frame(root, bg="#F5F5F5")
    info_frame.pack(fill=tk.X, side=tk.BOTTOM)
    
    tk.Label(info_frame, 
            text="New users: Get a unique auto-generated ID  |  Returning users: Select your ID to load your calibration",
            font=("Arial", 11), 
            bg="#F5F5F5", 
            fg="#666",
            justify=tk.CENTER).pack(pady=15)
    
    # Run dialog
    root.mainloop()
    root.destroy()
    
    # Return None if cancelled (user_id is None)
    if result["user_id"] is None:
        return None
    
    return result


if __name__ == "__main__":
    # Test the UI
    result = show_user_selection_screen()
    if result:
        print(f"Result: {result}")
    else:
        print("Cancelled")
