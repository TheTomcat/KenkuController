#include <Keypad.h>
//#include <Encoder.h>

const byte ROWS = 4;
const byte COLS = 3;
char keys[ROWS][COLS] = {
  {'1','2','3'},
  {'4','5','6'},
  {'7','8','9'},
  {'*','0','#'}
};

byte rowPins[ROWS] = {9, 10,11,12};
byte colPins[COLS] = {6,7,8};
Keypad kpd = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

const byte EncoderClockPin = 1;
const byte EncoderDataPin = 2;
const byte EncoderSwitchPin = 3;
//Encoder knob(EncoderClockPin,EncoderDataPin);
const byte LEDPin = 5;
int instruction = 0;

unsigned long loopCount;
unsigned long startTime;
char lastKeyPress;
long encPos=0;
String msg;
bool released = false;

volatile uint8_t EncodeCTR;
volatile int8_t EncodeDIR;
volatile uint8_t EncoderChange;
volatile uint8_t SwitchCtr;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  loopCount=0;
  startTime = millis();
  msg = "";
  Serial.println("Hello, Leo!");
  //pinMode(EncoderSwitchPin, INPUT);

  pinMode(EncoderSwitchPin , INPUT_PULLUP); // switch is not powered by the + on the Encoder breakout
  pinMode(EncoderClockPin , INPUT);
  pinMode(EncoderDataPin , INPUT);
  pinMode(LEDPin , OUTPUT);
  attachInterrupt(digitalPinToInterrupt(EncoderSwitchPin), Switch, FALLING);
  attachInterrupt(digitalPinToInterrupt(EncoderClockPin), Encode, FALLING);

}

void loop() {
 
  // if ( (millis() -startTime) > 5000) {
  //   Serial.print("Average loops per second = ");
  //   Serial.print( loopCount/5);
  //   startTime=millis();
  //   loopCount=0;
  // }

  if (Serial.available() > 0) {
    instruction = Serial.read();
    Serial.print("I Got ");
    Serial.println(instruction);
  }

  char keyPress = kpd.getKey();
  if (!keyPress) {
    released = true;
  }
  if (keyPress && released) {
    Serial.println(keyPress);
    lastKeyPress = keyPress;
  }// } else if (!keyPress) {
  //   Serial.println("release");
  // }

  // if (EncoderChange || SwitchCtr) {
  //   EncoderChange = 0;
  //   Serial.print("EncodeCTR: ");
  //   Serial.print(EncodeCTR);
  //   Serial.print(" - ");
  //   Serial.print(EncodeDIR);
  //   Serial.println();
  //   Serial.print("Switch Pressed ");
  //   Serial.println(SwitchCtr);
  //   SwitchCtr = 0;
  // }

  if (EncoderChange) {
    EncoderChange = 0;
    if (EncodeDIR==1) {
      Serial.println("+");
      digitalWrite(LEDPin, HIGH);
    } else {
      Serial.println("-");
      digitalWrite(LEDPin, LOW);
    }
  }

  if (SwitchCtr) {
    Serial.println("S");
    SwitchCtr = 0;
  }

  // newPos = knob.read();
  // if (newPos != encPos) {
  //   Serial.print("Position ");
  //   Serial.println(newPos);
  //   encPos=newPos;
  // }

}

void Switch() {
  static unsigned long DebounceTimer;
  if ((unsigned long)(millis() - DebounceTimer) >= (400)) {
    DebounceTimer = millis();
    if (!SwitchCtr) {
      SwitchCtr++;
    }
  }
}
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