#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

// --- Credenciales Wi-Fi (Solo redes 2.4 GHz) ---
const char* ssid = "Flia_Cupaban_Mejia";
const char* password = "Nicolas29";

// --- Credenciales Adafruit IO ---
#define AIO_SERVER      "io.adafruit.com"
#define AIO_SERVERPORT  1883
#define AIO_USERNAME    "cupaban"
#define AIO_KEY         "aio_iAnE46ZCGHKri0cVI7nzas3mh660"

// --- Definición de Pines ---
#define PIN_LDR     34  // Módulo LDR digital (DO)
#define PIN_DHT     4   // Sensor DHT11 (DATA)
#define PIN_LED     2   // LED rojo de alerta por baja luminosidad
#define PIN_BUZZER  23  // Buzzer de alerta por alta temperatura

#define DHTTYPE DHT11
DHT dht(PIN_DHT, DHTTYPE);

WiFiClient client;
PubSubClient mqtt(client);

String feed_luminosidad = String(AIO_USERNAME) + "/feeds/luminosidad";
String feed_temperatura = String(AIO_USERNAME) + "/feeds/temperatura";

// Control temporal no bloqueante (millis)
unsigned long tiempoAnteriorLuz = 0;
const long intervaloLuz = 5000;     // Publicar luz cada 5 segundos

unsigned long tiempoAnteriorTemp = 0;
const long intervaloTemp = 10000;   // Publicar temperatura cada 10 segundos

void conectarWiFi() {
  Serial.print("Conectando a WiFi: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n[OK] WiFi conectado.");
}

void reconectarMQTT() {
  while (!mqtt.connected()) {
    Serial.print("Conectando a Adafruit IO...");
    String clientId = "ESP32_Aula_" + String(random(0, 1000));
    if (mqtt.connect(clientId.c_str(), AIO_USERNAME, AIO_KEY)) {
      Serial.println(" [OK]");
    } else {
      Serial.print(" Fallo rc=");
      Serial.print(mqtt.state());
      Serial.println(". Reintentando en 3s...");
      delay(3000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_LDR, INPUT);
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  dht.begin();

  digitalWrite(PIN_LED, LOW);
  digitalWrite(PIN_BUZZER, LOW);

  conectarWiFi();
  mqtt.setServer(AIO_SERVER, AIO_SERVERPORT);
}

void loop() {
  if (!mqtt.connected()) {
    reconectarMQTT();
  }
  mqtt.loop();

  unsigned long tiempoActual = millis();

  // 1. Tarea de Luminosidad (Lógica inversa: 0 = luz -> 1000, 1 = oscuridad -> 0)
  if (tiempoActual - tiempoAnteriorLuz >= intervaloLuz) {
    tiempoAnteriorLuz = tiempoActual;
    int estadoLuz = digitalRead(PIN_LDR);
    int valorLuzEnviar = (estadoLuz == 0) ? 1000 : 0;

    digitalWrite(PIN_LED, (valorLuzEnviar == 0) ? HIGH : LOW);
    mqtt.publish(feed_luminosidad.c_str(), String(valorLuzEnviar).c_str());
    Serial.print("Luminosidad enviada: ");
    Serial.println(valorLuzEnviar);
  }

  // 2. Tarea de Temperatura (DHT11)
  if (tiempoActual - tiempoAnteriorTemp >= intervaloTemp) {
    tiempoAnteriorTemp = tiempoActual;
    float t = dht.readTemperature();

    if (!isnan(t)) {
      digitalWrite(PIN_BUZZER, (t > 30.0) ? HIGH : LOW);
      mqtt.publish(feed_temperatura.c_str(), String(t).c_str());
      Serial.print("Temperatura enviada: ");
      Serial.print(t);
      Serial.println(" °C");
    } else {
      Serial.println("[Error] Fallo de lectura en sensor DHT11.");
    }
  }
}