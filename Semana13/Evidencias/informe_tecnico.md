# **Informe Técnico de Documentación IoT** 

## **1. Situación Problema y Objetivos** 

El coordinador académico de la institución no puede permanecer constantemente frente al dashboard de Adafruit IO supervisando los parámetros ambientales de las aulas. Surge la necesidad de implementar un flujo automatizado en la nube que notifique de forma inmediata a su dispositivo móvil al detectarse anomalías, específicamente cuando la luminosidad ambiental desciende por debajo del umbral de 100 lux (evento que simula el apagado de luces o un cambio ambiental crítico en el aula). 

### **Objetivos Específicos del Proyecto** 

- **Configuración de Infraestructura IoT:** Desplegar y vincular un feed llamado 'luminosidad' en Adafruit IO para la ingesta continua de lecturas desde el ESP32. 

- **Visualización Histórica:** Diseñar un widget Line Chart en el dashboard de Adafruit IO para monitorear la tendencia temporal de luz. 

- **Automatización Cloud con IFTTT:** Construir un Applet bajo la regla Trigger-Action (This → That) conectando Adafruit IO con el servicio de Notificaciones. 

- **Validación en Entorno Real:** Verificar la recepción de notificaciones Push móviles al cubrir el sensor de luminosidad. 

- **Documentación Técnica:** Estructurar y entregar el repositorio en GitHub con evidencias verificables y código comentado. 

## **2. Arquitectura del Sistema y Materiales** 

El flujo de datos sigue un modelo distribuido de capas bien definidas: 

- **Capa de Captura (Hardware):** ESP32 DevKit junto con un sensor de luminosidad (LDR con divisor de tensión en el pin ADC GPIO 34 o módulo digital I2C BH1750). 

- **Capa de Comunicación (Firmware):** Código desarrollado en Arduino IDE utilizando las librerías WiFi.h, PubSubClient.h y Adafruit_MQTT.h publicando vía protocolo MQTT en el puerto 1883. 

- **Capa Nube & Almacenamiento:** Servidor io.adafruit.com administrando el feed de datos y renderizado del gráfico de líneas. 

- **Capa de Automatización & Alerta:** Plataforma IFTTT evaluando la condición de disparo (< 100 lux) y despachando la notificación Push a la app móvil. 

|**Recurso / Componente**|**Descripción y Función en el Sistema**|
|---|---|
|**Hardware**|ESP32 DevKit, Sensor LDR / BH1750, Resistencia 10kΩ, Protoboard y|
||Cables Dupont.|
|**Software & Librerías**|Arduino IDE, WiFi.h, PubSubClient.h, Adafruit_MQTT.h.|
|**Plataformas Cloud & Apps**|Cuenta gratuita Adafruit IO, IFTTT Cloud Service, App IFTTT para|



Android/iOS, Repositorio GitHub. 

## **3. Respuestas a las Preguntas de Reflexión** 

**1. ¿Qué ventaja ofrece IFTTT frente a programar el envío de correos directamente desde el ESP32?** IFTTT abstrae por completo la compleja capa de seguridad (certificados TLS/SSL) y los protocolos de mensajería (como SMTP para correos) que normalmente saturarían al microcontrolador. Programar el envío directo desde el ESP32 consume mucha memoria dinámica, bloquea el procesador durante las conexiones seguras, y hace que el sistema sea rígido. Con IFTTT, el ESP32 solo se preocupa por enviar un dato ligero por MQTT a Adafruit, y la nube se encarga del procesamiento pesado, permitiendo además cambiar el destino o tipo de la alerta sin tener que reprogramar la placa. 

**2. ¿Por qué es importante que el ESP32 publique datos con una frecuencia adecuada (10-15 s) para que IFTTT funcione correctamente?** 

