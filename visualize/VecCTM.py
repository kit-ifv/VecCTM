import logging
import tkinter as tk
from json.decoder import JSONDecodeError
from tkinter import messagebox, ttk
import json
import asyncio

from traffic import SimulationHandler
from traffic.SimulationHandler import SimulationType, SimulationHandler
from Visualization import VisualizationType, Visualization


class App:
    async def exec(self):
        self.window = SimulationWindow(asyncio.get_event_loop())
        await self.window.show()


class SimulationWindow(tk.Tk):
    SELECTED_OPTIONS_FILE = "../resources/selected_options.json"

    def __init__(self, loop):
        self.loop = loop
        self.root = tk.Tk()
        self.root.title("VecCTM")
        self.file_selected = False
        # Load saved options
        self.load_options()

        self.visualization = tk.IntVar(self.root, value=self.visualization_selected)
        self.change_visualization_button = None
        self.simulations = []
        self.error_label_text = tk.StringVar(self.root, "")
        self.error_label = tk.Label(self.root, textvariable=self.error_label_text)
        self.error_label.grid(row=0, column=0, columnspan=2, sticky="n", pady=5, padx=5)

        self.visualization_types = VisualizationType.get_types()

        self.simulation_option_frame = self.init_simulation_option_frame()

        self.visualization_option_frame = self.init_visualization_option_frame()

        self.visualization_frame = self.init_visualization_frame()

    async def show(self):
        try:
            while True:
                self.root.update()
                await asyncio.sleep(.05)
        except tk.TclError as ex:
            if "application has been destroyed" not in ex.args[0]:
                raise

    def init_simulation_option_frame(self):
        frame = tk.Frame(self.root)

        self.sim_check = []

        # Create a list of available simulation types
        self.simulation_types = SimulationType.get_types()

        # Create Checkbuttons for each simulation type
        for i, sim_type in enumerate(self.simulation_types):
            self.sim_check.append(tk.IntVar(frame, value=-1))
            cb = tk.Checkbutton(frame, text=sim_type, variable=self.sim_check[i], onvalue=i, offvalue=-1)
            cb.pack(anchor="w", pady=5, padx=5)
        for j in self.selected_options:
            if len(self.sim_check) > j:
                self.sim_check[j].set(j)

        self.file_label_text = tk.StringVar(frame, self.file_path)
        self.file_field = tk.Label(frame, textvariable=self.file_label_text)
        self.file_field.pack(anchor="w", pady=5, padx=5)

        self.file_button = tk.Button(frame, text="Choose File", command=self.choose_file)
        self.file_button.pack(pady=5, padx=5)
        frame.grid(row=1, column=0, sticky="n", pady=5, padx=5)
        return frame

    def init_visualization_option_frame(self):
        frame = tk.Frame(self.root)
        # Create a button to start the simulations
        self.start_button = tk.Button(frame, text="Start Simulations", command=self.start_simulations)
        self.start_button.pack(pady=5, padx=5)

        for i, vtype in enumerate(self.visualization_types):
            vcb = tk.Checkbutton(frame, text=vtype, variable=self.visualization, onvalue=i, offvalue=-1)
            vcb.pack(anchor="w", pady=5, padx=5)
        self.change_visualization_button = tk.Button(frame, text="Change Visualization",
                                                     command=self.change_visualization)
        self.change_visualization_button.pack(pady=5, padx=5)

        self.change_file()
        frame.grid(row=2, column=0, sticky="w", pady=5, padx=5)
        return frame

    def init_visualization_frame(self):
        frame = tk.Frame(self.root)
        self.visualization_frame = tk.Frame(self.root, width=100, height=100)
        self.tabControl = ttk.Notebook(self.visualization_frame)
        self.visualization_frame.grid(row=1, rowspan=2, column=1, columnspan=2, sticky="n", pady=5, padx=5)
        return frame

    def change_visualization(self):
        if SimulationHandler.is_simulating:
            self.error_label_text.set("Simulations are running. Please wait until they are finished.")
            return
        self.visualization_selected = self.visualization.get()
        print(f"{self.visualization_selected}")
        self.save_options()
        messagebox.showinfo("Visualization Changed",
                            f"Visualization changed to {self.visualization_types[self.visualization_selected]}")
        self.visualize_simulations()
        # test = tk.Frame(self.tabControl, width=100, height=100)
        # tlabel = tk.Label(test, text=self.visualization_selected)
        # self.tabControl.add(test, text=self.visualization_types[self.visualization_selected])
        # self.tabControl.pack(expand=1, fill="both")
        #
        # for simulation in self.simulations:
        #     # sim_plot = Visualization.show_results(simulation, self.visualization_types[self.visualization_selected])
        #     sim_plot = tk.Frame()
        #     sim_label = tk.Label(sim_plot, text=simulation)
        #     sim_plot.pack()
        #     self.tabControl.add(sim_plot, text=simulation)

    def choose_file(self):
        self.file_path = tk.filedialog.askopenfilename()
        self.change_file()

    def change_file(self):
        if not self.file_path:
            self.file_selected = False
            self.error_label_text.set("No file selected")
        else:
            self.file_selected = True
            self.error_label_text.set("")
        self.file_label_text.set(self.file_path)
        self.save_options()
    def start_simulations(self):
        self.error_label_text.set("Simulations are running. Please wait until they are finished.")
        self.loop.create_task(self.exec_simulations())

    async def exec_simulations(self):
        # Get selected options

        self.selected_options = [self.sim_check[i].get() for i in range(len(self.simulation_types)) if
                                 self.sim_check[i].get() != -1]

        # Save selected options
        self.save_options()

        # Perform simulations based on selected options
        if not self.file_selected:
            messagebox.showwarning("No File Selected", "Please select a file.")
            return
        if self.selected_options:
            # messagebox.showinfo("Simulations Started",
            #                    f"Simulations of {self.file_path} started for: {', '.join([self.simulation_types[i].get_name() for i in self.selected_options])}")

            self.simulations = SimulationHandler.exec_simulations(
                [self.simulation_types[i] for i in self.selected_options],
                self.file_path)

            if not SimulationHandler.get_all_simulated():
                messagebox.showerror("Error", "An error occurred during the simulation. Please check the log file.")

            self.visualize_simulations()

        else:
            messagebox.showwarning("No Selection", "Please select at least one simulation type.")

        self.error_label_text.set("Simulations finished.")

    def visualize_simulations(self):
        self.visualization_frame.destroy()
        self.visualization_frame = tk.Frame(self.root, width=100, height=100)
        self.visualization_frame.grid(row=2, rowspan=2, column=1, columnspan=2, sticky="n", pady=5, padx=5)
        self.tabControl = ttk.Notebook(self.visualization_frame)
        self.tabControl.grid(row=2, column=1, columnspan=2, sticky="n", pady=5, padx=5)

        for simulation in self.simulations:
            plot_frame = tk.Frame(self.tabControl)  # This frame will be added as a tab
            plot_frame.pack_propagate(False)  # Prevent resizing based on content

            sim_plot = Visualization.show_results(simulation, self.visualization_types[self.visualization_selected], plot_frame)

            #sim_plot_widget = tk.Frame(plot_frame)  # Create a sub-frame for the plot
            #sim_plot_widget.pack(fill=tk.BOTH, expand=True)  # Use pack to layout the plot in the sub-frame
            # sim_plot.grid(row=2, column=1, columnspan=2, sticky="n", pady=5, padx=5)  #.grid(row=0, column=0, sticky="nsew")  # If sim_plot itself uses grid internally

            sim_label = tk.Label(plot_frame, text=simulation.get_name())
            sim_label.pack()  # Pack label below the plot

            self.tabControl.add(plot_frame, text=simulation.get_name())


    def load_options(self):
        try:
            with open(SimulationWindow.SELECTED_OPTIONS_FILE, "r") as file:
                options = json.load(file)
                self.selected_options = options['selected']
                self.file_path = options['file_path']
                self.visualization_selected = options['visualization_selected']
        except FileNotFoundError as ex:
            logging.error(f"File {SimulationWindow.SELECTED_OPTIONS_FILE} not found: {ex}")
            return []
        except JSONDecodeError as ex:
            logging.error(f"File {SimulationWindow.SELECTED_OPTIONS_FILE} is not valid: {ex}")
            self.selected_options = []
            self.file_path = None
            self.visualization_selected = -1
            return

    def save_options(self):
        options = {'selected': self.selected_options, 'file_path': self.file_path,
                   'visualization_selected': self.visualization.get()}
        with open(SimulationWindow.SELECTED_OPTIONS_FILE, "w") as file:
            json.dump(options, file)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(App().exec())
