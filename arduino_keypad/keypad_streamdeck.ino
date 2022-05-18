#include <Keypad.h>

const byte ROWS = 4;
const byte COLS = 3;
char keys[ROWS][COLS] = {
  {'1','2','3'},
  {'4','5','6'},
  {'7','8','9'},
  {'*','0','#'}
};

// LEONARDNO PINS
// byte rowPins[ROWS] = {9, 10,11,12};
// byte colPins[COLS] = {6,7,8};
// const byte EncoderClockPin = 1;
// const byte EncoderDataPin = 2;
// const byte EncoderSwitchPin = 3;
// const byte LEDPin = 5;

// NANO PINS
byte rowPins[ROWS] = {9, 10,11,12};
byte colPins[COLS] = {6,7,8};
const byte EncoderClockPin = 2;
const byte EncoderDataPin = 3;
const byte EncoderSwitchPin = 4;
const byte LEDPin = 5;
const byte statusPin=13;

Keypad kpd = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

int instruction = 0;
unsigned long successfulRequestTime = 0;
int fadePeriod=2000;

// unsigned long loopCount;
// unsigned long startTime;
char lastKeyPress;
long encPos=0;
bool keypadReleased = false;
bool rotSwitchReleased = false;
int rotSwitchState;
int prevSwitchState = HIGH;

unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 50;

volatile uint8_t EncodeCTR;
volatile int8_t EncodeDIR;
volatile uint8_t EncoderChange;
volatile uint8_t SwitchCtr;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  // loopCount=0;
  // startTime = millis();
  //pinMode(EncoderSwitchPin, INPUT);

  pinMode(EncoderSwitchPin , INPUT_PULLUP); // switch is not powered by the + on the Encoder breakout
  pinMode(EncoderClockPin , INPUT);
  pinMode(EncoderDataPin , INPUT);
  pinMode(LEDPin , OUTPUT);
  pinMode(statusPin, OUTPUT);
  //attachInterrupt(digitalPinToInterrupt(EncoderSwitchPin), Switch, FALLING);
  attachInterrupt(digitalPinToInterrupt(EncoderClockPin), Encode, FALLING);
}

void loop() {
 
  if (Serial.available() > 0) {
    instruction = Serial.read();
    // if (instruction==)
    Serial.print("I Got ");
    Serial.println(instruction);
    if (instruction==89) {
      successfulRequestTime=millis();
    } else {
      successfulRequestTime=0;
    }
  }

  if ((millis() - successfulRequestTime) < 1000) {
    digitalWrite(statusPin, HIGH);
  } else {
    digitalWrite(statusPin, LOW);
  }

  char keyPress = kpd.getKey();
  if (!keyPress) {
    keypadReleased = true;
  }
  if (keyPress && keypadReleased) {
    Serial.println(keyPress);
    lastKeyPress = keyPress;
  }

  if (EncoderChange) {
    EncoderChange = 0;
    if (EncodeDIR==1) {
      Serial.println("+");
    } else {
      Serial.println("-");
    }
  }

  int reading = digitalRead(EncoderSwitchPin);
  // Serial.println(reading);
  if (reading != prevSwitchState) {
    // Serial.println("Reset");
    lastDebounceTime=millis();
  }
  if ((millis() - lastDebounceTime) > debounceDelay) {
    // Serial.println("L");
    if (reading != rotSwitchState) { 
      rotSwitchState = reading;
    }
    if (rotSwitchState == LOW && SwitchCtr==0) { 
      SwitchCtr++;
      Serial.println("S");
    }
    if (rotSwitchState==HIGH) {
      SwitchCtr=0;
    }
  }
  prevSwitchState = reading;
  // if (SwitchCtr) {
  //   Serial.println("S");
  //   SwitchCtr = 0;
  // }
  analogWrite(LEDPin, 128+127*cos(2*PI/fadePeriod*millis()));

}



// void Switch() {
//   static unsigned long DebounceTimer;
//   if ((unsigned long)(millis() - DebounceTimer) >= (400)) {
//     DebounceTimer = millis();
//     if (!SwitchCtr) {
//       SwitchCtr++;
//     }
//   }
// } This worked on a leonardo, with multiple interrupts. For some reason, despite only requiring two interrupt pins, it doesn't want to work on a Nano


void Encode() { // we know the clock pin is low so we only need to see what state the Data pin is and count accordingly
  static unsigned long DebounceTimer;
  if ((unsigned long)(millis() - DebounceTimer) >= (100)) { // standard blink without delay timer
    DebounceTimer = millis();
    if (digitalRead(EncoderDataPin) == LOW) // switch to LOW to reverse direction of Encoder counting
    {
      EncodeCTR++;
      EncodeDIR=1;
    }
    else {
      EncodeCTR--;
      EncodeDIR=-1;
    }
    EncoderChange++;
  }
}