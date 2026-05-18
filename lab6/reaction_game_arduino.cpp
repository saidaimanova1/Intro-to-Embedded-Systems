#include "Servo.h"
#include <Stepper.h>

const int stepsPerRevolution = 2048;  // 28BYJ-48

Stepper myStepper(stepsPerRevolution, 11, 9, 10, 8);
Servo myservo;

int servoPin = 12; 
int buzzer = 3;
int buttonPlayer1 = 6;
int buttonPlayer2 = 5;

// Game variables
int score1 = 0;
int score2 = 0;

unsigned long startTime;
unsigned long reactionTime1;
unsigned long reactionTime2;

int stepperPosition = 0;

void setup() {
  Serial.begin(9600);

  myStepper.setSpeed(10);
  myservo.attach(servoPin);

  pinMode(buttonPlayer1, INPUT_PULLUP);
  pinMode(buttonPlayer2, INPUT_PULLUP);
  pinMode(buzzer, OUTPUT);

  randomSeed(analogRead(A0));

  myservo.write(90); // neutral

  Serial.println("GAME STARTS AUTOMATICALLY");
}

void loop() {
  resetGame();
  playGame();

  // small pause before restarting game
  delay(5000);
}

void playGame() {
  
  myservo.write(90);

  while (score1 < 3 && score2 < 3) {

    Serial.println("NEW ROUND");

    // added initial position for servo (in the middle)

    int delayTime = random(1000, 20001); // 1–20 sec
    unsigned long waitStart = millis();

    // WAIT PHASE (false start detection)
    while (millis() - waitStart < delayTime) {

      if (digitalRead(buttonPlayer1) == LOW) {
        Serial.println("FALSE START P1");
        score2++;
        updateStepper(2);
        delay(1000);
        return;
      }

      if (digitalRead(buttonPlayer2) == LOW) {
        Serial.println("FALSE START P2");
        score1++;
        updateStepper(1);
        delay(1000);
        return;
      }
    }

    // BUZZER SIGNAL
    tone(buzzer, 1000);
    delay(200);
    noTone(buzzer);

    startTime = millis();

    bool p1Pressed = false;
    bool p2Pressed = false;

    // REACTION PHASE
    while (!p1Pressed || !p2Pressed) {

      if (!p1Pressed && digitalRead(buttonPlayer1) == LOW) {
        reactionTime1 = millis() - startTime;
        p1Pressed = true;
      }

      if (!p2Pressed && digitalRead(buttonPlayer2) == LOW) {
        reactionTime2 = millis() - startTime;
        p2Pressed = true;
      }
    }

    // DETERMINE WINNER
    if (reactionTime1 < reactionTime2) {
      score1++;
      Serial.print("P1 WIN: ");
      Serial.println(reactionTime1);
      moveServo(1);
      updateStepper(1);
    } 
    else {
      score2++;
      Serial.print("P2 WIN: ");
      Serial.println(reactionTime2);
      moveServo(2);
      updateStepper(2);
    }

    delay(1500);
  }

  // FINAL WINNER
  if (score1 == 3) {
    Serial.println("GAME WINNER: P1");
  } else {
    Serial.println("GAME WINNER: P2");
  }

  victorySpin();
}

void moveServo(int player) {
  if (player == 1) {
    myservo.write(0);
  } else {
    myservo.write(180);
  }
}

void updateStepper(int player) {
  if (player == 1) {
    myStepper.step(50);
    stepperPosition += 50;
  } else {
    myStepper.step(-50);
    stepperPosition -= 50;
  }
}

void victorySpin() {
  myStepper.step(stepsPerRevolution);
}

void resetGame() {
  score1 = 0;
  score2 = 0;
  myStepper.step(-stepperPosition);
  stepperPosition = 0;

  myservo.write(90);
}
