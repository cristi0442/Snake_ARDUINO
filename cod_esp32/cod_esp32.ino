#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>
#include <WebServer.h> 
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

// === DATELE TALE ===
const char* ssid = "DIGI-t3P6";
const char* password = "38KhEV4K";

String supabase_url = "https://trxwaqqoveluhysicitc.supabase.co";
String supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRyeHdhcXFvdmVsdWh5c2ljaXRjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjczNzk3NzYsImV4cCI6MjA4Mjk1NTc3Nn0.B3pHaLhfaMxsOTmYnwrYNiEnUYzPtVM0lKj0lAv0b5g";

int currentLevelID = 2; 
int liveScore = 0;      
int liveBest = 0;   
int liveSpeed = 300;    

WebServer server(80);   

// HTML + CSS + JS (Dashboard Profi)
const char* htmlPage = R"rawliteral(
<!DOCTYPE html><html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { font-family: 'Segoe UI', sans-serif; text-align: center; background-color: #121212; color: white; margin: 0; padding: 10px; }
    h1 { color: #00e676; letter-spacing: 2px; margin-bottom: 20px;}
    .card { background: #1e1e1e; padding: 15px; margin-bottom: 15px; border-radius: 12px; border-left: 4px solid #00e676; text-align: left; }
    h3 { margin: 0 0 10px 0; font-size: 14px; color: #aaa; text-transform: uppercase; }
    select { padding: 12px; width: 100%; border-radius: 8px; background: #333; color: white; border: none; font-size: 16px; }
    
    .btn-apply { background: linear-gradient(45deg, #00e676, #008CBA); color: #000; border: none; padding: 15px; width: 100%; border-radius: 30px; font-size: 18px; font-weight: bold; cursor: pointer; margin-top: 10px; box-shadow: 0 4px 15px rgba(0, 230, 118, 0.3); }
    .btn-apply:active { transform: scale(0.98); }

    /* Dashboard */
    .score-box { display: flex; justify-content: space-between; margin-bottom: 20px; }
    .score-item { background: #2a2a2a; padding: 15px; border-radius: 10px; width: 30%; text-align: center; }
    .score-val { font-size: 24px; font-weight: bold; color: #ffeb3b; }
    .score-lbl { font-size: 10px; color: #888; letter-spacing: 1px; }

    /* Switch */
    .toggle-row { display: flex; justify-content: space-between; align-items: center; margin-top: 10px; }
    .switch { position: relative; display: inline-block; width: 50px; height: 26px; }
    .switch input { opacity: 0; width: 0; height: 0; }
    .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #555; transition: .4s; border-radius: 34px; }
    .slider:before { position: absolute; content: ""; height: 18px; width: 18px; left: 4px; bottom: 4px; background-color: white; transition: .4s; border-radius: 50%; }
    input:checked + .slider { background-color: #f44336; }
    input:checked + .slider:before { transform: translateX(24px); }
  </style>
</head>
<body>

  <h1>SNAKE PRO</h1>

  <div class="score-box">
    <div class="score-item">
      <div class="score-val" id="liveScore">0</div>
      <div class="score-lbl">SCOR</div>
    </div>
    <div class="score-item">
      <div class="score-val" id="liveSpeed" style="color:#00e676">300</div>
      <div class="score-lbl">MS/MOVE</div>
    </div>
    <div class="score-item">
      <div class="score-val" id="liveBest">--</div>
      <div class="score-lbl">RECORD</div>
    </div>
  </div>

  <div class="card">
    <h3>Setari Joc</h3>
    <select id="level">
      <option value="1">Usoara (Slow)</option>
      <option value="2" selected>Medie (Normal)</option>
      <option value="3">Grea (Fast)</option>
    </select>
    <div style="height:10px"></div>
    <select id="grid">
      <option value="20,10" selected>Standard (20x10)</option>
      <option value="15,15">Patrat (15x15)</option>
      <option value="30,15">Mare (30x15)</option>
      <option value="40,20">Gigant (40x20)</option>
    </select>
  </div>

  <div class="card" style="border-left-color: #ffeb3b">
    <h3>Grafica & Reguli</h3>
    <select id="color">
      <option value="GREEN" selected>Clasic (Verde)</option>
      <option value="CYAN">Cyberpunk (Cyan)</option>
      <option value="MAGENTA">Neon (Mov)</option>
      <option value="YELLOW">Toxic (Galben)</option>
    </select>
    
    <div class="toggle-row">
      <span>Pereti Mortali?</span>
      <label class="switch">
        <input type="checkbox" id="walls">
        <span class="slider"></span>
      </label>
    </div>
  </div>

  <button class="btn-apply" onclick="sendData()">APLICA TOT</button>
  <p id="status" style="color:#555; font-size:12px">Conectat la ESP32</p>

  <script>
    function sendData() {
      var lvl = document.getElementById("level").value;
      var grd = document.getElementById("grid").value;
      var col = document.getElementById("color").value;
      var wal = document.getElementById("walls").checked ? "1" : "0";
      
      document.getElementById("status").style.color = "yellow";
      document.getElementById("status").innerText = "Trimitere...";

      fetch('/set?level='+lvl+'&grid='+grd+'&color='+col+'&walls='+wal)
        .then(r => r.text())
        .then(d => {
          document.getElementById("status").style.color = "#00ff00";
          document.getElementById("status").innerText = "✅ " + d;
        });
    }

    setInterval(function() {
      fetch('/data').then(r => r.json()).then(d => {
          document.getElementById("liveScore").innerText = d.live;
          document.getElementById("liveBest").innerText = d.best;
          document.getElementById("liveSpeed").innerText = d.spd;
      });
    }, 1000);
  </script>
</body></html>
)rawliteral";

String getSupabaseScore(int id);
void updateSupabaseScore(String scoreVal, int id);

void setup() {
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);
  Serial.begin(115200);
  Serial.setTimeout(50);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) delay(500);

  server.on("/", []() { server.send(200, "text/html", htmlPage); });

  server.on("/data", []() {
    String json = "{\"live\":" + String(liveScore) + ",\"best\":" + String(liveBest) + ",\"spd\":" + String(liveSpeed) + "}";
    server.send(200, "application/json", json);
  });
  
  server.on("/set", []() {
    if (server.hasArg("level")) {
      String lvl = server.arg("level");
      String grd = server.arg("grid");
      String col = server.arg("color");
      String wal = server.arg("walls");
      
      int spd = 150;
      if (lvl == "1") spd = 300;
      if (lvl == "3") spd = 50;
      currentLevelID = lvl.toInt();
      
      String cmd = "CONFIG:LEVEL=" + lvl + ";SPEED=" + String(spd) + ";GRID=" + grd + ";COLOR=" + col + ";WALLS=" + wal;
      Serial.println(cmd);
      
      server.send(200, "text/plain", "Setari Actualizate!");
    }
  });

  server.begin();
  Serial.println("\nSERVER PORNIT!");
  Serial.print("IP PENTRU TELEFON: ");
  Serial.println(WiFi.localIP()); 

  String s = getSupabaseScore(currentLevelID);
  liveBest = s.toInt();
  Serial.println("HIGHSCORE:" + s);
}

void loop() {
  server.handleClient();
  
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "GET_HIGHSCORE") {
      String hs = getSupabaseScore(currentLevelID);
      liveBest = hs.toInt();
      Serial.print("HIGHSCORE:");
      Serial.println(hs);
    }
    else if (command.startsWith("LIVE:")) {
       liveScore = command.substring(5).toInt();
    }
    else if (command.startsWith("LIVE_SPEED:")) {
       liveSpeed = command.substring(11).toInt();
    }
    else if (command.startsWith("SET_SCORE:")) {
      String val = command.substring(10);
      updateSupabaseScore(val, currentLevelID);
      liveBest = val.toInt();
    }
  }
}

// --- SUPABASE FUNCTIONS ---
void updateSupabaseScore(String scoreVal, int id) {
  if(WiFi.status() == WL_CONNECTED){
    WiFiClientSecure client; client.setInsecure(); HTTPClient http;
    http.begin(client, supabase_url + "/rest/v1/highscores?id=eq." + String(id));
    http.addHeader("apikey", supabase_key);
    http.addHeader("Authorization", "Bearer " + supabase_key);
    http.addHeader("Content-Type", "application/json");
    http.PATCH("{\"score\": " + scoreVal + "}");
    http.end();
  }
}

String getSupabaseScore(int id) {
  if(WiFi.status() == WL_CONNECTED){
    WiFiClientSecure client; client.setInsecure(); HTTPClient http;
    http.begin(client, supabase_url + "/rest/v1/highscores?id=eq." + String(id) + "&select=score");
    http.addHeader("apikey", supabase_key);
    http.addHeader("Authorization", "Bearer " + supabase_key);
    int code = http.GET();
    if (code > 0) {
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