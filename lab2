int white = 9;   // White LED pin
int red = 11;    // Red LED pin
int blue = 6;    // Blue LED pin
int green = 10;  // Green LED pin

int xPin = A0;   // Joystick X-axis (analog input)
int yPin = A1;   // Joystick Y-axis (analog input)

// Threshold range to detect center position
int centerMax = 530;
int centerMin = 490;

void setup() {
  
   Serial.begin(9600);   // Start serial communication

   // Set joystick pins as input
   pinMode(xPin, INPUT);
   pinMode(yPin, INPUT);

   // (Optional but recommended) Set LED pins as output
   pinMode(red, OUTPUT);
   pinMode(green, OUTPUT);
   pinMode(blue, OUTPUT);
   pinMode(white, OUTPUT);
}

void loop() {
  
  // Read joystick analog values (0–1023)
  int xVal = analogRead(xPin);
  int yVal = analogRead(yPin);
  
  // Debug (optional)
  // Serial.print(xVal);
  // Serial.print("|");
  // Serial.println(yVal);
  
  // LEFT → X is low, Y is centered
  if ((xVal < centerMin) && (centerMin < yVal && yVal < centerMax)){
    Serial.println("LEFT");

    digitalWrite(green, HIGH); // Turn ON green LED
    digitalWrite(red, LOW);
    digitalWrite(blue, LOW);
    digitalWrite(white, LOW);
  }
    
  // RIGHT → X is high, Y is centered
  else if ((xVal > centerMax) && (centerMin < yVal && yVal < centerMax)){
    Serial.println("RIGHT");

    digitalWrite(green, LOW);
    digitalWrite(red, LOW);
    digitalWrite(blue, HIGH); // Turn ON blue LED
    digitalWrite(white, LOW);
  }
    
  // UP → Y is low, X is centered
  else if ((yVal < centerMin)&& (centerMin < xVal && xVal < centerMax)){
    Serial.println("UP");

    digitalWrite(green, LOW);
    digitalWrite(red, LOW);
    digitalWrite(blue, LOW);
    digitalWrite(white, HIGH); // Turn ON white LED
  }
    
  // DOWN → Y is high, X is centered
  else if ((yVal > centerMax)&& (centerMin < xVal && xVal < centerMax) ){
    Serial.println("DOWN");

    digitalWrite(green, LOW);
    digitalWrite(red, HIGH); // Turn ON red LED
    digitalWrite(blue, LOW);
    digitalWrite(white, LOW);
  }
    
  // CENTER → both X and Y are within center range
  else if ((yVal > centerMin && yVal < centerMax)&&(xVal > centerMin && xVal < centerMax)){
    Serial.println("CENTER");

    // Turn OFF all LEDs
    digitalWrite(green, LOW);
    digitalWrite(red, LOW);
    digitalWrite(blue, LOW);
    digitalWrite(white, LOW);
  }

  // CORNER → joystick moved diagonally
  else{
    Serial.println("CORNER");
  }
}
