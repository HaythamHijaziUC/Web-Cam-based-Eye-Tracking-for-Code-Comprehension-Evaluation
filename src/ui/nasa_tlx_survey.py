"""NASA-TLX workload assessment survey UI"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Optional
from dataclasses import dataclass

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
        Display NASA-TLX survey and return responses.
        
        Returns:
            NasaTlxScore or None if cancelled
        """
        root = tk.Toplevel(self.parent) if self.parent else tk.Tk()
        root.title("NASA Task Load Index (TLX)")
        root.geometry("600x550")
        
        # Title
        title = tk.Label(root, text="NASA-TLX Workload Assessment",
                        font=("Arial", 14, "bold"))
        title.pack(pady=10)
        
        instructions = tk.Label(root, 
            text="Rate each dimension on a 0-100 scale.\n0 = Low, 100 = High",
            font=("Arial", 10), justify=tk.CENTER)
        instructions.pack(pady=5)
        
        # Canvas with scrollbar
        canvas = tk.Canvas(root)
        scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create sliders
        self.sliders = {}
        for idx, (dimension, question) in enumerate(self.DIMENSIONS):
            frame = ttk.LabelFrame(scrollable_frame, text=dimension)
            frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
            
            # Question label
            q_label = tk.Label(frame, text=question, font=("Arial", 9), wraplength=500)
            q_label.pack(pady=5)
            
            # Slider frame
            slider_frame = ttk.Frame(frame)
            slider_frame.pack(padx=10, pady=5, fill=tk.X)
            
            # Left label
            tk.Label(slider_frame, text="Low", font=("Arial", 8)).pack(side=tk.LEFT)
            
            # Slider
            slider = ttk.Scale(slider_frame, from_=0, to=100, orient=tk.HORIZONTAL)
            slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            
            # Value label
            value_label = tk.Label(slider_frame, text="50", font=("Arial", 9), width=3)
            value_label.pack(side=tk.LEFT)
            
            # Right label
            tk.Label(slider_frame, text="High", font=("Arial", 8)).pack(side=tk.LEFT)
            
            # Update value label on slider change
            def make_update(val_label):
                def update(event=None):
                    val_label.config(text=str(int(slider.get())))
                return update
            
            slider.bind("<B1-Motion>", make_update(value_label))
            slider.bind("<Button-1>", make_update(value_label))
            
            self.sliders[dimension] = slider
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Button frame
        button_frame = ttk.Frame(root)
        button_frame.pack(pady=10)
        
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
        
        ttk.Button(button_frame, text="Submit", command=submit).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=cancel).pack(side=tk.LEFT, padx=5)
        
        if self.parent is None:
            root.mainloop()
        
        return self.result


# Import numpy for averaging
import numpy as np
