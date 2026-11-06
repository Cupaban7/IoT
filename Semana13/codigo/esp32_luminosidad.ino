#include <WiFi.h>
#include <PubSubClient.h>

// Configuración WiFi
const char* ssid = "TU_SSID_WIFI";
const char* password = "TU_PASSWORD_WIFI";

// Credenciales de Adafruit IO
#define AIO_SERVER      "io.adafruit.com"
#define AIO_SERVERPORT  1883
#define AIO_USERNAME    "TU_USUARIO_ADAFRUIT"
#define AIO_KEY         "TU_AIO_KEY"

// Definición de pines y tópicos
#define LDR_PIN 34 // Sensor LDR conectado al pin analógico 34[cite: 11]
const char* TOPIC_LUMINOSIDAD = AIO_USERNAME "/feeds/luminosidad"; // Feed de luminosidad[cite: 11]

WiFiClient espClient;
PubSubClient client(espClient);

unsigned long lastPublishTime = 0;
const unsigned long publishInterval = 12000; // Publicación cada 12 segundos (rango 10-15s)[cite: 11]

void setupWiFi() {
  delay(10);
  Serial.print("\nConectando a ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi conectado.");
}

void reconnect() {
  while (!client.connected()) { // Función para mantener viva la conexión MQTT[cite: 11]
    Serial.print("Intentando conexión a Adafruit IO...");
    String clientId = "ESP32_Aula_Luz_" + String(random(0xffff), HEX);
    if (client.connect(clientId.c_str(), AIO_USERNAME, AIO_KEY)) {
      Serial.println("[OK] Conectado");
    } else {
      Serial.print("Fallo, rc=");
      Serial.print(client.state());
      Serial.println(" Reintentando en 3 segundos...");
      delay(3000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  setupWiFi();
  client.setServer(AIO_SERVER, AIO_SERVERPORT);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  unsigned long currentMillis = millis();
  
  // Evitamos el uso de delay() prolongados que rompan la conexión MQTT[cite: 11]
  if (currentMillis - lastPublishTime >= publishInterval) {
    lastPublishTime = currentMillis;

    // Lectura del sensor LDR
    int rawValue = analogRead(LDR_PIN);
    
    // Mapeo aproximado a Lux (Requiere calibración física según la resistencia usada)
    // Se invierte el valor asumiendo un divisor de tensión estándar
    int luxAprox = map(rawValue, 4095, 0, 0, 1000); 

    // Publicar en Adafruit IO
    client.publish(TOPIC_LUMINOSIDAD, String(luxAprox).c_str());
    
    Serial.print("Luminosidad publicada: ");
    Serial.print(luxAprox);
    Serial.println(" lux"); // Verificación en el monitor serial[cite: 11]
  }
}