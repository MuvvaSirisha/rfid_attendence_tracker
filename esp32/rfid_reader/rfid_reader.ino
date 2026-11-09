/*
 * SmartAttend — ESP32 RFID Reader with Wi-Fi
 * Stage 4: Scans card → sends UID to Flask API over Wi-Fi →
 *          gets result back → flashes LED + beeps buzzer.
 *
 * ── BEFORE UPLOADING ────────────────────────────────────────────────────────
 * 1. Set your Wi-Fi SSID and password below.
 * 2. Run  python api/flask_api.py  on your PC — it will print your PC's IP.
 * 3. Set SERVER_IP to that IP address (e.g. "192.168.1.10").
 * 4. Upload this sketch.
 *
 * ── WIRING (same as Stage 3) ────────────────────────────────────────────────
 *   RC522 SDA  → GPIO 5     RC522 MISO → GPIO 19
 *   RC522 SCK  → GPIO 18    RC522 RST  → GPIO 22
 *   RC522 MOSI → GPIO 23    RC522 3.3V → 3.3V   RC522 GND → GND
 *   Green LED  → GPIO 4 (220Ω to GND)
 *   Red LED    → GPIO 16 (220Ω to GND)
 *   Buzzer     → GPIO 2 (active buzzer, − to GND)
 * ────────────────────────────────────────────────────────────────────────────
 */

#include <SPI.h>
#include <MFRC522.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ── ⚙️  CONFIGURE THESE THREE LINES ─────────────────────────────────────────
const char* WIFI_SSID  = "YOUR_WIFI_NAME";       // Your Wi-Fi name
const char* WIFI_PASS  = "YOUR_WIFI_PASSWORD";   // Your Wi-Fi password
const char* SERVER_IP  = "192.168.1.10";         // PC IP shown by flask_api.py
// ─────────────────────────────────────────────────────────────────────────────

String API_URL = String("http://") + SERVER_IP + ":5000/api/scan";

// Pin definitions
#define SS_PIN    5
#define RST_PIN   22
#define GREEN_LED 4
#define RED_LED   16
#define BUZZER    2

MFRC522 rfid(SS_PIN, RST_PIN);

// ── Setup ────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);

  pinMode(GREEN_LED, OUTPUT);
  pinMode(RED_LED,   OUTPUT);
  pinMode(BUZZER,    OUTPUT);

  // Connect to Wi-Fi
  Serial.print("Connecting to Wi-Fi");
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  int tries = 0;
  while (WiFi.status() != WL_CONNECTED && tries < 20) {
    delay(500);
    Serial.print(".");
    tries++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWi-Fi connected!");
    Serial.print("ESP32 IP: ");
    Serial.println(WiFi.localIP());
    // Two green flashes = ready
    flashLED(GREEN_LED, 2);
  } else {
    Serial.println("\nWi-Fi FAILED — check SSID/password");
    // Three red flashes = error
    flashLED(RED_LED, 3);
  }

  SPI.begin();
  rfid.PCD_Init();

  Serial.println("================================");
  Serial.println("  SmartAttend — Stage 4 Ready  ");
  Serial.println("  Scan an RFID card...         ");
  Serial.println("================================");
}

// ── Main loop ────────────────────────────────────────────────────────────────
void loop() {
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) return;

  String uid = getUID();
  Serial.print("Card UID: "); Serial.println(uid);

  if (WiFi.status() == WL_CONNECTED) {
    sendToServer(uid);
  } else {
    Serial.println("No Wi-Fi — cannot send scan");
    flashLED(RED_LED, 2);
  }

  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
  delay(2000); // prevent duplicate reads
}

// ── Send UID to Flask API ────────────────────────────────────────────────────
void sendToServer(String uid) {
  HTTPClient http;
  http.begin(API_URL);
  http.addHeader("Content-Type", "application/json");

  // Build JSON: {"uid": "04:A3:F1:7C:05"}
  String body = "{\"uid\":\"" + uid + "\"}";
  int code = http.POST(body);

  if (code == 200) {
    String response = http.getString();
    Serial.println("Server response: " + response);

    // Parse JSON response
    StaticJsonDocument<256> doc;
    deserializeJson(doc, response);
    String status = doc["status"];

    if (status == "ok") {
      String name = doc["student"];
      Serial.println("Marked Present: " + name);
      // Green flash + 2 short beeps = known student
      flashLED(GREEN_LED, 2);
      beep(80); delay(100); beep(80);
    } else {
      Serial.println("Unknown card!");
      // Red flash + long beep = unknown card
      flashLED(RED_LED, 1);
      beep(500);
    }
  } else {
    Serial.print("HTTP error: "); Serial.println(code);
    flashLED(RED_LED, 3);
  }

  http.end();
}

// ── Helpers ──────────────────────────────────────────────────────────────────

String getUID() {
  String uid = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (i > 0) uid += ":";
    if (rfid.uid.uidByte[i] < 0x10) uid += "0";
    uid += String(rfid.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();
  return uid;
}

void flashLED(int pin, int times) {
  for (int i = 0; i < times; i++) {
    digitalWrite(pin, HIGH); delay(200);
    digitalWrite(pin, LOW);  delay(150);
  }
}

void beep(int ms) {
  digitalWrite(BUZZER, HIGH); delay(ms);
  digitalWrite(BUZZER, LOW);
}
