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
    PROPER LARGE UI with working buttons and calibration flow.
    
    Returns:
        Dictionary with 'user_id', 'is_new_user', 'recalibrate', 'calibration_data', or None if cancelled
    """
    root = tk.Tk()
    root.title("Eye-Tracking System - User Selection")
    
    # Get screen size and maximize window
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    root.geometry(f"{screen_w}x{screen_h}")
    root.resizable(True, True)
    
    result = {"user_id": None, "is_new_user": False, "recalibrate": False}
    manager = UserManager()
    
    # Get existing users upfront
    existing_users = manager.get_existing_users()
    
    # ========================
    # MAIN SCREEN LAYOUT
    # ========================
    
    # Title bar
    title_frame = tk.Frame(root, bg="#1565C0")
    title_frame.pack(fill=tk.X, padx=0, pady=0)
    
    tk.Label(title_frame, text="👁️ Eye-Tracking System - User Selection", 
            font=("Arial", 32, "bold"), bg="#1565C0", fg="white").pack(pady=30)
    
    # Subtitle
    tk.Label(root, text="Select whether you are a new user or returning user", 
            font=("Arial", 18), fg="#333").pack(pady=20)
    
    # Main content frame
    content_frame = tk.Frame(root)
    content_frame.pack(pady=40, expand=True)
    
    # Two columns for buttons
    left_frame = tk.Frame(content_frame)
    left_frame.pack(side=tk.LEFT, padx=60, expand=True)
    
    right_frame = tk.Frame(content_frame)
    right_frame.pack(side=tk.RIGHT, padx=60, expand=True)
    
    # ========================
    # NEW USER FLOW
    # ========================
    def on_new_user_click():
        """Create new user with auto-generated ID and proceed to calibration"""
        # Hide main window
        root.withdraw()
        
        # Auto-generate ID
        auto_id = manager.get_next_user_id()
        
        # Create new window for confirmation
        dialog = tk.Toplevel(root)
        dialog.title("New User")
        dialog.geometry("700x400")
        dialog.resizable(False, False)
        
        # Center dialog
        dialog.update_idletasks()
        x = (screen_w // 2) - (dialog.winfo_width() // 2)
        y = (screen_h // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Content
        tk.Label(dialog, text="Welcome, New User!", font=("Arial", 24, "bold")).pack(pady=20)
        
        tk.Label(dialog, text="Your User ID (auto-generated):", font=("Arial", 16)).pack(pady=10)
        
        # ID display box
        id_frame = tk.Frame(dialog, bg="#E3F2FD", relief=tk.SUNKEN, bd=3)
        id_frame.pack(pady=20, padx=30, fill=tk.BOTH, expand=True)
        
        tk.Label(id_frame, text=auto_id, font=("Arial", 40, "bold"), 
                bg="#E3F2FD", fg="#1976D2").pack(pady=20)
        
        tk.Label(dialog, text="This ID will identify you in future sessions\nNext: You will complete calibration", 
                font=("Arial", 13), fg="#666", justify=tk.CENTER).pack(pady=10)
        
        def confirm_new_user():
            """Proceed to calibration"""
            result["user_id"] = auto_id
            result["is_new_user"] = True
            result["recalibrate"] = False
            dialog.destroy()
            root.destroy()
        
        def cancel_new_user():
            """Go back"""
            dialog.destroy()
            root.deiconify()
        
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="Continue to Calibration", command=confirm_new_user, 
                 bg="#4CAF50", fg="white", font=("Arial", 14, "bold"),
                 width=20, height=2).pack(side=tk.LEFT, padx=10)
        
        tk.Button(button_frame, text="Back", command=cancel_new_user,
                 bg="#9E9E9E", fg="white", font=("Arial", 14, "bold"),
                 width=20, height=2).pack(side=tk.LEFT, padx=10)
    
    # ========================
    # EXISTING USER FLOW
    # ========================
    def on_existing_user_click():
        """Select existing user"""
        if not existing_users:
            messagebox.showwarning("No Users", "No existing users found. Please create a new user first.")
            return
        
        # Hide main window
        root.withdraw()
        
        # Create selection window
        dialog = tk.Toplevel(root)
        dialog.title("Select Existing User")
        dialog.geometry("700x600")
        dialog.resizable(False, False)
        
        # Center dialog
        dialog.update_idletasks()
        x = (screen_w // 2) - (dialog.winfo_width() // 2)
        y = (screen_h // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        tk.Label(dialog, text="Welcome Back!", font=("Arial", 24, "bold")).pack(pady=15)
        tk.Label(dialog, text="Select Your User ID", font=("Arial", 16)).pack(pady=5)
        
        # Listbox with scrollbar
        list_frame = tk.Frame(dialog, relief=tk.SUNKEN, bd=2)
        list_frame.pack(pady=15, padx=20, fill=tk.BOTH, expand=True)
        
        listbox = tk.Listbox(list_frame, font=("Arial", 14), height=12, width=50)
        scrollbar = tk.Scrollbar(list_frame, command=listbox.yview)
        listbox.config(yscrollcommand=scrollbar.set)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate with user info
        for user_id in existing_users:
            age = manager.get_calibration_age_days(user_id)
            if age is not None:
                if age > 7:
                    display_text = f"{user_id}  ({age} days old) ⚠️ STALE - RECALIBRATE RECOMMENDED"
                else:
                    display_text = f"{user_id}  ({age} days old)"
            else:
                display_text = f"{user_id}  (calibration age unknown)"
            listbox.insert(tk.END, display_text)
        
        # Auto-select first
        listbox.selection_set(0)
        listbox.see(0)
        
        def select_user():
            """Confirm user selection"""
            if not listbox.curselection():
                messagebox.showerror("Error", "Please select a user")
                return
            
            selected_idx = listbox.curselection()[0]
            selected_user = existing_users[selected_idx]
            
            # Load calibration
            calib_data = manager.load_user_calibration(selected_user)
            
            result["user_id"] = selected_user
            result["is_new_user"] = False
            
            if calib_data:
                result["calibration_data"] = calib_data
                print(f"✓ Loaded calibration for user {selected_user}")
            
            # Check if recalibration needed
            age = manager.get_calibration_age_days(selected_user)
            if age and age > 7:
                response = messagebox.askyesno(
                    "Calibration Stale",
                    f"Your calibration is {age} days old.\n\nWould you like to recalibrate?\n(Recommended for best accuracy)",
                    parent=dialog
                )
                result["recalibrate"] = response
            
            dialog.destroy()
            root.destroy()
        
        def back():
            """Go back"""
            dialog.destroy()
            root.deiconify()
        
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=15)
        
        tk.Button(button_frame, text="Select This User", command=select_user,
                 bg="#2196F3", fg="white", font=("Arial", 14, "bold"),
                 width=22, height=2).pack(side=tk.LEFT, padx=10)
        
        tk.Button(button_frame, text="Back", command=back,
                 bg="#9E9E9E", fg="white", font=("Arial", 14, "bold"),
                 width=22, height=2).pack(side=tk.LEFT, padx=10)
    
    # ========================
    # LEFT BUTTON: NEW USER
    # ========================
    tk.Label(left_frame, text="First Time?", font=("Arial", 18, "bold"), fg="#4CAF50").pack(pady=10)
    
    new_user_btn = tk.Button(
        left_frame, 
        text="➕\nNEW USER\n\nGet auto-generated ID\nand complete calibration",
        command=on_new_user_click,
        font=("Arial", 16, "bold"),
        bg="#4CAF50", 
        fg="white",
        width=30, 
        height=8,
        relief=tk.RAISED,
        bd=4,
        wraplength=250
    )
    new_user_btn.pack(pady=20, fill=tk.BOTH, expand=True)
    
    # ========================
    # RIGHT BUTTON: EXISTING USER
    # ========================
    tk.Label(right_frame, text="Returning?", font=("Arial", 18, "bold"), fg="#2196F3").pack(pady=10)
    
    existing_user_btn = tk.Button(
        right_frame,
        text="🔄\nRETURNING USER\n\nSelect your ID\nand load calibration",
        command=on_existing_user_click,
        font=("Arial", 16, "bold"),
        bg="#2196F3",
        fg="white",
        width=30,
        height=8,
        relief=tk.RAISED,
        bd=4,
        wraplength=250
    )
    existing_user_btn.pack(pady=20, fill=tk.BOTH, expand=True)
    
    # Run window
    root.mainloop()
    
    # Return result
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
