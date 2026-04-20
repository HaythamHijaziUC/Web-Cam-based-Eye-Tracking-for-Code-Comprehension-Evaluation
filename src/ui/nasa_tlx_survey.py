"""NASA-TLX workload assessment survey UI"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Optional
from dataclasses import dataclass
import numpy as np

@dataclass
class NasaTlxScore:
    """NASA-TLX survey response"""
    mental_demand: int  # 0-100
    physical_demand: int
    temporal_demand: int
    performance: int
    effort: int
    frustration: int
    overall_workload: float
    
    def to_dict(self) -> Dict:
        return {
            'mental_demand': self.mental_demand,
            'physical_demand': self.physical_demand,
            'temporal_demand': self.temporal_demand,
            'performance': self.performance,
            'effort': self.effort,
            'frustration': self.frustration,
            'overall_workload': self.overall_workload
        }


class NasaTlxSurvey:
    """NASA-TLX workload assessment survey"""
    
    DIMENSIONS = [
        ('Mental Demand', 'How mentally demanding was the code comprehension task?'),
        ('Physical Demand', 'How physically demanding was the task?'),
        ('Temporal Demand', 'How rushed or hurried was the pace of the task?'),
        ('Performance', 'How successful were you in accomplishing what you were asked?'),
        ('Effort', 'How hard did you have to work to accomplish your level of performance?'),
        ('Frustration', 'How insecure, discouraged, irritated, stressed, and annoyed were you?'),
    ]
    
    def __init__(self, parent=None):
        self.parent = parent or tk.Tk()
        self.sliders = {}
        self.result = None
        
    def show_survey(self) -> Optional[NasaTlxScore]:
        """
        Display NASA-TLX survey and return responses - LARGE UI.
        
        Returns:
            NasaTlxScore or None if cancelled
        """
        root = tk.Toplevel(self.parent) if self.parent else tk.Tk()
        root.title("NASA Task Load Index (TLX) - Workload Assessment")
        root.geometry("1000x800")
        root.resizable(False, False)
        
        # Center on screen
        root.update_idletasks()
        x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
        y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
        root.geometry(f"+{max(0, x)}+{max(0, y)}")
        
        # Title
        title = tk.Label(root, text="NASA Task Load Index - Workload Assessment",
                        font=("Arial", 20, "bold"), bg="#1565C0", fg="white")
        title.pack(fill=tk.X, padx=0, pady=0)
        
        instructions = tk.Label(root, 
            text="Please rate each dimension below on a 0-100 scale (0 = Low, 100 = High)",
            font=("Arial", 14), justify=tk.CENTER, bg="#F5F5F5")
        instructions.pack(fill=tk.X, padx=10, pady=15)
        
        # Canvas with scrollbar
        canvas = tk.Canvas(root, bg="white")
        scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create sliders - LARGER
        self.sliders = {}
        colors = ["#E3F2FD", "#F3E5F5", "#E0F2F1", "#FFF3E0", "#FCE4EC", "#E8F5E9"]
        
        for idx, (dimension, question) in enumerate(self.DIMENSIONS):
            # Outer frame with color
            outer_frame = tk.Frame(scrollable_frame, bg=colors[idx], relief=tk.RAISED, bd=2)
            outer_frame.pack(padx=15, pady=12, fill=tk.BOTH, expand=False)
            
            # Title
            title_label = tk.Label(outer_frame, text=dimension, 
                                 font=("Arial", 16, "bold"), bg=colors[idx], fg="#1565C0")
            title_label.pack(anchor=tk.W, padx=15, pady=(10, 5))
            
            # Question label
            q_label = tk.Label(outer_frame, text=question, 
                             font=("Arial", 13), wraplength=900, justify=tk.LEFT, bg=colors[idx])
            q_label.pack(anchor=tk.W, padx=15, pady=(0, 15))
            
            # Slider frame
            slider_frame = tk.Frame(outer_frame, bg=colors[idx])
            slider_frame.pack(padx=15, pady=10, fill=tk.X)
            
            # Left label
            tk.Label(slider_frame, text="0", font=("Arial", 12, "bold"), bg=colors[idx]).pack(side=tk.LEFT, padx=5)
            tk.Label(slider_frame, text="Low", font=("Arial", 12), bg=colors[idx], fg="#666").pack(side=tk.LEFT)
            
            # Slider - LARGER
            slider = ttk.Scale(slider_frame, from_=0, to=100, orient=tk.HORIZONTAL, length=600)
            slider.set(50)
            slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=20)
            
            # Value label - LARGE
            value_label = tk.Label(slider_frame, text="50", font=("Arial", 16, "bold"), 
                                 bg=colors[idx], fg="#D32F2F", width=4)
            value_label.pack(side=tk.LEFT, padx=10)
            
            # Right label
            tk.Label(slider_frame, text="High", font=("Arial", 12), bg=colors[idx], fg="#666").pack(side=tk.LEFT)
            tk.Label(slider_frame, text="100", font=("Arial", 12, "bold"), bg=colors[idx]).pack(side=tk.LEFT, padx=5)
            
            # Update value label on slider change
            def make_update(val_label):
                def update(event=None):
                    val_label.config(text=str(int(slider.get())))
                return update
            
            slider.bind("<B1-Motion>", make_update(value_label))
            slider.bind("<Button-1>", make_update(value_label))
            slider.bind("<MouseWheel>", make_update(value_label))
            
            self.sliders[dimension] = slider
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Button frame
        button_frame = tk.Frame(root, bg="#F5F5F5")
        button_frame.pack(fill=tk.X, padx=10, pady=20)
        
        def submit():
            try:
                scores = NasaTlxScore(
                    mental_demand=int(self.sliders['Mental Demand'].get()),
                    physical_demand=int(self.sliders['Physical Demand'].get()),
                    temporal_demand=int(self.sliders['Temporal Demand'].get()),
                    performance=int(self.sliders['Performance'].get()),
                    effort=int(self.sliders['Effort'].get()),
                    frustration=int(self.sliders['Frustration'].get()),
                    overall_workload=np.mean([
                        int(s.get()) for s in self.sliders.values()
                    ])
                )
                self.result = scores
                root.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Invalid input: {e}")
        
        def cancel():
            self.result = None
            root.destroy()
        
        tk.Button(button_frame, text="✓ Submit Responses", command=submit,
                 font=("Arial", 14, "bold"), bg="#4CAF50", fg="white",
                 width=25, height=2, relief=tk.RAISED, bd=2).pack(side=tk.LEFT, padx=10)
        
        tk.Button(button_frame, text="✕ Cancel", command=cancel,
                 font=("Arial", 14, "bold"), bg="#f44336", fg="white",
                 width=25, height=2, relief=tk.RAISED, bd=2).pack(side=tk.LEFT, padx=10)
        
        if self.parent is None:
            root.mainloop()
        
        return self.result
