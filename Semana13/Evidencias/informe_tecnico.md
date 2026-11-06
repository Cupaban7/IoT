# Informe Técnico y Preguntas de Reflexión - Semana 13

**Autores:** Juan Diego Cupaban Mejía & Andrea Vanessa Fonseca Gómez

### 1. ¿Qué ventaja ofrece IFTTT frente a programar el envío de correos directamente desde el ESP32?
IFTTT abstrae por completo la compleja capa de seguridad (certificados TLS/SSL) y los protocolos de mensajería (como SMTP para correos) que normalmente saturarían al microcontrolador. Programar el envío directo desde el ESP32 consume mucha memoria dinámica, bloquea el procesador durante las conexiones seguras, y hace que el sistema sea rígido. Con IFTTT, el ESP32 solo se preocupa por enviar un dato ligero por MQTT a Adafruit, y la nube se encarga del procesamiento pesado, permitiendo además cambiar el destino o tipo de la alerta sin tener que reprogramar la placa.

### 2. ¿Por qué es importante que el ESP32 publique datos con una frecuencia adecuada (10-15 s) para que IFTTT funcione correctamente?
IFTTT evalúa transiciones y estados estables para disparar sus Applets. Si publicamos datos demasiado rápido (ej. cada segundo), podemos superar el límite de peticiones (rate limit) de la versión gratuita de Adafruit IO, provocando un bloqueo temporal de la cuenta y pérdida de información. Una ventana de 10 a 15 segundos garantiza que la base de datos se actualice de forma segura y le da tiempo a los algoritmos de integración en la nube para registrar el cambio de variable y ejecutar el *Trigger* correctamente.

### 3. ¿Qué otras acciones (That) podrían configurarse en IFTTT además de la notificación push, y cómo beneficiarían al proyecto integrador?
Para un proyecto de monitoreo académico, se podrían integrar acciones como:
*   **Google Sheets:** Para registrar un log histórico de cada anomalía (fecha, hora, aula y valor de luz). Ideal para auditorías y control de calidad.
*   **Telegram/WhatsApp:** Configurar un bot que envíe un mensaje automático a un grupo del personal de mantenimiento o vigilancia, logrando una respuesta operativa mucho más ágil que un correo o una notificación personal.
*   **Correos electrónicos (Email):** Para enviar avisos formales de mantenimiento preventivo si el sensor se queda pegado en 0 por daño físico.

### 4. ¿Qué limitaciones encontró al usar la versión gratuita de Adafruit IO y de IFTTT?
Durante el desarrollo del proyecto experimentamos en carne propia la limitación de consulta (polling) de IFTTT gratuito. El servidor no evalúa los cambios en tiempo real, sino que revisa el feed de Adafruit IO en intervalos prolongados. Esto causó que al simular anomalías, las alertas se acumularan en una cola de espera y llegaran cientos de notificaciones de golpe casi 30 minutos después. 
Además, la limitación de Adafruit IO de retener datos solo por 30 días impide realizar análisis a largo plazo, como comparar la iluminación de las aulas entre diferentes semestres o estaciones del año, lo cual requeriría conectar una base de datos externa persistente.