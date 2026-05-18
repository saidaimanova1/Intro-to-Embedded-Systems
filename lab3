#include <LiquidCrystal.h> // LCD library
#include <Wire.h>          // I2C communication
#include <uRTCLib.h>       // RTC module library

// RTC object (I2C address 0x68)
uRTCLib rtc(0x68);

// LCD pin connections
const int rs = 12, en = 11, d4 = 5, d5 = 4, d6 = 3, d7 = 2;
LiquidCrystal lcd(rs, en, d4, d5, d6, d7);

// Timer variables
unsigned long seconds = 0;     // Current seconds value from RTC
unsigned long lastSecond = 0;  // Stores last valid second

// Button handling
static bool buttonLastState = false; // Toggle state (start/stop)
int buttonPin = A0;                 // Button connected to A0

// LEDs
int greenLed = 9;
int redLed = 8;

/* =========================================================
   BUTTON FUNCTION WITH DEBOUNCING
   ========================================================= */
bool buttonPressed(){
  static bool last = HIGH;              // Last button state
  static unsigned long tLastChange = 0; // Time of last change
  static bool armed = true;             // Prevent multiple triggers

  bool now = digitalRead(buttonPin);    // Read current button state

  // Detect change in button state
  if (now != last) {
    tLastChange = millis();             // Reset debounce timer
    last = now;
  }

  // Check if stable for 30 ms (debounce)
  if ((millis() - tLastChange) > 30) {
    if (last == LOW && armed) {         // Button pressed (active LOW)
      armed = false;
      return true;                      // Valid press detected
    }
    if (last == HIGH) armed = true;     // Reset when released
  }
  return false;
}

void setup() {

  Serial.begin(9600); // Start serial communication

  // Initialize LCD (16 columns, 2 rows)
  lcd.begin(16, 2);
  lcd.print("10 SECONDS GAME"); // Display title

  // Set LED pins as output
  pinMode(greenLed, OUTPUT);
  pinMode(redLed, OUTPUT);

  // Set button pin as input
  pinMode(buttonPin, INPUT);

  // Initialize I2C communication
  Wire.begin();
  URTCLIB_WIRE.begin();
}

void loop() {

  rtc.refresh();                // Update RTC values
  bool pressed = buttonPressed(); // Check if button pressed
  seconds = rtc.second();       // Get current seconds from RTC

  // Toggle game state when button is pressed
  if (pressed) {
    buttonLastState = !buttonLastState;
  }

  /* =========================================================
     IDLE MODE (COUNTING TIME)
     ========================================================= */
  if (!buttonLastState){
  
    // Reset timer if it exceeds 10 seconds
    if (seconds > 10){
      rtc.set(0, 0, 0, 0, 0, 0, 26); // Reset RTC time
      seconds  = 0;
    }

    // Save last second value
    lastSecond = seconds;
  }

  /* =========================================================
     GAME MODE (BUTTON PRESSED)
     ========================================================= */
  if(buttonLastState){

    // Freeze time at lastSecond
    rtc.set(lastSecond, rtc.minute(), rtc.hour(),
            rtc.dayOfWeek(), rtc.day(),
            rtc.month(), rtc.year());

    seconds = lastSecond;

    // Check if user stopped exactly at 10 seconds
    if (seconds == 10) {
      Serial.println("Should be green");

      digitalWrite(greenLed, HIGH); // Success → green LED
      digitalWrite(redLed, LOW);
    } 
    else if (seconds != 10){
      Serial.println("Should be red");

      digitalWrite(redLed, HIGH);   // Fail → red LED
      digitalWrite(greenLed, LOW);
    } 
    else {
      // Safety fallback (not really needed)
      Serial.println("nothing");

      digitalWrite(greenLed, LOW);
      digitalWrite(redLed, LOW);
    }
  }

  // Print seconds to Serial Monitor
  Serial.println(seconds);

  // Display seconds on LCD (second row)
  lcd.setCursor(0, 1);
  lcd.print("    ");   // Clear previous value
  lcd.setCursor(0, 1);
  lcd.print(seconds);  // Show current seconds
}
