import sys                      
import time                    
import csv                      # Used to save alert data into a CSV file
from datetime import datetime   # Used to generate real timestamps for logging

import serial                   # PySerial: enables UART/Serial communication with Arduino
import serial.tools.list_ports  # Helps us detect Arduino COM port automatically on Windows

from PyQt6.QtCore import QTimer # QTimer calls a function repeatedly without freezing the GUI
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton
)

import pyqtgraph as pg          


BAUD = 9600                     # Serial speed; MUST match Arduino Serial.begin(9600)
THRESHOLD = 600                 # If sound value > this, we show ALERT and log it
SAMPLES_ON_SCREEN = 200         # How many last samples we keep visible on the plot (sliding window)
UPDATE_MS = 50                  # How often (ms) QTimer triggers serial reading
PORT = None                     # If auto-detect fails, manually set like PORT = "COM7"



def auto_detect_port() -> str | None:
    """
    Searches available serial ports and tries to pick the Arduino port.
    Returns something like "COM7" if found, otherwise returns None.
    """
    ports = list(serial.tools.list_ports.comports())   # Get all COM ports
    for p in ports:
        desc = (p.description or "").lower()           # Port description (device name) in lowercase
        # Common identifiers for Arduino clones: Arduino, CH340, USB Serial
        if "arduino" in desc or "ch340" in desc or "usb serial" in desc:
            return p.device                            # Example: "COM7"
    return None                                       # Arduino not found


