#include "Wire.h"
#include "I2Cdev.h"
#include "MPU6050_6Axis_MotionApps612.h"

// initialize the two MPUs with their I2C ID
MPU6050 mpu_primary(0x68);
MPU6050 mpu_secondary(0x69);

uint8_t status_code = 0U;      // return status after each device operation (0 = success, !0 = error)

void setup() {
  Wire.begin();

  // it seems that we cannot use too high clock rate, due to the long I2C wire.
  // cannot flash firmware if signal integrity is too bad.
  // Wire.setClock(400000);
  Wire.setClock(100000);

  Serial.begin(115200);
  
  // initialize device
  Serial.print("{\"key\": \"/log\", \"value\": \"Initializing device 0x68...\", \"level\": \"DEBUG\"}\n");
  mpu_primary.initialize();
  status_code = mpu_primary.dmpInitialize();
  
  // 1 = initial memory load failed
  // 2 = DMP configuration updates failed
  // (if it's going to break, usually the code will be 1)
  if (status_code == 1U) {
    Serial.print("{\"key\": \"/log\", \"value\": \"device 0x68 initialization failed: initial memory load failed.\", \"level\": \"ERROR\"}\n");
    while (1) {}
  }
  if (status_code == 2U) {
    Serial.print("{\"key\": \"/log\", \"value\": \"device 0x68 initialization failed: DMP configuration updates failed.\", \"level\": \"ERROR\"}\n");
    while (1) {}
  }
  
  Serial.print("{\"key\": \"/log\", \"value\": \"Initializing device 0x69...\", \"level\": \"DEBUG\"}\n");
  mpu_secondary.initialize();
  status_code = mpu_secondary.dmpInitialize();

  // 1 = initial memory load failed
  // 2 = DMP configuration updates failed
  // (if it's going to break, usually the code will be 1)
  if (status_code == 1U) {
    Serial.print("{\"key\": \"/log\", \"value\": \"device 0x69 initialization failed: initial memory load failed.\", \"level\": \"ERROR\"}\n");
    while (1) {}
  }
  if (status_code == 2U) {
    Serial.print("{\"key\": \"/log\", \"value\": \"device 0x69 initialization failed: DMP configuration updates failed.\", \"level\": \"ERROR\"}\n");
    while (1) {}
  }

  // verify connection
  if (!mpu_primary.testConnection()) {
    Serial.print("{\"key\": \"/log\", \"value\": \"device 0x68 connection failed.\", \"level\": \"ERROR\"}\n"); 
  }
  if (!mpu_secondary.testConnection()) {
    Serial.print("{\"key\": \"/log\", \"value\": \"device 0x69 connection failed.\", \"level\": \"ERROR\"}\n");
  }

  // supply your own gyro offsets here, scaled for min sensitivity
  mpu_primary.setXGyroOffset(0);
  mpu_primary.setYGyroOffset(0);
  mpu_primary.setZGyroOffset(0);
  mpu_primary.setXAccelOffset(0);
  mpu_primary.setYAccelOffset(0);
  mpu_primary.setZAccelOffset(0);
  
  mpu_secondary.setXGyroOffset(0);
  mpu_secondary.setYGyroOffset(0);
  mpu_secondary.setZGyroOffset(0);
  mpu_secondary.setXAccelOffset(0);
  mpu_secondary.setYAccelOffset(0);
  mpu_secondary.setZAccelOffset(0);

  
  // Calibration Time: generate offsets and calibrate our MPU6050
  mpu_primary.CalibrateAccel(6);
  mpu_primary.CalibrateGyro(6);
  
  mpu_secondary.CalibrateAccel(6);
  mpu_secondary.CalibrateGyro(6);

  // calibration procedure will dump garbage on serial, we use a newline to fence it
  Serial.print("\n");
  
  // turn on the DMP, now that it's ready
  Serial.print("{\"key\": \"/log\", \"value\": \"Enabling DMP...\", \"level\": \"DEBUG\"}\n");
  mpu_primary.setDMPEnabled(true);
  mpu_secondary.setDMPEnabled(true);
  Serial.print("{\"key\": \"/log\", \"value\": \"Device ready.\", \"level\": \"INFO\"}\n");
}

void loop() {
  // Get the Latest packet 
  uint8_t fifo_buffer_primary[64]; // FIFO storage buffer
  if (!mpu_primary.dmpGetCurrentFIFOPacket(fifo_buffer_primary)) {
    return;
  }

  uint8_t fifo_buffer_secondary[64]; // FIFO storage buffer
  if (!mpu_secondary.dmpGetCurrentFIFOPacket(fifo_buffer_secondary)) {
    return;
  }
  
  // orientation/motion vars
  Quaternion quat_primary;           // [w, x, y, z]         quaternion container
  Quaternion quat_secondary;           // [w, x, y, z]         quaternion container

  mpu_primary.dmpGetQuaternion(&quat_primary, fifo_buffer_primary);
  mpu_secondary.dmpGetQuaternion(&quat_secondary, fifo_buffer_secondary);
  
  Serial.print("{\"key\": \"/joint/2\", \"value\": [");
  Serial.print(quat_primary.w);Serial.print(", ");
  Serial.print(quat_primary.x);Serial.print(", ");
  Serial.print(quat_primary.y);Serial.print(", ");
  Serial.print(quat_primary.z);
  Serial.print("]}\n");
  
  Serial.print("{\"key\": \"/joint/3\", \"value\": [");
  Serial.print(quat_secondary.w);Serial.print(", ");
  Serial.print(quat_secondary.x);Serial.print(", ");
  Serial.print(quat_secondary.y);Serial.print(", ");
  Serial.print(quat_secondary.z);
  Serial.print("]}\n");
}
