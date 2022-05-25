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

const long pingIntervalNormal = 30000;
const long pingIntervalError = 5000;
const long pingTimeout = 300;
long lastPing = -pingIntervalNormal;

Keypad kpd = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

int instruction = 0;
unsigned long successfulRequestTime = 0;
int fadePeriod=2000;

enum deviceStatus {
  CONNECTED,
  PENDING,
  ERROR
};

enum messages {
  PING = 0,
  PONG = 1,
  ACK = 2,
  STATUS = 3
};

enum deviceStatus devStatus = PENDING;

char lastKeyPress;
bool awaitingPing;
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
  Serial.begin(9600);
  pinMode(EncoderSwitchPin , INPUT_PULLUP); 
  pinMode(EncoderClockPin , INPUT);
  pinMode(EncoderDataPin , INPUT);
  pinMode(LEDPin , OUTPUT);
  pinMode(statusPin, OUTPUT);
  attachInterrupt(digitalPinToInterrupt(EncoderClockPin), Encode, FALLING);
}

void loop() {

  if ((millis() - lastPing) > pingIntervalNormal) { 
    // If it's time to send a ping, then send a ping. 
    awaitingPing = true;
    Serial.println("p");
    lastPing = millis();
  }
  
  if (((millis() - lastPing) > pingTimeout) && awaitingPing) { 
    // Our ping timed out
    devStatus = ERROR;
    awaitingPing = false;
  }

  if (((millis() - lastPing) > pingIntervalError) && devStatus == ERROR) { 
    // If we've been waiting in error mode longer than pingIntervalError, send another ping
    Serial.print("p");
    awaitingPing = true;
    lastPing = millis();
  }

  if (Serial.available() > 0) {
    instruction = Serial.read();

    if (instruction==97 && awaitingPing) { 
      // We have received an ack ping, and we were waiting for one
      devStatus = CONNECTED;
      lastPing = millis();
      awaitingPing = false;
    }
    if (instruction==89) {
      successfulRequestTime=millis();
    } 
    if (instruction==63) {
      Serial.print("> CON_STAT ");
      Serial.println(devStatus);
      Serial.print("> Alive");
      Serial.print("> [ts]:");
      Serial.println(millis()/1000);
    }
  }

  if ((millis() - successfulRequestTime) < 1000) {
    // If an acknowledgement is received from the controller, light the LED for 1 sec
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
    if (reading != prevSwitchState) {
      lastDebounceTime=millis();
  }
  if ((millis() - lastDebounceTime) > debounceDelay) {
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

  switch (devStatus) {
    case CONNECTED:
      analogWrite(LEDPin, 128+127*cos(2*PI/fadePeriod*millis()));
      break;
    case PENDING:
      analogWrite(LEDPin, 128+127*cos(2*PI/(fadePeriod/5)*millis()));
      break;
    case ERROR:
      digitalWrite(LEDPin, int(millis()/200) % 2);
      break;
  }
}

void Encode() { 
  // we know the clock pin is low so we only need to see what state the Data pin is and count accordingly
  static unsigned long DebounceTimer;
  if ((unsigned long)(millis() - DebounceTimer) >= (100)) { // standard blink without delay timer
    DebounceTimer = millis();
    if (digitalRead(EncoderDataPin) == LOW) 
    // switch to LOW to reverse direction of Encoder counting
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