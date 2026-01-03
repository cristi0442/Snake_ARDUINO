#include <Arduino.h>

const int pinX = A0;
const int pinY = A1;
const int pinSW = 2; // Buton Joystick

// --- CONFIGURARE INITIALA ---
int width = 20;  
int height = 10;
int speed = 300;      

// Variabile Timp si Logica
unsigned long lastSpeedIncreaseTime = 0; 
int accelerationInterval = 15000; // 15 secunde default       
bool wallsActive = false; 
bool isPaused = false;     
bool lastSwState = HIGH;   

int snakeX[400]; 
int snakeY[400];
int snakeLen = 1;

int foodX, foodY;
int dir = 0; 
bool gameOver = false;
int score = 0;
int joyX, joyY;

void setup() {
  Serial.begin(115200); 
  pinMode(pinX, INPUT);
  pinMode(pinY, INPUT);
  pinMode(pinSW, INPUT_PULLUP); // Activam rezistenta interna
  
  randomSeed(analogRead(A5));
  updateIntervalBasedOnSpeed(); 
  resetGame();
}

void loop() {
  checkSettings();
  readButton(); 

  if (gameOver) {
    handleGameOver();
    return;
  }

  if (!isPaused) {
    handleSpeedIncrease(); 
    readJoystick();
    logic();
  }
  
  draw(); // Desenam continuu (chiar si in pauza)
  delay(speed);
}

// --- FUNCTII ---

void readButton() {
  int swState = digitalRead(pinSW);
  if (lastSwState == HIGH && swState == LOW) {
    isPaused = !isPaused; 
  }
  lastSwState = swState;
}

void handleSpeedIncrease() {
  if (dir != 0) { 
    if (millis() - lastSpeedIncreaseTime > accelerationInterval) {
      lastSpeedIncreaseTime = millis();
      if (speed > 30) {
        speed -= 10;
        Serial.println("EVENT:SPEED_UP"); // Trimitem notificare la Python
      }
    }
  }
}

void updateIntervalBasedOnSpeed() {
  if (speed >= 300) accelerationInterval = 15000; // Easy
  else if (speed >= 150) accelerationInterval = 20000; // Medium
  else accelerationInterval = 40000; // Hard
}

void checkSettings() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    
    if (cmd.startsWith("SET_SPEED:")) {
      speed = cmd.substring(10).toInt();
      updateIntervalBasedOnSpeed(); 
      lastSpeedIncreaseTime = millis(); 
    }
    else if (cmd.startsWith("SET_GRID:")) {
      String params = cmd.substring(9);
      int comma = params.indexOf(',');
      if (comma > 0) {
        width = params.substring(0, comma).toInt();
        height = params.substring(comma + 1).toInt();
        resetGame();
      }
    }
    else if (cmd.startsWith("SET_WALLS:")) {
      wallsActive = (cmd.substring(10).toInt() == 1);
    }
  }
}

void resetGame() {
  snakeX[0] = width / 2;
  snakeY[0] = height / 2;
  snakeLen = 1;
  score = 0;
  dir = 0; 
  gameOver = false;
  isPaused = false;
  spawnFood();
  lastSpeedIncreaseTime = millis();
}

void spawnFood() {
  bool onSnake = true;
  while (onSnake) {
    onSnake = false;
    foodX = random(0, width);
    foodY = random(0, height);
    for (int i = 0; i < snakeLen; i++) {
      if (snakeX[i] == foodX && snakeY[i] == foodY) {
        onSnake = true; break;
      }
    }
  }
}

void readJoystick() {
  joyX = analogRead(pinX);
  joyY = analogRead(pinY);
  if (joyX < 200 && dir != 4) dir = 3;
  else if (joyX > 800 && dir != 3) dir = 4;
  if (joyY < 200 && dir != 2) dir = 1;
  else if (joyY > 800 && dir != 1) dir = 2;
}

void logic() {
  int prevX = snakeX[0];
  int prevY = snakeY[0];
  int prev2X, prev2Y;
  
  if (dir == 1) snakeY[0]--;
  else if (dir == 2) snakeY[0]++;
  else if (dir == 3) snakeX[0]--;
  else if (dir == 4) snakeX[0]++;
  
  if (dir == 0) return;

  for (int i = 1; i < snakeLen; i++) {
    prev2X = snakeX[i];
    prev2Y = snakeY[i];
    snakeX[i] = prevX;
    snakeY[i] = prevY;
    prevX = prev2X;
    prevY = prev2Y;
  }

  // LOGICA COLIZIUNE
  if (wallsActive) {
    if (snakeX[0] >= width || snakeX[0] < 0 || snakeY[0] >= height || snakeY[0] < 0) gameOver = true;
  } else {
    // Teleportare
    if (snakeX[0] >= width) snakeX[0] = 0; else if (snakeX[0] < 0) snakeX[0] = width - 1;
    if (snakeY[0] >= height) snakeY[0] = 0; else if (snakeY[0] < 0) snakeY[0] = height - 1;
  }

  for (int i = 1; i < snakeLen; i++) {
    if (snakeX[0] == snakeX[i] && snakeY[0] == snakeY[i]) gameOver = true;
  }

  if (snakeX[0] == foodX && snakeY[0] == foodY) {
    score += 10;
    snakeLen++;
    spawnFood();
  }
}

void handleGameOver() {
  Serial.println("GAME OVER");
  Serial.print("SET_SCORE:"); Serial.println(score);
  delay(1000);
  while (true) {
    if (abs(analogRead(pinX) - 512) > 200 || abs(analogRead(pinY) - 512) > 200 || digitalRead(pinSW) == LOW) {
      resetGame(); break;
    }
    checkSettings(); 
  }
}

void draw() {
  Serial.print("DATA:");
  Serial.print(foodX); Serial.print(",");
  Serial.print(foodY); Serial.print(";");
  Serial.print(snakeLen); Serial.print(";");
  for(int i=0; i<snakeLen; i++) {
     Serial.print(snakeX[i]); Serial.print(",");
     Serial.print(snakeY[i]);
     if(i < snakeLen - 1) Serial.print(",");
  }
  Serial.print(";");
  Serial.print(score); Serial.print(";");
  Serial.print(gameOver ? 1 : 0); Serial.print(";");
  // Date suplimentare: Viteza si Pauza
  Serial.print(speed); Serial.print(";");
  Serial.println(isPaused ? 1 : 0);
}