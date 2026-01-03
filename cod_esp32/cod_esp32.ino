#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>
#include <WebServer.h> 
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

// =========================================================
// CONFIGURARE WI-FI
// =========================================================
const char* ssid = "DIGI-t3P6";
const char* password = "38KhEV4K";

// =========================================================
// CONFIGURARE SUPABASE
// =========================================================
String supabase_url = "https://trxwaqqoveluhysicitc.supabase.co";
String supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRyeHdhcXFvdmVsdWh5c2ljaXRjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjczNzk3NzYsImV4cCI6MjA4Mjk1NTc3Nn0.B3pHaLhfaMxsOTmYnwrYNiEnUYzPtVM0lKj0lAv0b5g";

// Variabile Globale
int currentLevelID = 1; // Default Easy (ID 1 in baza de date)
WebServer server(80);   

// HTML-ul pentru telefon
const char* htmlPage = R"rawliteral(
<!DOCTYPE html><html>
<head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body { font-family: Arial; text-align: center; background-color: #1a1a1a; color: white; }
  h1 { color: #00ff00; margin-bottom: 5px; }
  .card { background: #333; padding: 20px; margin: 10px; border-radius: 10px; }
  select, button { padding: 10px; font-size: 18px; width: 100%; margin-top: 10px; border-radius: 5px; }
  .btn-apply { background-color: #008CBA; color: white; border: none; font-weight: bold; }
</style></head>
<body>
  <h1>SNAKE CONTROL</h1>
  
  <form action="/set" method="get">
    <div class="card">
      <h3>1. Dificultate (Viteza)</h3>
      <select name="level">
        <option value="1">Usoara (Slow)</option>
        <option value="2" selected>Medie (Normal)</option>
        <option value="3">Grea (Fast)</option>
      </select>
    </div>

    <div class="card">
      <h3>2. Marime Harta (Grid)</h3>
      <select name="grid">
        <option value="20,10" selected>Standard (20x10)</option>
        <option value="15,15">Patrat Mic (15x15)</option>
        <option value="30,15">Mare (30x15)</option>
        <option value="40,20">Gigant (40x20)</option>
      </select>
    </div>

    <button type="submit" class="btn-apply">APLICA SETARILE</button>
  </form>
  
  <p>Conectat la ESP32</p>
</body></html>
)rawliteral";

// Prototipuri functii (ca sa nu dea eroare compilatorul)
String getSupabaseScore(int id);
void updateSupabaseScore(String scoreVal, int id);

void setup() {
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);
  Serial.begin(115200);
  Serial.setTimeout(50);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
  
  // Pornim Serverul Web
  server.on("/", []() { server.send(200, "text/html", htmlPage); });
  
  // LOGICA BUTON APLICA (Aici era greseala ta)
  server.on("/set", []() {
    // Verificam daca am primit "level" si "grid" de la formular
    if (server.hasArg("level") && server.hasArg("grid")) {
      String lvl = server.arg("level");
      String gridVal = server.arg("grid"); // EX: "20,10"
      
      // Calculam viteza bazat pe nivel (Formularul nu trimite viteza, doar ID-ul)
      int spd = 150; // Default Mediu
      if (lvl == "1") spd = 300; // Easy
      if (lvl == "3") spd = 50;  // Hard
      
      currentLevelID = lvl.toInt();
      
      // Trimitem comanda catre Python -> Mega
      // Format: CONFIG:LEVEL=1;SPEED=300;GRID=20,10
      String cmd = "CONFIG:LEVEL=" + lvl + ";SPEED=" + String(spd) + ";GRID=" + gridVal;
      Serial.println(cmd);
      
      server.send(200, "text/html", "<h1>Setari Aplicate!</h1><a href='/'>Inapoi la Control</a>");
    } else {
      server.send(400, "text/plain", "Eroare: Lipsesc parametri!");
    }
  });

  server.begin();
  Serial.println("\nSERVER PORNIT!");
  Serial.print("IP PENTRU TELEFON: ");
  Serial.println(WiFi.localIP()); 
}

void loop() {
  server.handleClient(); // Asculta telefonul
  
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "GET_HIGHSCORE") {
      String hs = getSupabaseScore(currentLevelID); // Luam scorul DOAR pentru nivelul curent
      Serial.print("HIGHSCORE:");
      Serial.println(hs);
    }
    else if (command.startsWith("SET_SCORE:")) {
      String val = command.substring(10);
      updateSupabaseScore(val, currentLevelID); // Facem UPDATE la ID-ul curent
    }
  }
}

// --- UPDATE (PATCH) ---
void updateSupabaseScore(String scoreVal, int id) {
  if(WiFi.status() == WL_CONNECTED){
    WiFiClientSecure client;
    client.setInsecure();
    HTTPClient http;
    
    // URL-ul pentru UPDATE specific: /highscores?id=eq.X
    String path = "/rest/v1/highscores?id=eq." + String(id);
    
    http.begin(client, supabase_url + path);
    http.addHeader("apikey", supabase_key);
    http.addHeader("Authorization", "Bearer " + supabase_key);
    http.addHeader("Content-Type", "application/json");
    
    String jsonPayload = "{\"score\": " + scoreVal + "}";
    
    // Folosim PATCH pentru a modifica rândul existent
    int httpCode = http.PATCH(jsonPayload); 
    
    if (httpCode > 0) Serial.println("HTTP Code: " + String(httpCode));
    else Serial.println("Eroare: " + http.errorToString(httpCode));
    
    http.end();
  }
}

// --- GET (SELECT) ---
String getSupabaseScore(int id) {
  if(WiFi.status() == WL_CONNECTED){
    WiFiClientSecure client;
    client.setInsecure();
    HTTPClient http;
    
    // Citim doar randul cu ID-ul curent
    String path = "/rest/v1/highscores?id=eq." + String(id) + "&select=score";
    
    http.begin(client, supabase_url + path);
    http.addHeader("apikey", supabase_key);
    http.addHeader("Authorization", "Bearer " + supabase_key);
    
    int httpCode = http.GET();
    if (httpCode > 0) {
      String payload = http.getString();
      int start = payload.indexOf("score\":");
      if (start > 0) {
        int end = payload.indexOf("}", start);
        return payload.substring(start + 7, end);
      }
    }
    http.end();
  }
  return "0";
}