IFTTT evalúa transiciones y estados estables para disparar sus Applets. Si publicamos datos demasiado rápido (ej. cada segundo), podemos superar el límite de peticiones (rate limit) de la versión gratuita de Adafruit IO, provocando un bloqueo temporal de la cuenta y pérdida de información. Una ventana de 10 a 15 segundos garantiza que la base de datos se actualice de forma segura y le da tiempo a los algoritmos de integración en la nube para registrar el cambio de variable y ejecutar el Trigger correctamente. 

**3. ¿Qué otras acciones (That) podrían configurarse en IFTTT además de la notificación push, y cómo beneficiarían al proyecto integrador?** 

Para un proyecto de monitoreo académico, se podrían integrar acciones como: 

   - Google Sheets: Para registrar un log histórico de cada anomalía (fecha, hora, aula y valor de luz). Ideal para auditorías y control de calidad. 

   - Telegram/WhatsApp: Configurar un bot que envíe un mensaje automático a un grupo del personal de mantenimiento o vigilancia, logrando una respuesta operativa mucho más ágil que un correo o una notificación personal. 

   - Correos electrónicos (Email): Para enviar avisos formales de mantenimiento preventivo si el sensor se queda pegado en 0 por daño físico. 

**4. ¿Qué limitaciones encontró al usar la versión gratuita de Adafruit IO y de IFTTT?** 

- Durante el desarrollo del proyecto experimentamos en carne propia la limitación de consulta (polling) de IFTTT gratuito. El servidor no evalúa los cambios en tiempo real, sino que revisa el feed de Adafruit IO en intervalos prolongados. Esto causó que al simular anomalías, las alertas se acumularan en una cola de espera y llegaran cientos de notificaciones de golpe casi 30 minutos después. Además, la limitación de Adafruit IO de retener datos solo por 30 días impide realizar análisis a largo plazo, como comparar la iluminación de las aulas entre diferentes semestres o estaciones del año, lo cual requeriría conectar una base de datos externa persistente. 

## **4. Código Fuente Comentado (esp32_luminosidad.ino)** 

#include <WiFi.h> 

#include <PubSubClient.h> 

// Configuración WiFi const char* ssid = "TU_SSID_WIFI"; const char* password = "TU_PASSWORD_WIFI"; 

// Credenciales de Adafruit IO #define AIO_SERVER      "io.adafruit.com" #define AIO_SERVERPORT  1883 #define AIO_USERNAME    "TU_USUARIO_ADAFRUIT" #define AIO_KEY         "TU_AIO_KEY" 

// Definición de pines y tópicos #define LDR_PIN 34 // Sensor LDR conectado al pin analógico 34[cite: 11] 

const char* TOPIC_LUMINOSIDAD = AIO_USERNAME "/feeds/luminosidad"; // Feed de luminosidad[cite: 11] 

WiFiClient espClient; PubSubClient client(espClient); 

unsigned long lastPublishTime = 0; 

const unsigned long publishInterval = 12000; // Publicación cada 12 segundos (rango 10-15s)[cite: 11] 

void setupWiFi() { delay(10); Serial.print("\nConectando a "); 

Serial.println(ssid); WiFi.begin(ssid, password); while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); } Serial.println("\nWiFi conectado."); } 

void reconnect() { while (!client.connected()) { // Función para mantener viva la conexión MQTT[cite: 11] Serial.print("Intentando conexión a Adafruit IO..."); String clientId = "ESP32_Aula_Luz_" + String(random(0xf **f** ), HEX); if (client.connect(clientId.c_str(), AIO_USERNAME, AIO_KEY)) { Serial.println("[OK] Conectado"); } else { Serial.print("Fallo, rc="); Serial.print(client.state()); Serial.println(" Reintentando en 3 segundos..."); delay(3000); } } } 

void setup() { 

Serial.begin(115200); setupWiFi(); client.setServer(AIO_SERVER, AIO_SERVERPORT); 

} 

void loop() { if (!client.connected()) { reconnect(); } client.loop(); 

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

Serial.print(luxAprox); Serial.println(" lux"); // Verificación en el monitor serial[cite: 11] 

} 

} 

