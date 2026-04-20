"""User selection and management for eye-tracking system"""

import tkinter as tk
from tkinter import simpledialog, messagebox
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


def show_user_selection_screen() -> Optional[Dict[str, Any]]:
    """
    Display user selection/creation screen on app launch.
    
    Returns:
        Dictionary with 'user_id' and 'is_new_user' flag, or None if cancelled
    """
    root = tk.Tk()
    root.title("Eye-Tracking System - User Selection")
    root.geometry("400x300")
    root.resizable(False, False)
    
    result = {"user_id": None, "is_new_user": False}
    manager = UserManager()
    
    def on_new_user():
        """Create new user"""
        dialog = tk.Toplevel(root)
        dialog.title("New User")
        dialog.geometry("300x150")
        dialog.resizable(False, False)
        
        tk.Label(dialog, text="Enter User ID:", font=("Arial", 10)).pack(pady=10)
        entry = tk.Entry(dialog, font=("Arial", 12), width=20)
        entry.pack(pady=5)
        
        def submit():
            user_id = entry.get().strip()
            if not user_id:
                messagebox.showerror("Error", "User ID cannot be empty")
                return
            
            if manager.user_exists(user_id):
                if messagebox.askyesno("Confirm", f"User '{user_id}' exists. Replace calibration?"):
                    result["user_id"] = user_id
                    result["is_new_user"] = True
                    root.quit()
            else:
                result["user_id"] = user_id
                result["is_new_user"] = True
                root.quit()
        
        tk.Button(dialog, text="Create", command=submit, bg="#4CAF50", fg="white").pack(pady=10)
    
    def on_existing_user():
        """Select existing user"""
        users = manager.get_existing_users()
        
        if not users:
            messagebox.showinfo("Info", "No existing users found")
            return
        
        dialog = tk.Toplevel(root)
        dialog.title("Select Existing User")
        dialog.geometry("350x250")
        
        tk.Label(dialog, text="Select User:", font=("Arial", 10)).pack(pady=10)
        
        # Listbox with user info
        frame = tk.Frame(dialog)
        frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        listbox = tk.Listbox(frame, font=("Arial", 10), height=8)
        scrollbar = tk.Scrollbar(frame, command=listbox.yview)
        listbox.config(yscrollcommand=scrollbar.set)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate with user info
        for user_id in users:
            age = manager.get_calibration_age_days(user_id)
            age_str = f" ({age}d old)" if age is not None else ""
            warning = " ⚠️ STALE" if age and age > 7 else ""
            listbox.insert(tk.END, f"{user_id}{age_str}{warning}")
        
        def select():
            if not listbox.curselection():
                messagebox.showshowerror("Error", "Please select a user")
                return
            
            selected_idx = listbox.curselection()[0]
            result["user_id"] = users[selected_idx]
            result["is_new_user"] = False
            
            age = manager.get_calibration_age_days(result["user_id"])
            if age and age > 7:
                if messagebox.askyesno("Warning", 
                    f"Calibration is {age} days old. Recalibrate?"):
                    result["recalibrate"] = True
            
            root.quit()
        
        tk.Button(dialog, text="Select", command=select, bg="#2196F3", fg="white").pack(pady=10)
    
    # Main buttons
    tk.Label(root, text="Eye-Tracking System", font=("Arial", 16, "bold")).pack(pady=20)
    
    tk.Button(root, text="New User", command=on_new_user, 
             bg="#4CAF50", fg="white", font=("Arial", 12), width=30, height=2).pack(pady=10)
    
    tk.Button(root, text="Existing User", command=on_existing_user,
             bg="#2196F3", fg="white", font=("Arial", 12), width=30, height=2).pack(pady=10)
    
    tk.Button(root, text="Exit", command=root.quit,
             bg="#f44336", fg="white", font=("Arial", 10), width=30).pack(pady=10)
    
    root.mainloop()
    root.destroy()
    
    return result if result["user_id"] else None