class SoundGUI(QWidget):
    def __init__(self):
        super().__init__()  # Initialize QWidget parent class

        # -------- Window settings --------
        self.setWindowTitle("Sound Level Monitor (UART)")  # Title displayed on the window
        self.resize(900, 550)                              # Window size (width, height)

        self.ser = None            # Will store serial.Serial object when connected
        self.running = False       # True if monitoring is active, False when stopped


        main = QVBoxLayout(self)                 # Main layout is vertical (top to bottom)

        self.status = QLabel("Status: stopped")  # Label to show current state to the user
        main.addWidget(self.status)              # Add label to the window

        # -------- Button row --------
        btn_row = QHBoxLayout()                  # Horizontal row for buttons (left to right)
        main.addLayout(btn_row)

        self.start_btn = QPushButton("Start")    # Start monitoring button
        self.stop_btn = QPushButton("Stop")      # Stop monitoring button
        self.stop_btn.setEnabled(False)          # Initially disabled because nothing is running

        btn_row.addWidget(self.start_btn)        # Add Start button to row
        btn_row.addWidget(self.stop_btn)         # Add Stop button to row

        # ===================== LIVE PLOT SETUP =====================

        self.plot = pg.PlotWidget()              # Create a plot area
        main.addWidget(self.plot)                # Put plot into the main layout

        self.plot.setTitle("Live Sound Level")   # Plot title
        self.plot.setLabel("left", "Sound (0–1023)")   # Y-axis label
        self.plot.setLabel("bottom", "Sample #")       # X-axis label
        self.plot.showGrid(x=True, y=True)       # Show grid to make reading easier

        # -------- Data arrays for the plot --------
        self.x = []              # x-axis values: sample number (1,2,3,...)
        self.y = []              # y-axis values: sound sensor readings
        self.sample_idx = 0      # Counts how many samples have been received

        self.curve = self.plot.plot(self.x, self.y)  # Draw line curve using x and y lists

        # -------- Threshold reference line --------
        self.threshold_line = pg.InfiniteLine(pos=THRESHOLD, angle=0)  # Horizontal line at THRESHOLD
        self.plot.addItem(self.threshold_line)                         # Add line to plot

        # ===================== CSV LOGGING SETUP =====================

        # Open CSV file in append mode ("a") so old data is not deleted
        self.csv_file = open("sound_threshold_log.csv", "a", newline="", encoding="utf-8")
        self.csv_writer = csv.writer(self.csv_file)

        # If file is empty, write column headers once
        if self.csv_file.tell() == 0:
            self.csv_writer.writerow(["timestamp", "sound_value"])

        # ===================== TIMER SETUP =====================

        self.timer = QTimer()                      # QTimer triggers events repeatedly
        self.timer.timeout.connect(self.read_serial)  # Every timeout, call read_serial()

        # ===================== BUTTON SIGNALS =====================

        # When Start is clicked -> run start_monitoring()
        self.start_btn.clicked.connect(self.start_monitoring)
        # When Stop is clicked -> run stop_monitoring()
        self.stop_btn.clicked.connect(self.stop_monitoring)


    # ===================== START MONITORING =====================

    def start_monitoring(self):
        """Connect to Arduino serial port and start reading live data."""
        if self.running:
            return  # Prevent starting again if already running

        # Choose COM port: manual PORT if set, otherwise auto-detect
        port = PORT or auto_detect_port()

        if port is None:
            # If Arduino not found, show message and do not start
            self.status.setText("Status: Arduino not found. Set PORT='COMx' in code.")
            return

        # Try to open serial port with BAUD rate
        try:
            self.ser = serial.Serial(port, BAUD, timeout=0.1)  # timeout makes readline non-blocking-ish
        except Exception as e:
            # If COM port cannot open (busy/wrong port), show the error
            self.status.setText(f"Status: cannot open {port}: {e}")
            return

        # Reset plot each time we start (optional)
        self.x.clear()
        self.y.clear()
        self.sample_idx = 0
        self.curve.setData(self.x, self.y)         # Update graph with empty data

        self.running = True                        # Now we are in running mode
        self.timer.start(UPDATE_MS)                # Start timer; read_serial called every UPDATE_MS ms

        # Update buttons to prevent wrong use
        self.start_btn.setEnabled(False)           # Start disabled while running
        self.stop_btn.setEnabled(True)             # Stop enabled while running

        # Show connection info on status label
        self.status.setText(f"Status: running (connected {port} @ {BAUD})")


    # ===================== STOP MONITORING =====================

    def stop_monitoring(self):
        """Stop reading, stop timer, and close serial port to free COM port."""
        if not self.running:
            return  # Nothing to stop if not running

        self.timer.stop()                          # Stop calling read_serial()
        self.running = False

        # Close serial port so Windows releases it
        try:
            if self.ser is not None and self.ser.is_open:
                self.ser.close()
        except:
            pass

        self.ser = None                             # Clear serial object

        # Update buttons
        self.start_btn.setEnabled(True)              # Allow start again
        self.stop_btn.setEnabled(False)

        self.status.setText("Status: stopped")       # Update status label


    def read_serial(self):
        """
        Reads incoming serial lines from Arduino.
        Expected Arduino format: SOUND:<value>
        Updates status label, logs alerts, and updates the plot.
        """
        if not self.running or self.ser is None:
            return  # Safety check

        try:
            # While there is data waiting in serial buffer, read it
            while self.ser.in_waiting:

                # Read one line from serial and decode bytes -> string
                line = self.ser.readline().decode(errors="ignore").strip()

                # Ignore lines not in expected format
                if not line.startswith("SOUND:"):
                    continue

                # Extract number after "SOUND:"
                try:
                    value = int(line.split(":", 1)[1])
                except ValueError:
                    continue  # Skip if conversion fails

                if value > THRESHOLD:
                    # ALERT condition: update status text and log it to CSV
                    self.status.setText(f"Status: ALERT | Sound={value} (>{THRESHOLD})")

                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Current timestamp
                    self.csv_writer.writerow([ts, value])              # Save to CSV
                    self.csv_file.flush()                               # Ensure data is written immediately
                else:
                    # Normal condition
                    self.status.setText(f"Status: running | Sound={value} (threshold {THRESHOLD})")

                self.sample_idx += 1                 # Increase sample counter
                self.x.append(self.sample_idx)       # Add x value
                self.y.append(value)                 # Add y value

                # Keep only last SAMPLES_ON_SCREEN points (sliding window)
                if len(self.x) > SAMPLES_ON_SCREEN:
                    self.x = self.x[-SAMPLES_ON_SCREEN:]
                    self.y = self.y[-SAMPLES_ON_SCREEN:]

                self.curve.setData(self.x, self.y)   # Redraw curve with new data

        except Exception as e:
            # If serial disconnects or another error happens
            self.status.setText(f"Status: serial read error: {e}")
            self.stop_monitoring()                   # Stop safely


    def closeEvent(self, event):
        
        self.stop_monitoring()  # Stop timer and serial first

        try:
            self.csv_file.close()  # Close CSV file
        except:
            pass

        event.accept()  # Allow window to close normally


if __name__ == "__main__":
    app = QApplication(sys.argv)   # Create Qt application object (must exist for GUI)
    w = SoundGUI()                 # Create main window from SoundGUI class
    w.show()                       # Show the window on screen
    sys.exit(app.exec())           # Start Qt event loop (keeps GUI running)
