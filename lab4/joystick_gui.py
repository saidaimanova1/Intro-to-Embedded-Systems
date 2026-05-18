import sys                    # Gives access to system-specific parameters (sys.argv, sys.exit)
import time                   # Used for time measurement and delays
import serial                 # pyserial library for serial communication with Arduino
import serial.tools.list_ports  # Used to automatically detect available COM ports

from PyQt6.QtCore import QTimer  #runs a function repeatedly
from PyQt6.QtWidgets import ( #these are GUI frameworks: boxes, frames, buttons
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QProgressBar
)##GUI elements


BAUD = 9600  #Serial speed between Arduino and PC

def auto_detect_port():
    ports = list(serial.tools.list_ports.comports())  # Get list of all COM ports

    for p in ports: #Check each port one by one.
        if "Arduino" in p.description or "CH340" in p.description:
            print(f"Auto-detected Arduino on {p.device}") # Print detected port
            return p.device  # Return port name (example: COM7)

    print("No Arduino found!")  # If nothing found
    return None  # Return None if no Arduino detected


def parse_arduino_line(line: str):
    line = line.strip() #Removes spaces/newline from start/end.
    if not line:
        return None

    if "|" not in line:
        return None

    try:
        x_str, y_str = line.split("|")
        x_v = float(x_str.strip())
        y_v = float(y_str.strip())

        #Define joystick center zone
        centerMin = 490
        centerMax = 530

        if x_v < centerMin and centerMin < y_v < centerMax:
            direction = "LEFT"
        elif x_v > centerMax and centerMin < y_v < centerMax:
            direction = "RIGHT"
        elif y_v < centerMin and centerMin < x_v < centerMax:
            direction = "UP"
        elif y_v > centerMax and centerMin < x_v < centerMax:
            direction = "DOWN"
        else:
            direction = "CENTER"#If none of the above conditions match

        # Convert to “V” for GUI scaling if you want
        x_v = x_v / 100.0
        y_v = y_v / 100.0

        return x_v, y_v, direction

    except:
        return None

