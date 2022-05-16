#include <Keypad.h>
#include <Encoder.h>

const byte ROWS = 4;
const byte COLS = 4;
char keys[ROWS][COLS] = {
  {'1','2','3','4'},
  {'5','6','7','8'},
  {'9','A','B','C'},
  {'D','E','F','0'}
};

byte rowPins[ROWS] = {13,12,14,27};
byte colPins[COLS] = {21,19,18,5};

Keypad kpd = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);
Encoder knob(22,23);
unsigned long loopCount;
unsigned long startTime;
long encPos=0;
String msg;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  loopCount=0;
  startTime = millis();
  msg = "";
  Serial.println("Hello, ESP32!");
}

void loop() {

  loopCount++;
  long newPos;

  if ( (millis() -startTime) > 5000) {
    Serial.print("Average loops per second = ");
    Serial.print( loopCount/5);
    startTime=millis();
    loopCount=0;
  }

  char keyPress = kpd.getKey();
  newPos = knob.read();

  if (keyPress) {
    Serial.println(keyPress);
  }

  if (newPos != encPos) {
    Serial.println("Position ");
    Serial.print(newPos);
    encPos=newPos;
  }

}
