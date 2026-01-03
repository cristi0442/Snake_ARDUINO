#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

// =========================================================
// CONFIGURARE WI-FI (Trebuie să completezi aici!)
// =========================================================
const char* ssid = "DIGI-t3P6";       // Pune numele rețelei tale
const char* password = "38KhEV4K"; // Pune parola rețelei tale

// =========================================================
// CONFIGURARE SUPABASE (Gata completat cu datele tale)
// =========================================================
String supabase_url = "https://trxwaqqoveluhysicitc.supabase.co";
String supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRyeHdhcXFvdmVsdWh5c2ljaXRjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjczNzk3NzYsImV4cCI6MjA4Mjk1NTc3Nn0.B3pHaLhfaMxsOTmYnwrYNiEnUYzPtVM0lKj0lAv0b5g";

// Căile pentru citire și scriere în tabelul 'highscores'
// Citim scorul cel mai mare (ordonat descrescător, limitat la 1)
String readPath = "/rest/v1/highscores?select=score&order=score.desc&limit=1";
String writePath = "/rest/v1/highscores";

void setup() {
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0); 
  
  Serial.begin(115200); 

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
}

void loop() {
  // Ascultăm comenzi de la Arduino Mega
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "GET_HIGHSCORE") {
      String hs = getSupabaseScore();
      // Raspundem catre PC (si PC-ul va trimite la Mega)
      Serial.println(hs); 
    }
    else if (command.startsWith("SET_SCORE:")) {
      String val = command.substring(10); 
      sendSupabaseScore(val);
    }
  }
  delay(10);
}

// --- FUNCȚIE PENTRU CITIRE SCOR (GET) ---
String getSupabaseScore() {
  if(WiFi.status() == WL_CONNECTED){
    WiFiClientSecure client;
    client.setInsecure(); // Ignoră verificarea certificatului SSL (esențial)
    HTTPClient http;
    
    // Construim linkul complet
    http.begin(client, supabase_url + readPath);
    
    // Adăugăm cheile de securitate
    http.addHeader("apikey", supabase_key);
    http.addHeader("Authorization", "Bearer " + supabase_key);
    
    int httpCode = http.GET();
    
    if (httpCode > 0) {
      String payload = http.getString();
      // Supabase returnează un JSON de genul: [{"score": 150}]
      // Extragem doar numărul simplu
      int start = payload.indexOf("score\":");
      if (start > 0) {
        int end = payload.indexOf("}", start);
        String scoreStr = payload.substring(start + 7, end);
        return scoreStr;
      }
      return "0"; // Dacă tabelul e gol sau nu găsim numărul
    }
    http.end();
  }
  return "0"; // Eroare conexiune
}

// --- FUNCȚIE PENTRU SALVARE SCOR (POST) ---
void sendSupabaseScore(String scoreVal) {
  if(WiFi.status() == WL_CONNECTED){
    WiFiClientSecure client;
    client.setInsecure();
    HTTPClient http;
    
    http.begin(client, supabase_url + writePath);
    
    // Headers obligatorii
    http.addHeader("apikey", supabase_key);
    http.addHeader("Authorization", "Bearer " + supabase_key);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("Prefer", "return=minimal"); // Să nu primim răspuns lung
    
    // Creăm pachetul JSON: {"score": 100}
    String jsonPayload = "{\"score\": " + scoreVal + "}";
    
    http.POST(jsonPayload);
    http.end();
  }
}