/**
 * FactoryPulse AI - ESP32 Sensor & Actuator Abstraction Header
 */

#ifndef SENSORS_H
#define SENSORS_H

#include <Arduino.h>

struct SensorReadings {
    float rpm;
    float cycle_time;
    float throughput;
    float utilization;
    int queue_length;
    String status; // "NORMAL", "WARNING", "CRITICAL", "STOPPED"
    bool has_vibration;
    float vibration;
    bool has_temperature;
    float temperature;
    bool has_current;
    float current;
};

class SensorManager {
public:
    SensorManager();
    void init();
    void updateRPM();
    SensorReadings getReadings();
    
    // Actuators
    void setMotorSpeed(uint8_t pwmSpeed, bool forward = true);
    void emergencyStop();
    void setStatusLEDs(const String& status);
    void triggerAlarm(bool enableBuzzer, int durationMs = 1000);
    void handleLoop();

    // Pulse counter ISR
    static void IRAM_ATTR onPulseInterrupt();

private:
    static volatile unsigned long pulseCount;
    static volatile unsigned long lastPulseTime;
    unsigned long lastCalculationTime;
    float currentRPM;
    float smoothedRPM;
    int simulatedQueue;

    // Optional sensor flags
    bool mpuAvailable;
    bool dhtAvailable;
    bool acsAvailable;
};

extern SensorManager sensors;

#endif // SENSORS_H

