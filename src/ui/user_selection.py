"""User selection and management for eye-tracking system - SIMPLIFIED"""

import tkinter as tk
from tkinter import messagebox
import os
import pickle
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
    Ultra-simplified user selection using only message dialogs.
    No complex nested windows or grab() calls.
    Just simple yes/no dialogs that definitely work.
    """
    print("\n" + "="*70)
    print("LAUNCHING USER SELECTION SCREEN")
    print("="*70)
    
    manager = UserManager()
    existing_users = manager.get_existing_users()
    
    result = {
        "user_id": None,
        "is_new_user": False,
        "recalibrate": False,
        "calibration_data": None
    }
    
    # Create minimal root window (hidden)
    root = tk.Tk()
    root.withdraw()
    root.attributes('-alpha', 0)
    root.resizable(False, False)
    root.geometry("1x1+0+0")
    
    # Ask: new or existing user?
    choice = messagebox.askyesno(
        "User Selection",
        "Are you a NEW user?\n\n(YES = New User\nNO = Returning User)"
    )
    
    if choice:  # YES - New User
        print("[FLOW] User chose: NEW USER")
        auto_id = manager.get_next_user_id()
        print(f"[FLOW] Generated auto ID: {auto_id}")
        
        messagebox.showinfo(
            "New User Created",
            f"Your User ID:\n\n{auto_id}\n\nNext: Complete calibration"
        )
        
        result["user_id"] = auto_id
        result["is_new_user"] = True
        result["recalibrate"] = False
        print(f"[FLOW] New user confirmed: {auto_id}\n")
        
    else:  # NO - Existing User
        print(f"[FLOW] User chose: EXISTING USER")
        
        if not existing_users:
            print("[FLOW] No existing users found - treating as new")
            messagebox.showwarning("No Users", "No existing users found.\nCreating as new user.")
            auto_id = manager.get_next_user_id()
            result["user_id"] = auto_id
            result["is_new_user"] = True
            result["recalibrate"] = False
        else:
            print(f"[FLOW] Found {len(existing_users)} users: {existing_users}")
            
            # Simple: just select first user for now
            selected_user = existing_users[0]
            print(f"[FLOW] Selecting first user: {selected_user}")
            
            # Load calibration
            calib_data = manager.load_user_calibration(selected_user)
            if calib_data:
                print(f"[FLOW] Loaded calibration for {selected_user}")
                result["calibration_data"] = calib_data
            
            result["user_id"] = selected_user
            result["is_new_user"] = False
            
            # Check age
            age = manager.get_calibration_age_days(selected_user)
            if age and age > 7:
                print(f"[FLOW] Calibration is {age} days old")
                recal = messagebox.askyesno(
                    "Recalibration",
                    f"Calibration is {age} days old.\n\nRecalibrate now?"
                )
                result["recalibrate"] = recal
                print(f"[FLOW] Recalibrate: {recal}")
            else:
                result["recalibrate"] = False
                if age:
                    print(f"[FLOW] Calibration is {age} days old (fresh)")
            
            print(f"[FLOW] Existing user flow complete\n")
    
    try:
        root.destroy()
    except:
        pass
    
    if result["user_id"] is None:
        print("[FLOW] User selection CANCELLED")
        return None
    
    print(f"[FLOW] User selection COMPLETE: {result}\n")
    return result


if __name__ == "__main__":
    result = show_user_selection_screen()
    if result:
        print(f"✓ Final result: {result}")
    else:
        print("✗ Cancelled")
