/*
 * SmartAttend — ESP32 RC522 RFID Reader (USB Serial Mode)
 * ========================================================
 * Sends card scans directly over USB Serial to the Streamlit Dashboard.
 * No Wi-Fi required!
 *
 * ── WIRING ──────────────────────────────────────────────────────────────────
 *   RC522 SDA (SS) → GPIO 5
 *   RC522 SCK      → GPIO 18
 *   RC522 MOSI     → GPIO 23
 *   RC522 MISO     → GPIO 19
 *   RC522 RST      → GPIO 22
 *   RC522 3.3V     → 3.3V (Do NOT use 5V!)
 *   RC522 GND      → GND
 *
 *   Optional Feedback:
 *   Green LED      → GPIO 4 (via 220Ω resistor to GND)
 *   Red LED        → GPIO 16 (via 220Ω resistor to GND)
 *   Buzzer         → GPIO 2 (active buzzer, (-) to GND)
 * ────────────────────────────────────────────────────────────────────────────
 */

#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN    5
#define RST_PIN   22
#define GREEN_LED 4
#define RED_LED   16
#define BUZZER    2

MFRC522 rfid(SS_PIN, RST_PIN);

void setup() {
  Serial.begin(115200);
  while (!Serial); // Wait for serial port ready

  pinMode(GREEN_LED, OUTPUT);
  pinMode(RED_LED,   OUTPUT);
  pinMode(BUZZER,    OUTPUT);

  digitalWrite(GREEN_LED, LOW);
  digitalWrite(RED_LED, LOW);
  digitalWrite(BUZZER, LOW);

  SPI.begin();
  rfid.PCD_Init();

  // Startup indication: 2 short beeps
  digitalWrite(BUZZER, HIGH); delay(80); digitalWrite(BUZZER, LOW);
  delay(100);
  digitalWrite(BUZZER, HIGH); delay(80); digitalWrite(BUZZER, LOW);

  Serial.println("\n--- SmartAttend Serial RFID Ready ---");
  Serial.println("Scan an RFID tag or card...");
}

void loop() {
  // Look for new RFID card
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) {
    return;
  }

  // Format UID as XX:XX:XX:XX
  String uid = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (i > 0) uid += ":";
    if (rfid.uid.uidByte[i] < 0x10) uid += "0";
    uid += String(rfid.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();

  // Print exact prefix expected by Python serial processor
  Serial.println("UID:" + uid);

  // Beep & flash green on scan
  digitalWrite(GREEN_LED, HIGH);
  digitalWrite(BUZZER, HIGH);
  delay(120);
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(BUZZER, LOW);

  // Halt card & stop crypto
  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();

  // Delay to prevent duplicate immediate triggers
  delay(1500);
}
