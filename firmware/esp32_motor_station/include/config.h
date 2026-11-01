/**
 * FactoryPulse AI - ESP32 Hardware Station Pinout and Configuration Header
 */

#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

// =============================================================================
// 1. NETWORK & MQTT CONFIGURATION
// =============================================================================
#define DEFAULT_WIFI_SSID       "Factory_WiFi_Network"
#define DEFAULT_WIFI_PASS       "FactorySecure2026"

// Set to your local broker IP (e.g. 192.168.1.100) or HiveMQ Cloud host
#define MQTT_BROKER_HOST        "192.168.1.100"
#define MQTT_BROKER_PORT        1883
#define MQTT_CLIENT_ID          "esp32_station02_motor"
#define MQTT_USER               ""
#define MQTT_PASSWORD           ""

// MQTT Topics
#define TOPIC_TELEMETRY         "factory/station02/telemetry"
#define TOPIC_STATUS            "factory/devices/motor01/status"
#define TOPIC_COMMANDS          "factory/devices/motor01/commands"
#define TOPIC_ALERTS            "factory/alerts"

// =============================================================================
// 2. HARDWARE GPIO PIN ASSIGNMENTS (ESP32 DevKit V1)
// =============================================================================
// IR Speed Sensor (Optical encoder disc pulse counter)
#define PIN_IR_SENSOR           18      // Digital Input (Interrupt capable, internal pullup)

// L298N Dual H-Bridge Motor Driver
#define PIN_MOTOR_ENA           25      // PWM Speed Control (ESP32 LEDC PWM)
#define PIN_MOTOR_IN1           26      // Direction Input 1
#define PIN_MOTOR_IN2           27      // Direction Input 2

// Visual Status Indicators (LEDs)
#define PIN_LED_GREEN           19      // Normal Operation
#define PIN_LED_YELLOW          21      // Warning Alert State
#define PIN_LED_RED             22      // Critical Alarm / Emergency Stoppage

// Audible Alarm (Active 3.3V Buzzer or Transistor Driver)
#define PIN_BUZZER              23      // Active Buzzer Output

// Optional Industrial Sensors
#define PIN_ACS712_CURRENT      34      // ADC1 Channel 6 (Current sensor analog output)
#define PIN_DHT_DATA            15      // DHT11 / DHT22 Temperature & Humidity
#define PIN_I2C_SDA             4       // MPU6050 Accelerometer/Vibration SDA
#define PIN_I2C_SCL             5       // MPU6050 Accelerometer/Vibration SCL

// =============================================================================
// 3. PHYSICAL MOTOR & SAMPLING PARAMETERS
// =============================================================================
#define IR_PULSES_PER_REV       20      // Number of slots in optical encoder disk
#define SAMPLING_INTERVAL_MS    1000    // Telemetry publish interval (1.0 second)
#define PWM_FREQUENCY           20000   // 20 kHz PWM (silent, smooth DC motor drive)
#define PWM_CHANNEL             0       // LEDC PWM Channel
#define PWM_RESOLUTION          8       // 8-bit resolution (0 - 255)

#define BASE_STATION_RPM        1500.0f
#define NOMINAL_CAPACITY_PPM    15.0f   // Nominal capacity: 15 parts per minute

#endif // CONFIG_H

