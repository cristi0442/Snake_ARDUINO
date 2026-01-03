const int pinX = A0;
const int pinY = A1;

const int width = 20;  
const int height = 10; 
int speed = 300;      

// Variabile Șarpe
int snakeX[100]; // Coordonatele X ale corpului (maxim 100 lungime)
int snakeY[100]; // Coordonatele Y ale corpului
int snakeLen = 1; // Lungimea inițială

// Variabile Mâncare
int foodX, foodY;

// Direcție: 0=Stop, 1=Sus, 2=Jos, 3=Stânga, 4=Dreapta
int dir = 0; 
bool gameOver = false;
int score = 0;

// Joystick
int joyX, joyY;

void setup() {
  
  Serial.begin(115200); 
  
  pinMode(pinX, INPUT);
  pinMode(pinY, INPUT);
  
  // Inițializare Random (folosim zgomot de pe un pin analogic neconectat)
  randomSeed(analogRead(A5));
  
  resetGame();
}

void loop() {
  if (gameOver) {
    
    Serial.println("\n\n=== GAME OVER ===");
    Serial.print("Scor Final: ");
    Serial.println(score);

    Serial.print("SET_SCORE:");   
    Serial.println(score);       

    Serial.println("Misca joystick-ul pentru a restarta...");
    delay(1000);
    
    while (true) {
      if (abs(analogRead(pinX) - 512) > 200 || abs(analogRead(pinY) - 512) > 200) {
        resetGame();
        break;
      }
    }
  }

  readJoystick();
  logic();
  draw();
  delay(speed);
}

void resetGame() {
  snakeX[0] = width / 2;
  snakeY[0] = height / 2;
  snakeLen = 1;
  score = 0;
  dir = 0; 
  gameOver = false;
  spawnFood();
}

void spawnFood() {
  bool onSnake = true;
  while (onSnake) {
    onSnake = false;
    foodX = random(1, width - 1);
    foodY = random(1, height - 1);
    
    // Verificăm să nu apară mâncarea în șarpe
    for (int i = 0; i < snakeLen; i++) {
      if (snakeX[i] == foodX && snakeY[i] == foodY) {
        onSnake = true;
        break;
      }
    }
  }
}

void readJoystick() {
  joyX = analogRead(pinX);
  joyY = analogRead(pinY);
  
  // Praguri (Deadzone 200-800)
  
  if (joyX < 200 && dir != 4) dir = 3; // Stânga
  else if (joyX > 800 && dir != 3) dir = 4; // Dreapta
  
  if (joyY < 200 && dir != 2) dir = 1; // Sus
  else if (joyY > 800 && dir != 1) dir = 2; // Jos
}

void logic() {
  // Mutăm fiecare segment pe poziția celui din față, pornind de la coadă
  int prevX = snakeX[0];
  int prevY = snakeY[0];
  int prev2X, prev2Y;
  
  if (dir == 1) snakeY[0]--; // Sus
  else if (dir == 2) snakeY[0]++; // Jos
  else if (dir == 3) snakeX[0]--; // Stânga
  else if (dir == 4) snakeX[0]++; // Dreapta
  
  if (dir == 0) return;

  // Mutăm corpul
  for (int i = 1; i < snakeLen; i++) {
    prev2X = snakeX[i];
    prev2Y = snakeY[i];
    snakeX[i] = prevX;
    snakeY[i] = prevY;
    prevX = prev2X;
    prevY = prev2Y;
  }

  // Coliziune cu pereții
  if (snakeX[0] >= width || snakeX[0] < 0 || snakeY[0] >= height || snakeY[0] < 0) {
    gameOver = true;
  }

  // Coliziune cu coada
  for (int i = 1; i < snakeLen; i++) {
    if (snakeX[0] == snakeX[i] && snakeY[0] == snakeY[i]) {
      gameOver = true;
    }
  }

  // Mâncare
  if (snakeX[0] == foodX && snakeY[0] == foodY) {
    score += 10;
    snakeLen++;
    spawnFood();
  }
}

void draw() {
  
  Serial.print("DATA:");
  
  // 1. Mâncarea
  Serial.print(foodX); Serial.print(",");
  Serial.print(foodY); Serial.print(";");
  
  // 2. Lungimea Șarpelui
  Serial.print(snakeLen); Serial.print(";");
  
  // 3. Coordonatele Șarpelui (perechi X,Y)
  for(int i=0; i<snakeLen; i++) {
     Serial.print(snakeX[i]); Serial.print(",");
     Serial.print(snakeY[i]);
     
     if(i < snakeLen - 1) 
     Serial.print(",");
  }
  Serial.print(";");
  
  // 4. Scor și Status
  Serial.print(score); Serial.print(";");
  Serial.println(gameOver ? 1 : 0); // 1 = Game Over, 0 = Jocul merge
}