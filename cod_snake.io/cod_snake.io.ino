// Pini
const int pinX = A0;
const int pinY = A1;
const int pinBtn = 2;

// Variabile pentru calibrare
int valX = 0;
int valY = 0;

// Pragurile pentru a detecta mișcarea (0-1023)
// Centrul este aprox 512. Considerăm mișcare dacă e sub 300 sau peste 700.
// Vom folosi analogRead, pentru a putea interpreta corect valorile primite de la joystick
const int thresholdLow = 300;
const int thresholdHigh = 700;

// debounce simplu, precum am făcut și la laborator
unsigned long lastSendTime = 0;
const int delayTime = 100; 

void setup() {
  Serial.begin(9600); 
  pinMode(pinX, INPUT);
  pinMode(pinY, INPUT);
  pinMode(pinBtn, INPUT_PULLUP); 
}

void loop() {
  valX = analogRead(pinX);
  valY = analogRead(pinY);
  
  // Verificăm timpul pentru a nu inunda PC-ul cu date
  if (millis() - lastSendTime > delayTime) {
    
    if (valX < thresholdLow) {
      Serial.println("L"); // Left
      lastSendTime = millis();
    } 
    else if (valX > thresholdHigh) {
      Serial.println("R"); // Right
      lastSendTime = millis();
    }
    
    if (valY < thresholdLow) {
      Serial.println("U"); // Up
      lastSendTime = millis();
    } 
    else if (valY > thresholdHigh) {
      Serial.println("D"); // Down
      lastSendTime = millis();
    }
  }
  
  if (digitalRead(pinBtn) == LOW) {
     Serial.println("S"); // Start/Reset
     delay(500); // Debounce
  }
}