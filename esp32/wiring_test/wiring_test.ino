/*
 * SmartAttend — ESP32 Serial Test
 * Stage 3: Upload this FIRST to verify your RC522 wiring is correct
 *          before uploading the full rfid_reader.ino sketch.
 *
 * Expected Serial output when working:
 *   MFRC522 firmware version: 0x92 = v2.0
 *   Scan a card...
 *   Card UID: 04:A3:F1:7C
 *
 * If you see "WARNING: Communication failure" — check your wiring.
 */

#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN  5
#define RST_PIN 22

MFRC522 rfid(SS_PIN, RST_PIN);

void setup() {
  Serial.begin(115200);
  SPI.begin();
  rfid.PCD_Init();

  Serial.println("\n=== SmartAttend — Wiring Test ===");
  rfid.PCD_DumpVersionToSerial();  // Prints firmware version
  Serial.println("Scan a card...");
}

void loop() {
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) return;

  Serial.print("Card UID: ");
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (i > 0) Serial.print(":");
    if (rfid.uid.uidByte[i] < 0x10) Serial.print("0");
    Serial.print(rfid.uid.uidByte[i], HEX);
  }
  Serial.println();

  rfid.PICC_HaltA();
  delay(1000);
}
