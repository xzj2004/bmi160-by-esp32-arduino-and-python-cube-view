#include <Wire.h>
#include <DFRobot_BMI160.h>

DFRobot_BMI160 bmi160;
bool initialized = false;

// 加入滤波相关变量
float prev_gx = 0, prev_gy = 0, prev_gz = 0;
float prev_ax = 0, prev_ay = 0, prev_az = 0;
const float filter_alpha = 0.8; // 滤波系数

void setup() {
  Serial.begin(115200);
  delay(2000); // 增加延迟，确保串口稳定
  
  // 清除所有初始输出
  while(Serial.available()) {
    Serial.read();
  }
  
  Serial.println("BMI160初始化开始...");
  
  // 软复位
  if (bmi160.softReset() != BMI160_OK) {
    Serial.println("BMI160复位失败");
    while (1);
  }

  // 初始化I2C，默认地址0x69
  if (bmi160.I2cInit(0x69) != BMI160_OK) {
    Serial.println("BMI160初始化失败，请检查连接");
    while (1);
  }
  
  Serial.println("BMI160初始化成功");
  delay(500);
  
  // 发送一个特殊标记，表示数据开始
  Serial.println("DATA_BEGIN");
  initialized = true;
}

void loop() {
  if (!initialized) return;
  
  int16_t accelGyro[6] = {0};
  int rslt = bmi160.getAccelGyroData(accelGyro);
  
  if (rslt == 0) {
    // 加速度数据（单位：mg，1g=16384）
    float ax = accelGyro[3] / 16384.0;
    float ay = accelGyro[4] / 16384.0;
    float az = accelGyro[5] / 16384.0;
    
    // 陀螺仪数据（单位：°/s，直接使用度数不转换为弧度）
    float gx = accelGyro[0];
    float gy = accelGyro[1];
    float gz = accelGyro[2];
    
    // 简单低通滤波，减少噪声
    ax = filter_alpha * ax + (1-filter_alpha) * prev_ax;
    ay = filter_alpha * ay + (1-filter_alpha) * prev_ay;
    az = filter_alpha * az + (1-filter_alpha) * prev_az;
    
    gx = filter_alpha * gx + (1-filter_alpha) * prev_gx;
    gy = filter_alpha * gy + (1-filter_alpha) * prev_gy;
    gz = filter_alpha * gz + (1-filter_alpha) * prev_gz;
    
    // 保存当前值为下次滤波做准备
    prev_ax = ax; prev_ay = ay; prev_az = az;
    prev_gx = gx; prev_gy = gy; prev_gz = gz;
    
    // 在陀螺仪数据上应用一个缩放因子，使旋转更接近1:1
    gx *= 0.75;
    gy *= 0.75;
    gz *= 0.75;

    // 输出格式：ax,ay,az,gx,gy,gz
    Serial.print(ax, 4);
    Serial.print(",");
    Serial.print(ay, 4);
    Serial.print(",");
    Serial.print(az, 4);
    Serial.print(",");
    Serial.print(gx, 4);
    Serial.print(",");
    Serial.print(gy, 4);
    Serial.print(",");
    Serial.println(gz, 4); // 修改为println，移除多余的逗号
  } else {
    Serial.println("读取数据失败，错误代码：" + String(rslt));
    delay(1000);  // 错误时延长等待时间
  }
  
  delay(10);  // 100Hz采样率
}
