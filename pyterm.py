
import tkinter as tk
import tkinter.scrolledtext
import tkinter.ttk as ttk
import glob
import serial
import threading
import queue

class SerialController:
    def __init__(self):
        self.serial = None

    def _send_worker(self):
        while True:
            item = self.send_queue.get()
            if (item is None) or (not self.serial.isOpen()):
                break
            try:
                self.serial.write(item)
            except Exception as ex:
                print("send worker exception: ", ex)
                break
            
    def connect(self, device, baudrate):
        try:
            self.serial = serial.Serial(device, baudrate=baudrate)
            if self.serial.isOpen():
                self.send_queue = queue.Queue()
                self.send_thread = threading.Thread(target=self._send_worker)
                self.send_thread.start()
                return True
            else:
                return False
        except Exception as ex:
            print("serial error: ", ex)
            return False
    
    def disconnect(self):
        if self.serial is not None:
            if self.send_queue is not None:
                self.send_queue.put(None)
            self.serial.close()
            return not self.serial.isOpen()
        return False
    
    def is_connected(self):
        return (self.serial is not None) and self.serial.isOpen()

    def receive_noblock(self):
        return self.serial.read_all()
    
    def send_noblock(self, message):
        self.send_queue.put(message)


class Application(ttk.Frame):
    LINE_ENDING_OPTIONS_DICT = {"None": "", "LF": "\n", "CR": "\r", "CR+LF": "\r\n"}
    LINE_ENDING_DEFAULT_INDEX = 0
    BUADRATE_OPTIONS = (9600, 19200, 115200, 1000000, 2000000, 4000000, 12000000)
    BAUDRATE_DEFAULT_INDEX = 6

    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        
        self.serial_ctrl = SerialController()
        self.master.protocol("WM_DELETE_WINDOW", self.handle_cleanup)

        self.pack()
        self.create_widgets()
        self.handle_serial_devices_refresh()

    def handle_cleanup(self):
        self.serial_ctrl.disconnect()
        self.master.destroy()

    def create_widgets(self):

        # Window resize constraints
        self.master.rowconfigure(0, weight=1, pad=5)
        self.master.columnconfigure(0, weight=1, pad=5)

        # Root grid resize constraints
        self.grid(sticky=tk.NSEW)
        self.rowconfigure(0, weight=0, pad=5)  # port settings
        self.rowconfigure(1, weight=1, pad=5)  # received text
        self.rowconfigure(2, weight=1, pad=5)  # sent text
        self.rowconfigure(3, weight=0, pad=5)  # to send
        self.columnconfigure(0, weight=1, pad=5)

        ###
        # Serial port settings row
        self.serial_grid = tk.Frame(self)
        self.serial_grid.grid(row=0, column=0, sticky=tk.NSEW)
        self.serial_grid.columnconfigure(0, weight=0, pad=5)
        self.serial_grid.columnconfigure(1, weight=0, pad=5)
        self.serial_grid.columnconfigure(2, weight=1, pad=5)
        self.serial_grid.columnconfigure(3, weight=0, pad=5)
        self.serial_grid.columnconfigure(4, weight=0, pad=5)
        self.serial_grid.columnconfigure(5, weight=0, pad=5)
        self.serial_grid.columnconfigure(6, weight=0, pad=5)

        self.btn_refresh = ttk.Button(self.serial_grid)
        self.btn_refresh.grid(row=0, column=0, sticky=tk.NSEW)
        self.btn_refresh["text"] = "Refresh"
        self.btn_refresh["command"] = self.handle_serial_devices_refresh

        self.lbl_1 = ttk.Label(self.serial_grid, text="Serial Device:")
        self.lbl_1.grid(row=0, column=1, sticky=tk.NSEW)

        self.cbx_serial_device = ttk.Combobox(self.serial_grid)
        self.cbx_serial_device.grid(row=0, column=2, sticky=tk.NSEW)

        self.lbl_2 = ttk.Label(self.serial_grid, text="Baudrate:")
        self.lbl_2.grid(row=0, column=3, sticky=tk.NSEW)

        self.cbx_serial_baudrate = ttk.Combobox(self.serial_grid)
        self.cbx_serial_baudrate["values"] = Application.BUADRATE_OPTIONS
        self.cbx_serial_baudrate.current(Application.BAUDRATE_DEFAULT_INDEX)
        self.cbx_serial_baudrate.grid(row=0, column=4, sticky=tk.NSEW)

        self.btn_connect = ttk.Button(self.serial_grid)
        self.btn_connect["text"] = "Connect"
        self.btn_connect["command"] = self.handle_connect
        self.btn_connect.grid(row=0, column=5, sticky=tk.NSEW)

        self.btn_disconnect = ttk.Button(self.serial_grid)
        self.btn_disconnect["text"] = "Disconnect"
        self.btn_disconnect["command"] = self.handle_disconnect
        self.btn_disconnect.grid(row=0, column=6, sticky=tk.NSEW)
        ###

        ###
        # Received text panel
        self.receive_grid = tk.Frame(self)
        self.receive_grid.grid(row=1, column=0, sticky=tk.NSEW)
        self.receive_grid.rowconfigure(0, weight=0, pad=5)
        self.receive_grid.rowconfigure(1, weight=1, pad=5)
        self.receive_grid.columnconfigure(0, weight=1, pad=5)

        self.lbl_3 = ttk.Label(self.receive_grid, text="Received Data:")
        self.lbl_3.grid(row=0, column=0, sticky=tk.NSEW)

        self.txt_received = tk.scrolledtext.ScrolledText(self.receive_grid)
        self.txt_received.grid(row=1, column=0, sticky=tk.NSEW)
        self.txt_received["state"] = tk.DISABLED
        ###

        ###
        # Sent text panel
        self.send_grid = tk.Frame(self)
        self.send_grid.grid(row=2, column=0, sticky=tk.NSEW)
        self.send_grid.rowconfigure(0, weight=0, pad=5)
        self.send_grid.rowconfigure(1, weight=1, pad=5)
        self.send_grid.rowconfigure(2, weight=0, pad=5)
        self.send_grid.columnconfigure(0, weight=1, pad=5)

        self.lbl_4 = ttk.Label(self.send_grid, text="Sent Data:")
        self.lbl_4.grid(row=0, column=0, sticky=tk.NSEW)

        self.txt_sent = tk.scrolledtext.ScrolledText(self.send_grid)
        self.txt_sent.grid(row=1, column=0, sticky=tk.NSEW)
        self.txt_sent["state"] = tk.DISABLED
        ###

        ###
        # To send panel
        self.tosend_grid = tk.Frame(self)
        self.tosend_grid.grid(row=3, column=0, sticky=tk.NSEW)
        self.tosend_grid.rowconfigure(0, weight=1, pad=5)
        self.tosend_grid.columnconfigure(0, weight=0, pad=5)
        self.tosend_grid.columnconfigure(1, weight=1, pad=5)
        self.tosend_grid.columnconfigure(2, weight=0, pad=5)
        self.tosend_grid.columnconfigure(3, weight=0, pad=5)

        self.lbl_5 = ttk.Label(self.tosend_grid, text="Send: ")
        self.lbl_5.grid(row=0, column=0, sticky=tk.NSEW)

        self.ent_tosend = ttk.Entry(self.tosend_grid)
        self.ent_tosend.grid(row=0, column=1, sticky=tk.NSEW)
        
        self.cbx_line_endings = ttk.Combobox(self.tosend_grid)
        self.cbx_line_endings.grid(row=0, column=2, sticky=tk.NSEW)
        self.cbx_line_endings["values"] = list(Application.LINE_ENDING_OPTIONS_DICT.keys())
        self.cbx_line_endings.current(Application.LINE_ENDING_DEFAULT_INDEX)
        self.cbx_line_endings["state"] = "readonly"

        self.btn_send = ttk.Button(self.tosend_grid)
        self.btn_send.grid(row=0, column=3, sticky=tk.NSEW)
        self.btn_send["text"] = "Send"
        self.btn_send["command"] = self.handle_serial_send
        ###

        # Set disconnected GUI state
        self.btn_refresh["state"] = tk.NORMAL
        self.cbx_serial_device["state"] = tk.NORMAL
        self.cbx_serial_baudrate["state"] = tk.NORMAL
        self.btn_connect["state"] = tk.NORMAL
        self.ent_tosend["state"] = tk.DISABLED
        self.btn_send["state"] = tk.DISABLED
        self.btn_disconnect["state"] = tk.DISABLED

    def enumerate_serial_devices(self):
        return glob.glob("/dev/tty*")

    def handle_serial_devices_refresh(self):
        serial_devices = self.enumerate_serial_devices()
        self.cbx_serial_device["values"] = serial_devices
        if len(serial_devices) > 0:
            self.cbx_serial_device.current(0)

    def handle_connect(self):
        device = self.cbx_serial_device.get()
        try:
            baudrate = int(self.cbx_serial_baudrate.get())
        except ValueError:
            print("Baudrate not number")
            return
        
        if self.serial_ctrl.connect(device, baudrate):
            self.btn_refresh["state"] = tk.DISABLED
            self.cbx_serial_device["state"] = tk.DISABLED
            self.cbx_serial_baudrate["state"] = tk.DISABLED
            self.btn_connect["state"] = tk.DISABLED
            self.ent_tosend["state"] = tk.NORMAL
            self.btn_send["state"] = tk.NORMAL
            self.btn_disconnect["state"] = tk.NORMAL
            self.master.after(100, self.handle_serial_receive)

    def handle_disconnect(self):
        if self.serial_ctrl.disconnect():
            self.btn_refresh["state"] = tk.NORMAL
            self.cbx_serial_device["state"] = tk.NORMAL
            self.cbx_serial_baudrate["state"] = tk.NORMAL
            self.btn_connect["state"] = tk.NORMAL
            self.ent_tosend["state"] = tk.DISABLED
            self.btn_send["state"] = tk.DISABLED
            self.btn_disconnect["state"] = tk.DISABLED

    def handle_serial_receive(self):
        if self.serial_ctrl.is_connected():
            msg = self.serial_ctrl.receive_noblock().decode()
            self.txt_received["state"] = tk.NORMAL
            self.txt_received.insert(tk.END, msg)
            self.txt_received["state"] = tk.DISABLED
            self.master.after(100, self.handle_serial_receive)
    
    def handle_serial_send(self):
        if self.serial_ctrl.is_connected():
            line_ending = Application.LINE_ENDING_OPTIONS_DICT[self.cbx_line_endings.get()]
            msg = self.ent_tosend.get() + line_ending
            self.txt_sent["state"] = tk.NORMAL
            self.txt_sent.insert(tk.END, msg)
            self.txt_sent["state"] = tk.DISABLED
            self.serial_ctrl.send_noblock(msg.encode())


root = tk.Tk()
app = Application(master=root)
app.mainloop()
