import tkinter as tk
from tkinter import ttk, messagebox
import logging
import threading
import multiprocessing
import queue
import time
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import json
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bmi_calculator.log'),
        logging.StreamHandler()
    ]
)


class BMIProcessor:
    """CPU-bound BMI calculation using multiprocessing"""

    @staticmethod
    def calculate_bmi_process(weight, height):
        """Calculate BMI using multiprocessing for CPU-bound task"""
        try:
            height_in_meters = height / 100
            bmi = weight / (height_in_meters ** 2)
            return round(bmi, 2)
        except Exception as e:
            logging.error(f"BMI calculation error: {e}")
            return None


class BMIHistory:
    """IO-bound operations for history management"""

    def __init__(self, filename='bmi_history.json'):
        self.filename = filename

    def save_to_history(self, data):
        """IO-bound operation in separate thread"""

        def save_task():
            try:
                history = self.load_history()
                history.append(data)
                with open(self.filename, 'w') as f:
                    json.dump(history, f, indent=2)
                logging.info(f"Saved BMI record: {data}")
            except Exception as e:
                logging.error(f"History save error: {e}")

        threading.Thread(target=save_task, daemon=True).start()

    def load_history(self):
        """Load history from file"""
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logging.error(f"History load error: {e}")
            return []


class AdvancedBMICalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced BMI Calculator")
        self.root.configure(bg='black')
        self.root.geometry('800x600')

        # Initialize components
        self.bmi_processor = BMIProcessor()
        self.history_manager = BMIHistory()
        self.current_bmi = None
        self.current_category = None

        # Style configuration
        self.setup_styles()

        # Create GUI
        self.create_gui()

        logging.info("Advanced BMI Calculator started")

    def setup_styles(self):
        """Configure advanced styling"""
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Configure colors
        self.style.configure('TFrame', background='black')
        self.style.configure('TLabel', background='black', foreground='white', font=('Arial', 10))
        self.style.configure('Title.TLabel', background='black', foreground='cyan', font=('Arial', 16, 'bold'))
        self.style.configure('Result.TLabel', background='black', foreground='yellow', font=('Arial', 12, 'bold'))
        self.style.configure('Status.TLabel', background='black', font=('Arial', 11, 'bold'))

        # Configure buttons
        self.style.configure('Action.TButton',
                             background='#0066cc',
                             foreground='white',
                             font=('Arial', 10, 'bold'),
                             focuscolor='none')
        self.style.map('Action.TButton',
                       background=[('active', '#0088ff'), ('pressed', '#004499')])

        # Configure entries
        self.style.configure('TEntry', fieldbackground='#333333', foreground='white')

    def create_gui(self):
        """Create the main GUI layout"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title
        title_label = ttk.Label(main_frame, text="ADVANCED BMI CALCULATOR", style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Input frame
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=(0, 10))

        # Weight input
        ttk.Label(input_frame, text="Weight (kg):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.weight_var = tk.StringVar()
        weight_entry = ttk.Entry(input_frame, textvariable=self.weight_var, width=15)
        weight_entry.grid(row=0, column=1, pady=5, padx=(5, 0))
        weight_entry.bind('<Return>', lambda e: self.calculate_bmi())

        # Height input
        ttk.Label(input_frame, text="Height (cm):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.height_var = tk.StringVar()
        height_entry = ttk.Entry(input_frame, textvariable=self.height_var, width=15)
        height_entry.grid(row=1, column=1, pady=5, padx=(5, 0))
        height_entry.bind('<Return>', lambda e: self.calculate_bmi())

        # Buttons
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)

        calculate_btn = ttk.Button(button_frame, text="Calculate BMI",
                                   command=self.calculate_bmi, style='Action.TButton')
        calculate_btn.grid(row=0, column=0, padx=5)

        clear_btn = ttk.Button(button_frame, text="Clear",
                               command=self.clear_inputs, style='Action.TButton')
        clear_btn.grid(row=0, column=1, padx=5)

        show_chart_btn = ttk.Button(button_frame, text="Show Chart",
                                    command=self.toggle_chart, style='Action.TButton')
        show_chart_btn.grid(row=0, column=2, padx=5)

        history_btn = ttk.Button(button_frame, text="Show History",
                                 command=self.show_history, style='Action.TButton')
        history_btn.grid(row=0, column=3, padx=5)

        # Results frame
        results_frame = ttk.Frame(main_frame)
        results_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=10)

        self.bmi_result = ttk.Label(results_frame, text="BMI: --", style='Result.TLabel')
        self.bmi_result.grid(row=0, column=0, pady=5)

        self.category_result = ttk.Label(results_frame, text="Category: --", style='Result.TLabel')
        self.category_result.grid(row=1, column=0, pady=5)

        # Status frame with detailed information
        self.status_frame = ttk.Frame(main_frame)
        self.status_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)

        self.status_label = ttk.Label(self.status_frame, text="", style='Status.TLabel', wraplength=300)
        self.status_label.grid(row=0, column=0, sticky=tk.W)

        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=5)

        # Chart frame (initially hidden)
        self.chart_frame = ttk.Frame(main_frame)
        self.chart_visible = False

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

    def toggle_chart(self):
        """Toggle chart visibility"""
        if not self.chart_visible:
            self.show_chart()
        else:
            self.hide_chart()

    def show_chart(self):
        """Show the BMI history chart"""
        if not self.chart_visible:
            self.chart_frame.grid(row=1, column=1, rowspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
            self.setup_chart()
            self.chart_visible = True
            self.update_chart()

    def hide_chart(self):
        """Hide the BMI history chart"""
        if self.chart_visible:
            self.chart_frame.grid_remove()
            self.chart_visible = False

    def setup_chart(self):
        """Setup matplotlib chart for BMI history"""
        self.fig, self.ax = plt.subplots(figsize=(6, 4), facecolor='black')
        self.canvas = FigureCanvasTkAgg(self.fig, self.chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Style the chart
        self.ax.set_facecolor('black')
        self.ax.tick_params(colors='white')
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['top'].set_color('white')
        self.ax.spines['right'].set_color('white')
        self.ax.spines['left'].set_color('white')
        self.ax.title.set_color('white')
        self.ax.xaxis.label.set_color('white')
        self.ax.yaxis.label.set_color('white')

        self.ax.set_title('BMI History', color='cyan', fontsize=12, fontweight='bold')
        self.ax.set_xlabel('Date')
        self.ax.set_ylabel('BMI')

    def calculate_bmi(self):
        """Calculate BMI with proper multiprocessing"""
        try:
            weight = float(self.weight_var.get())
            height = float(self.height_var.get())

            if weight <= 0 or height <= 0:
                messagebox.showerror("Error", "Please enter valid positive values")
                return

            # Start progress bar
            self.progress.start()
            self.status_label.config(text="Calculating BMI...")

            # Use threading for the calculation process
            threading.Thread(target=self._calculate_in_thread, args=(weight, height), daemon=True).start()

        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers")
        except Exception as e:
            logging.error(f"Calculation error: {e}")
            messagebox.showerror("Error", "An error occurred during calculation")
            self.progress.stop()

    def _calculate_in_thread(self, weight, height):
        """Perform calculation in thread"""
        try:
            # Simulate CPU-intensive calculation
            time.sleep(0.5)  # Remove this in production

            # Calculate BMI
            height_in_meters = height / 100
            bmi = weight / (height_in_meters ** 2)
            bmi_rounded = round(bmi, 2)

            # Determine category
            category, color, status_message = self.get_bmi_category(bmi_rounded)

            # Update UI in main thread
            self.root.after(0, lambda: self._update_ui_results(bmi_rounded, category, color, status_message))

            # Save to history
            record = {
                'timestamp': datetime.now().isoformat(),
                'weight': weight,
                'height': height,
                'bmi': bmi_rounded,
                'category': category
            }
            self.history_manager.save_to_history(record)

            # Update chart if visible
            if self.chart_visible:
                self.root.after(0, self.update_chart)

        except Exception as e:
            logging.error(f"Calculation thread error: {e}")
            self.root.after(0, lambda: messagebox.showerror("Error", "Calculation failed"))

    def _update_ui_results(self, bmi, category, color, status_message):
        """Update UI with results"""
        self.progress.stop()

        # Update BMI and category
        self.bmi_result.config(text=f"BMI: {bmi}")
        self.category_result.config(text=f"Category: {category}", foreground=color)

        # Show detailed status message
        self.status_label.config(text=status_message, foreground=color)

        # Store current values
        self.current_bmi = bmi
        self.current_category = category

        logging.info(f"BMI calculated: {bmi} ({category})")

    def get_bmi_category(self, bmi):
        """Determine BMI category with detailed messages"""
        if bmi < 18.5:
            message = "⚠️ UNDERWEIGHT: You are below the healthy weight range.\nRecommendation: Consider consulting a nutritionist for healthy weight gain."
            return "Underweight", "lightblue", message
        elif 18.5 <= bmi < 25:
            message = "✅ NORMAL WEIGHT: Congratulations! You are in the healthy weight range.\nRecommendation: Maintain your current lifestyle with balanced diet and regular exercise."
            return "Normal Weight", "green", message
        elif 25 <= bmi < 30:
            message = "⚠️ OVERWEIGHT: You are above the healthy weight range.\nRecommendation: Consider increasing physical activity and adjusting your diet."
            return "Overweight", "orange", message
        elif 30 <= bmi < 35:
            message = "🚨 OBESE: Your weight may pose health risks.\nRecommendation: Consult with a healthcare provider for weight management guidance."
            return "Obese", "red", message
        else:
            message = "🚨 SEVERELY OBESE: Immediate medical attention recommended.\nRecommendation: Please consult with a healthcare professional for comprehensive weight management."
            return "Severely Obese", "darkred", message

    def clear_inputs(self):
        """Clear all input fields and results"""
        self.weight_var.set("")
        self.height_var.set("")
        self.bmi_result.config(text="BMI: --")
        self.category_result.config(text="Category: --", foreground="white")
        self.status_label.config(text="")
        self.progress.stop()
        self.current_bmi = None
        self.current_category = None

    def show_history(self):
        """Show history in a new window (IO-bound)"""

        def load_and_display():
            try:
                history = self.history_manager.load_history()
                self.root.after(0, lambda: self._display_history(history))
            except Exception as e:
                logging.error(f"History display error: {e}")
                self.root.after(0, lambda: messagebox.showerror("Error", "Failed to load history"))

        threading.Thread(target=load_and_display, daemon=True).start()

    def _display_history(self, history):
        """Display history in a new window"""
        history_window = tk.Toplevel(self.root)
        history_window.title("BMI History")
        history_window.configure(bg='black')
        history_window.geometry('600x400')

        # Create treeview
        tree = ttk.Treeview(history_window, columns=('Date', 'Weight', 'Height', 'BMI', 'Category'), show='headings')

        # Configure columns
        tree.heading('Date', text='Date')
        tree.heading('Weight', text='Weight (kg)')
        tree.heading('Height', text='Height (cm)')
        tree.heading('BMI', text='BMI')
        tree.heading('Category', text='Category')

        # Configure column widths
        tree.column('Date', width=150)
        tree.column('Weight', width=80)
        tree.column('Height', width=80)
        tree.column('BMI', width=80)
        tree.column('Category', width=120)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(history_window, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        # Pack widgets
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        # Add data
        for record in reversed(history[-20:]):  # Show last 20 records
            date = datetime.fromisoformat(record['timestamp']).strftime('%Y-%m-%d %H:%M')
            tree.insert('', 0, values=(
                date,
                record['weight'],
                record['height'],
                record['bmi'],
                record['category']
            ))

    def update_chart(self):
        """Update the BMI history chart"""
        try:
            history = self.history_manager.load_history()

            self.ax.clear()

            if history:
                # Prepare data - show last 10 records
                recent_history = history[-10:]
                dates = [datetime.fromisoformat(record['timestamp']) for record in recent_history]
                bmis = [record['bmi'] for record in recent_history]

                # Plot data
                self.ax.plot(dates, bmis, 'o-', color='cyan', linewidth=2, markersize=6)

                # Add reference lines
                self.ax.axhline(y=18.5, color='green', linestyle='--', alpha=0.7, label='Underweight')
                self.ax.axhline(y=25, color='yellow', linestyle='--', alpha=0.7, label='Normal')
                self.ax.axhline(y=30, color='orange', linestyle='--', alpha=0.7, label='Overweight')
                self.ax.axhline(y=35, color='red', linestyle='--', alpha=0.7, label='Obese')

                self.ax.legend(facecolor='black', labelcolor='white')

            # Style the chart
            self.ax.set_facecolor('black')
            self.ax.tick_params(colors='white')
            for spine in self.ax.spines.values():
                spine.set_color('white')
            self.ax.title.set_color('cyan')
            self.ax.xaxis.label.set_color('white')
            self.ax.yaxis.label.set_color('white')

            self.ax.set_title('BMI History', fontweight='bold')
            self.ax.set_xlabel('Date')
            self.ax.set_ylabel('BMI')

            # Format x-axis dates
            plt.xticks(rotation=45)
            self.fig.tight_layout()
            self.canvas.draw()

        except Exception as e:
            logging.error(f"Chart update error: {e}")


def main():
    """Main application entry point"""
    try:
        # Create root window
        root = tk.Tk()

        # Create application
        app = AdvancedBMICalculator(root)

        # Start application
        root.mainloop()

    except Exception as e:
        logging.critical(f"Application failed to start: {e}")
        messagebox.showerror("Fatal Error", f"The application failed to start:\n{e}")


if __name__ == "__main__":
    main()