/**
 * FactoryPulse AI - ESP32 Hardware Workstation Station 2 Firmware
 * Implements WiFi, MQTT, IR Pulse Counter, L298N Control, Status LEDs, and Buzzer.
 */

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <time.h>
#include "mqtt_ca.h"
#include <PubSubClient.h>
#include <ArduinoJson.h>

#include "config.h"
#include "sensors.h"

WiFiClientSecure espClient;
PubSubClient mqttClient(espClient);

unsigned long lastTelemetryTime = 0;
unsigned long lastStatusTime = 0;

void setupWiFi() {
    delay(10);
    Serial.println();
    Serial.print("[WiFi] Connecting to SSID: ");
    Serial.println(DEFAULT_WIFI_SSID);

    WiFi.mode(WIFI_STA);
    WiFi.begin(DEFAULT_WIFI_SSID, DEFAULT_WIFI_PASS);

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
        delay(500);
        Serial.print(".");
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println();
        Serial.print("[WiFi] Connected! IP Address: ");
        Serial.println(WiFi.localIP());
    } else {
        Serial.println("\n[WiFi] Connection timed out. Running in offline/demo mode.");
    }
}

void onMqttMessage(char* topic, byte* payload, unsigned int length) {
    char messageBuffer[1024];
    if (length >= sizeof(messageBuffer)) length = sizeof(messageBuffer) - 1;
    memcpy(messageBuffer, payload, length);
    messageBuffer[length] = '\0';

    Serial.print("[MQTT] Message received on topic: ");
    Serial.println(topic);

    JsonDocument doc;
    DeserializationError error = deserializeJson(doc, messageBuffer);
    if (error) {
        Serial.print("[JSON] Parse error: ");
        Serial.println(error.c_str());
        return;
    }

    String topicStr = String(topic);

    // 1. Motor Command Topic
    if (topicStr == TOPIC_COMMANDS) {
        const char* action = doc["action"];
        if (!action) return;

        Serial.print("[CMD] Executing action: ");
        Serial.println(action);

        if (strcmp(action, "SET_SPEED") == 0) {
            int speedPwm = doc["speed_pwm"] | 200;
            sensors.setMotorSpeed((uint8_t)speedPwm, true);
        } else if (strcmp(action, "STOP") == 0) {
            sensors.emergencyStop();
        } else if (strcmp(action, "START") == 0) {
            sensors.setMotorSpeed(200, true);
        } else if (strcmp(action, "RESET_ALARM") == 0) {
            sensors.setStatusLEDs("NORMAL");
        }
    }
    // 2. Alert Events Topic
    else if (topicStr == TOPIC_ALERTS) {
        const char* severity = doc["severity"];
        if (severity) {
            if (strcmp(severity, "CRITICAL") == 0) {
                sensors.setStatusLEDs("CRITICAL");
                sensors.triggerAlarm(true, 500); // 500ms audible burst
            } else if (strcmp(severity, "WARNING") == 0) {
                sensors.setStatusLEDs("WARNING");
            } else if (strcmp(severity, "NORMAL") == 0) {
                sensors.setStatusLEDs("NORMAL");
            }
        }
    }
}

void reconnectMQTT() {
    if (WiFi.status() != WL_CONNECTED || time(nullptr) < 1700000000) return;

    while (!mqttClient.connected()) {
        Serial.print("[MQTT] Connecting to broker ");
        Serial.print(MQTT_BROKER_HOST);
        Serial.print("...");

        if (mqttClient.connect(MQTT_CLIENT_ID, MQTT_USER, MQTT_PASSWORD)) {
            Serial.println(" Connected!");
            mqttClient.subscribe(TOPIC_COMMANDS);
            mqttClient.subscribe(TOPIC_ALERTS);
            Serial.println("[MQTT] Subscriptions registered.");
        } else {
            Serial.print(" Failed, rc=");
            Serial.print(mqttClient.state());
            Serial.println(" (retrying in 5 seconds)");
            delay(5000);
            break; // Non-blocking retry in main loop
        }
    }
}

void publishTelemetry() {
    SensorReadings r = sensors.getReadings();

    JsonDocument doc;
    doc["schema_version"] = "1.0.0";
    doc["message_id"] = "esp32_" + String(millis());
    doc["station_id"] = "station02";
    doc["station_name"] = "Drilling/Machining (Real ESP32)";
    doc["source"] = "hardware";
    doc["rpm"] = round(r.rpm * 10.0f) / 10.0f;
    doc["cycle_time"] = round(r.cycle_time * 100.0f) / 100.0f;
    doc["throughput"] = round(r.throughput * 100.0f) / 100.0f;
    doc["utilization"] = round(r.utilization * 1000.0f) / 1000.0f;
    doc["queue_length"] = r.queue_length;
    doc["status"] = r.status;

    // Explicit null when sensors are unequipped
    if (r.has_vibration) doc["vibration"] = r.vibration;
    else doc["vibration"] = nullptr;

    if (r.has_temperature) doc["temperature"] = r.temperature;
    else doc["temperature"] = nullptr;

    if (r.has_current) doc["current"] = r.current;
    else doc["current"] = nullptr;

    char buffer[512];
    serializeJson(doc, buffer);
    mqttClient.publish(TOPIC_TELEMETRY, buffer);
    sensors.setStatusLEDs(r.status);
}

void publishDeviceStatus() {
    JsonDocument doc;
    doc["device_id"] = "motor01";
    doc["station_id"] = "station02";
    doc["wifi_rssi"] = WiFi.RSSI();
    doc["ip_address"] = WiFi.localIP().toString();
    doc["free_heap"] = ESP.getFreeHeap();
    doc["uptime_sec"] = millis() / 1000;
    doc["firmware_version"] = "1.0.0";

    char buffer[256];
    serializeJson(doc, buffer);
    mqttClient.publish(TOPIC_STATUS, buffer);
}

void setup() {
    Serial.begin(115200);
    delay(500);
    Serial.println("\n=======================================================");
    Serial.println("FactoryPulse AI — ESP32 Motor Station Firmware v1.0.0");
    Serial.println("College Engineering Demonstration Firmware");
    Serial.println("=======================================================");

    sensors.init();
    setupWiFi();

    if (WiFi.status() == WL_CONNECTED) {
        configTime(0, 0, "pool.ntp.org", "time.google.com");

        unsigned long start = millis();
        while (time(nullptr) < 1700000000 &&
               millis() - start < 15000) {
            delay(200);
        }
    }

    espClient.setCACert(MQTT_ROOT_CA);

    mqttClient.setServer(MQTT_BROKER_HOST, MQTT_BROKER_PORT);
    mqttClient.setCallback(onMqttMessage);

    // Initial safe speed (nominal)
    sensors.setMotorSpeed(0, true);
}

void loop() {
    sensors.handleLoop();

    if (WiFi.status() == WL_CONNECTED) {
        if (!mqttClient.connected()) {
            reconnectMQTT();
        }
        mqttClient.loop();
    }

    unsigned long now = millis();
    // 1. Telemetry Publishing Interval (1000ms)
    if (now - lastTelemetryTime >= SAMPLING_INTERVAL_MS) {
        lastTelemetryTime = now;
        publishTelemetry();
    }

    // 2. Device Status Heartbeat (5000ms)
    if (now - lastStatusTime >= 5000) {
        lastStatusTime = now;
        publishDeviceStatus();
    }
}