class Lab4JoystickGUI(QWidget):

    def __init__(self):
        super().__init__()  # Initialize parent QWidget

        self.setWindowTitle("Lab 4 — Joystick Monitor")  # Window title

        self.ser = None #store the serial connection object,first there is no connection
        self.port = None #store the port name 
        self.is_running = False #test is running or not
        self.last_time = None  # Used to calculate Hz

        main = QVBoxLayout()  # creates a vertical layout.

        row1 = QHBoxLayout()  # Creates a horizontal layout.

        #creates buttons and adds them to the horizontal layout. The stop button is disabled at the start.
        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)  
        row1.addWidget(self.start_btn)
        row1.addWidget(self.stop_btn)
        row1.addStretch(1)  # Push buttons to left

        main.addLayout(row1)#Adds the button row to the main vertical layout.

        center = QHBoxLayout()  # Main center area


        #Creates a box container.Draws a border around the frame.
        data_frame = QFrame()
        data_frame.setFrameShape(QFrame.Shape.Box)  
        data_layout = QVBoxLayout() #Inside the frame, elements will be stacked vertically.

        title = QLabel("Joystick Position")
        title.setStyleSheet("font-weight: bold;")
        data_layout.addWidget(title)

        # X progress bar/ X joystick position.
        self.bar_x = QProgressBar()
        self.bar_x.setRange(0, 2000)  # Range 0–500
        #Displays text inside the bar, showing current value and max value. %v is replaced by the current value of the bar.
        self.bar_x.setFormat("X: %v / 1023")  
        data_layout.addWidget(self.bar_x)#Adds the X bar to the layout.

        # Y progress bar / Y joystick position.
        self.bar_y = QProgressBar()
        self.bar_y.setRange(0, 1023)
        self.bar_y.setFormat("Y: %v / 1023")
        data_layout.addWidget(self.bar_y)

        data_frame.setLayout(data_layout)#Puts the layout inside the frame.
        center.addWidget(data_frame)#Adds the frame to the center area.



        
        cross = QVBoxLayout()

        self.up = self.block()  # Create square block
        cross.addWidget(self.up)#Adds it to the top.

        mid = QHBoxLayout()#Creates a horizontal layout for the middle row of the cross (left, center, right)

        #Creates three square blocks
        self.left = self.block()
        self.center_block = self.block()
        self.right = self.block()

        #Adds them side-by-side
        mid.addWidget(self.left)
        mid.addWidget(self.center_block)
        mid.addWidget(self.right)

        #Adds the middle row to the cross layout.
        cross.addLayout(mid)

        #Creates the DOWN indicator block
        self.down = self.block()
        cross.addWidget(self.down)#Adds it to the bottom

        center.addLayout(cross)#adds the direction cross to the center area.
        main.addLayout(center)#Adds the entire center section to the main layout.


        #Creates horizontal layout for text info.
        bottom = QHBoxLayout()

        self.x_label = QLabel("X: -")
        self.y_label = QLabel("Y: -")
        self.rate_label = QLabel("Hz: -")  
        self.dir_label = QLabel("Dir: -")

        #Adds all labels to the bottom row.
        bottom.addWidget(self.x_label)
        bottom.addWidget(self.y_label)
        bottom.addWidget(self.rate_label)
        bottom.addWidget(self.dir_label)

        main.addLayout(bottom)#Ads this row to the main layout
        self.setLayout(main)  # Apply layout to window

        #Connect buttons to functions
        self.start_btn.clicked.connect(self.start_test)#Start button is clicked:
        self.stop_btn.clicked.connect(self.stop_test)#Stop button is clicked:

        #Creates a timer that runs repeatedly
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)  # Call tick() every interval
        self.timer.start(20)  # 20 ms (~50 Hz)



    def block(self):
        f = QFrame()
        f.setFrameShape(QFrame.Shape.Box)  # Draw a border around this frame
        f.setMinimumSize(40, 40)  # Square size
        return f



    
    def highlight(self, direction):

        off = ""  # Default style
        on = "background-color: lightgreen;"  # Highlight style

        # Reset all blocks
        self.up.setStyleSheet(off)
        self.down.setStyleSheet(off)
        self.left.setStyleSheet(off)
        self.right.setStyleSheet(off)
        self.center_block.setStyleSheet(off)

        # Highlight correct direction
        if direction == "UP":
            self.up.setStyleSheet(on)
        elif direction == "DOWN":
            self.down.setStyleSheet(on)
        elif direction == "LEFT":
            self.left.setStyleSheet(on)
        elif direction == "RIGHT":
            self.right.setStyleSheet(on)
        else:
            self.center_block.setStyleSheet(on)#center

        self.dir_label.setText(f"Dir: {direction}")



    def open_serial_and_start(self): #start 

        self.port = "COM12"  #where the Arduino is connected
        print(f"Using Arduino port: {self.port}")

        if not self.port:
            print("Cannot start: Arduino port not found.")
            return False

        try:
            # Open serial connection
            self.ser = serial.Serial(self.port, BAUD, timeout=0.2)
            print(f"Connected to {self.port}")
        except Exception as e:
            print("Serial error:", e)
            return False

        time.sleep(2.0)  # Wait for Arduino reset
        self.ser.reset_input_buffer()  # Clear old data

        try:
            self.ser.write(b"START\n")  # Send START command
            self.ser.flush()#send the data immediately, not wait in buffer.
            print("START sent")
            return True
        except Exception as e:
            print("Failed to send START:", e)
            return False

    def close_serial(self):

        if self.ser and self.ser.is_open:
            try:
                self.ser.write(b"STOP\n")  # Tell Arduino to stop
                self.ser.close()           # Close port
            except Exception:
                pass

        self.ser = None



    #Start button is clicked
    def start_test(self):

        if not (self.ser and self.ser.is_open):
            if not self.open_serial_and_start():#Opens the serial connection
                return

        self.is_running = True
        self.start_btn.setEnabled(False)#disables the Start button, test is already running
        self.stop_btn.setEnabled(True)
        self.last_time = None #reset the timer for Hz calculation when starting a new test


    #Stop button is clicked
    def stop_test(self):

        self.is_running = False
        self.close_serial()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)



    def tick(self):

        if not self.is_running or not self.ser:
            return  # Do nothing if not running

        updated = False

        try:
            while self.ser.in_waiting:  # While data exists in buffer

                #convert bytes → text, ignore errors if non-text data is present
                line = self.ser.readline().decode(errors="ignore")
                print("RAW:", repr(line))  # shows hidden characters like \r, \n, etc.

                parsed = parse_arduino_line(line)#Try to extract X, Y, and direction from the line. If the line is not in the expected format, parsed will be None.

                if parsed:
                    x_v, y_v, direction = parsed #returned values into variables
                    self.update_ui(x_v, y_v, direction)
                    updated = True

        except Exception:
            self.stop_test()
            return

        # Calculate frequency (Hz)
        if updated:
            now = time.time()
            if self.last_time:
                hz = 1.0 / (now - self.last_time)
                self.rate_label.setText(f"Hz: {hz:.1f}")
            self.last_time = now

    def update_ui(self, x_v, y_v, direction):

        #label text
        self.x_label.setText(f"X: {x_v:.2f} V")
        self.y_label.setText(f"Y: {y_v:.2f} V")

        # Convert voltage to 0–500 scale
        #never goes above 500, never goes below 0
        self.bar_x.setValue(int(max(0, min(1023, x_v * 100))))
        self.bar_y.setValue(int(max(0, min(1023, y_v * 100))))

        self.highlight(direction)


    def closeEvent(self, e):
        self.stop_test()
        super().closeEvent(e)





if __name__ == "__main__":

    app = QApplication(sys.argv)  # Create Qt application
    w = Lab4JoystickGUI()         # Create main window
    w.resize(1000, 800)           # Set window size
    w.show()                      # Show window
    sys.exit(app.exec())          # Start event loop
