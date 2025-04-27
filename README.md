# BMI160姿态可视化项目

这个项目包含两个主要部分：
1. ESP32读取BMI160传感器数据的Arduino程序
2. 用Python实现的3D立方体实时姿态显示程序

## 硬件要求
- ESP32开发板
- BMI160传感器模块
- 连接用的杜邦线

## 接线说明
ESP32与BMI160的连接：
- SDA -> GPIO21
- SCL -> GPIO22
- VCC -> 3.3V
- GND -> GND

## Arduino程序使用说明
1. 安装必要的库：
   - Wire库（Arduino标准库）
   - BMI160库（通过Arduino库管理器安装）
2. 将代码上传到ESP32
3. 打开串口监视器，波特率设置为115200

## Python程序使用说明
1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 运行程序：
   ```bash
   python cube_visualization.py
   ```

3. 配置：
   - 默认使用COM3串口，如需修改，请在代码中更改Serial端口
   - 串口波特率设置为115200

## 注意事项
- 确保ESP32和电脑已经正确连接
- 运行Python程序前，确保Arduino程序已经在运行
- 如果立方体显示异常，检查传感器的安装方向是否正确

## 程序说明
- Arduino程序每10ms发送一次传感器数据
- Python程序使用互补滤波算法融合加速度计和陀螺仪数据
- 3D显示使用PyGame和OpenGL实现 