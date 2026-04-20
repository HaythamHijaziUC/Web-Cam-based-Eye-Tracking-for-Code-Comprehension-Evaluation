#!/usr/bin/env python
"""Test user selection flow"""

from src.ui.user_selection import show_user_selection_screen

print("Testing user selection screen...")
print("=" * 70)

result = show_user_selection_screen()

print("=" * 70)
if result:
    print(f"SUCCESS! Result: {result}")
else:
    print("FAILED: No result returned")
