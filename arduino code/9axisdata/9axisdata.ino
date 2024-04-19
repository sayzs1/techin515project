#include <MPU9250.h>
#include <Wire.h>

MPU9250 mpu;

void setup() {
    Serial.begin(115200);
    Wire.begin();
    delay(2000);

    if (!mpu.setup(0x68)) {  // change to your own address
        while (1) {
            Serial.println("MPU connection failed. Please check your connection with `connection_check` example.");
            delay(5000);
        }
    }
}

void loop() {
  if (mpu.update()) {
    int16_t ax = mpu.getAccX();
    int16_t ay = mpu.getAccY();
    int16_t az = mpu.getAccZ();
    int16_t gx = mpu.getGyroX();
    int16_t gy = mpu.getGyroY() - 1;
    int16_t gz = mpu.getGyroZ();
    int16_t mx = mpu.getMagX();
    int16_t my = mpu.getMagY();
    int16_t mz = mpu.getMagZ();

    Serial.print(ax); Serial.print("\t");
    Serial.print(ay); Serial.print("\t");
    Serial.print(az); Serial.print("\t");
    Serial.print(gx); Serial.print("\t");
    Serial.print(gy); Serial.print("\t");
    Serial.print(gz); Serial.print("\t");
    Serial.print(mx); Serial.print("\t");
    Serial.print(my); Serial.print("\t");
    Serial.println(mz);
  }
  delay(10);  // Small delay to stabilize data stream
}
