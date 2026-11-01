/**
 * FactoryPulse AI - ESP32 Sensor & Actuator Implementation
 * Interrupt-driven optical pulse counting, motor PWM control, and sensor acquisition.
 */

#include "sensors.h"
#include "config.h"

// Static member initialization
volatile unsigned long SensorManager::pulseCount = 0;
volatile unsigned long SensorManager::lastPulseTime = 0;

void IRAM_ATTR SensorManager::onPulseInterrupt() {
    unsigned long now = micros();
    // Hardware debouncing: ignore pulses within 500 microseconds (> 30,000 RPM artifact)
    if (now - lastPulseTime > 500) {
        pulseCount++;
        lastPulseTime = now;
    }
}

SensorManager::SensorManager() :
    lastCalculationTime(0),
    currentRPM(0.0f),
    smoothedRPM(0.0f),
    simulatedQueue(5),
    mpuAvailable(false),
    dhtAvailable(false),
    acsAvailable(false) {}

void SensorManager::init() {
    // Configure IR sensor input with pullup
    pinMode(PIN_IR_SENSOR, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(PIN_IR_SENSOR), SensorManager::onPulseInterrupt, FALLING);

    // Motor driver pins
    pinMode(PIN_MOTOR_IN1, OUTPUT);
    pinMode(PIN_MOTOR_IN2, OUTPUT);
    digitalWrite(PIN_MOTOR_IN1, LOW);
    digitalWrite(PIN_MOTOR_IN2, LOW);

    // Setup PWM channel for motor speed
    ledcSetup(PWM_CHANNEL, PWM_FREQUENCY, PWM_RESOLUTION);
    ledcAttachPin(PIN_MOTOR_ENA, PWM_CHANNEL);
    ledcWrite(PWM_CHANNEL, 0);

    // Indicator LEDs
    pinMode(PIN_LED_GREEN, OUTPUT);
    pinMode(PIN_LED_YELLOW, OUTPUT);
    pinMode(PIN_LED_RED, OUTPUT);
    digitalWrite(PIN_LED_GREEN, HIGH); // Startup green
    digitalWrite(PIN_LED_YELLOW, LOW);
    digitalWrite(PIN_LED_RED, LOW);

    // Buzzer
    pinMode(PIN_BUZZER, OUTPUT);
    digitalWrite(PIN_BUZZER, LOW);

    // ADC Current sensor
    pinMode(PIN_ACS712_CURRENT, INPUT);

    lastCalculationTime = millis();
}

void SensorManager::updateRPM() {
    unsigned long now = millis();
    unsigned long dtMs = now - lastCalculationTime;

    if (dtMs >= 500) { // Calculate every 500ms
        noInterrupts();
        unsigned long pulses = pulseCount;
        pulseCount = 0;
        interrupts();

        // RPM calculation: (pulses / pulses_per_rev) * (60,000 / dt_ms)
        float calculatedRPM = ((float)pulses / (float)IR_PULSES_PER_REV) * (60000.0f / (float)dtMs);
        
        // Exponential moving average filter
        smoothedRPM = 0.7f * smoothedRPM + 0.3f * calculatedRPM;
        currentRPM = smoothedRPM;
        lastCalculationTime = now;
    }

    // Zero-speed timeout detection
    if (micros() - lastPulseTime > 2000000UL) { // No pulses for 2 seconds
        currentRPM = 0.0f;
        smoothedRPM = 0.0f;
    }
}

void SensorManager::setMotorSpeed(uint8_t pwmSpeed, bool forward) {
    if (pwmSpeed == 0) {
        emergencyStop();
        return;
    }
    if (forward) {
        digitalWrite(PIN_MOTOR_IN1, HIGH);
        digitalWrite(PIN_MOTOR_IN2, LOW);
    } else {
        digitalWrite(PIN_MOTOR_IN1, LOW);
        digitalWrite(PIN_MOTOR_IN2, HIGH);
    }
    ledcWrite(PWM_CHANNEL, pwmSpeed);
}

void SensorManager::emergencyStop() {
    digitalWrite(PIN_MOTOR_IN1, LOW);
    digitalWrite(PIN_MOTOR_IN2, LOW);
    ledcWrite(PWM_CHANNEL, 0);
    setStatusLEDs("STOPPED");
}

void SensorManager::setStatusLEDs(const String& status) {
    if (status == "NORMAL") {
        digitalWrite(PIN_LED_GREEN, HIGH);
        digitalWrite(PIN_LED_YELLOW, LOW);
        digitalWrite(PIN_LED_RED, LOW);
        digitalWrite(PIN_BUZZER, LOW);
    } else if (status == "WARNING") {
        digitalWrite(PIN_LED_GREEN, LOW);
        digitalWrite(PIN_LED_YELLOW, HIGH);
        digitalWrite(PIN_LED_RED, LOW);
    } else if (status == "CRITICAL" || status == "STOPPED") {
        digitalWrite(PIN_LED_GREEN, LOW);
        digitalWrite(PIN_LED_YELLOW, LOW);
        digitalWrite(PIN_LED_RED, HIGH);
    }
}

void SensorManager::triggerAlarm(bool enableBuzzer, int durationMs) {
    if (enableBuzzer) {
        digitalWrite(PIN_BUZZER, HIGH);
        delay(durationMs);
        digitalWrite(PIN_BUZZER, LOW);
    }
}

void SensorManager::handleLoop() {
    updateRPM();
}

SensorReadings SensorManager::getReadings() {
    SensorReadings r;
    r.rpm = currentRPM;

    // Calibration: Throughput (PPM) = Nominal_Capacity * (RPM / Base_RPM)
    float ratio = currentRPM / BASE_STATION_RPM;
    r.throughput = max(0.0f, NOMINAL_CAPACITY_PPM * ratio);
    r.cycle_time = r.throughput > 0.1f ? (60.0f / r.throughput) : 99.9f;
    r.utilization = min(1.0f, max(0.0f, ratio));

    // Dynamic queue tracking
    if (ratio < 0.6f && ratio > 0.05f) {
        simulatedQueue = min(45, simulatedQueue + 1);
    } else if (ratio >= 0.9f && simulatedQueue > 4) {
        simulatedQueue = max(3, simulatedQueue - 1);
    }
    r.queue_length = simulatedQueue;

    // Status evaluation
    if (currentRPM < 50.0f) {
        r.status = "STOPPED";
    } else if (ratio < 0.40f || simulatedQueue >= 30) {
        r.status = "CRITICAL";
    } else if (ratio < 0.70f || simulatedQueue >= 15) {
        r.status = "WARNING";
    } else {
        r.status = "NORMAL";
    }

    // Optional sensor reporting: explicit null/false when not physically present
    r.has_vibration = false;
    r.vibration = 0.0f;
    r.has_temperature = false;
    r.temperature = 0.0f;

    // Read analog ACS712 if connected
    int rawAdc = analogRead(PIN_ACS712_CURRENT);
    if (rawAdc > 500 && rawAdc < 3500) {
        r.has_current = true;
        // ACS712-05B sensitivity: 185mV/A, Vref = 3.3V
        float voltage = (rawAdc / 4095.0f) * 3.3f;
        r.current = max(0.0f, (voltage - 1.65f) / 0.185f);
    } else {
        r.has_current = false;
        r.current = 0.0f;
    }

    return r;
}

SensorManager sensors;

