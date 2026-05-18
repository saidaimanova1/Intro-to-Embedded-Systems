#include <LiquidCrystal.h>          // Library to control 16x2 LCD (HD44780)

// Create an LCD object and tell Arduino which pins are connected to LCD
// LiquidCrystal(rs, en, d4, d5, d6, d7)
LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

const int soundPin = A0;            // Sound sensor OUT connected to Analog pin A0
const int ledPin = 8;               // LED connected to Digital pin 8


// ---------------- THRESHOLD SETTING ----------------
const int threshold = 600;          // If sound value is > 600, we show ALERT and turn LED ON


// ---------------- NON-BLOCKING TIMING ----------------
// previousMillis remembers the last time we read the sensor
unsigned long previousMillis = 0;

// interval = how often we read sensor (100 ms)
const long interval = 100;


void setup()
{
  Serial.begin(9600);               // Start serial communication at 9600 baud (for PC/Python)

  pinMode(ledPin, OUTPUT);          // Set LED pin as output so we can turn it ON/OFF

  lcd.begin(16,2);                  // Initialize LCD with 16 columns and 2 rows
  lcd.clear();                      // Clear LCD screen

  lcd.setCursor(0,0);               // Move cursor to row 0, column 0
  lcd.print("Sound Monitor");       // Print title on first line
}


void loop()
{
  unsigned long currentMillis = millis();   // millis() gives time since Arduino started (in ms)

  // We only read sensor if 100 ms has passed (non-blocking style)
  if(currentMillis - previousMillis >= interval)
  {
    previousMillis = currentMillis;         // Update last read time

    int soundValue = analogRead(soundPin);  // Read sound sensor (0–1023)

    // ---------------- LCD DISPLAY ----------------
    lcd.setCursor(0,1);                     // Go to second line
    lcd.print("Lvl:");                      // Show label
    lcd.print(soundValue);                  // Print current sound value
    lcd.print("    ");                      // Extra spaces to erase old digits if value shrinks

    // ---------------- SERIAL OUTPUT ----------------
    // Python GUI expects this format: SOUND:<number>
    Serial.print("SOUND:");
    Serial.println(soundValue);

    // ---------------- THRESHOLD CHECK ----------------
    if(soundValue > threshold)              // If sound level is too high
    {
      digitalWrite(ledPin, HIGH);           // Turn ON LED

      lcd.setCursor(10,1);                  // Move cursor near end of line 2
      lcd.print("ALERT");                   // Show "ALERT"
    }
    else                                    // If sound is normal
    {
      digitalWrite(ledPin, LOW);            // Turn OFF LED

      lcd.setCursor(10,1);                  // Same place where ALERT was
      lcd.print("     ");                   // Print spaces to clear ALERT word
    }
  }
}
