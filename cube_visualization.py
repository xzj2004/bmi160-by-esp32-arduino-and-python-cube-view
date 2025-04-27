import numpy as np
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import serial
import math
import time

# 立方体顶点
vertices = (
    (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, -1),
    (1, -1, 1), (1, 1, 1), (-1, -1, 1), (-1, 1, 1)
)

# 立方体边
edges = (
    (0,1), (0,3), (0,4), (2,1), (2,3), (2,7),
    (6,3), (6,4), (6,7), (5,1), (5,4), (5,7)
)

# 立方体面
surfaces = (
    (0,1,2,3), (3,2,7,6), (6,7,5,4),
    (4,5,1,0), (1,5,7,2), (4,0,3,6)
)

# 颜色（更鲜艳的颜色）
colors = (
    (1,0,0), (0,1,0), (0,0,1),
    (1,1,0), (1,0,1), (0,1,1)
)

def draw_axes():
    glLineWidth(3.0)
    glBegin(GL_LINES)
    # X轴 红色
    glColor3f(1.0, 0.0, 0.0)
    glVertex3f(-2.0, 0.0, 0.0)
    glVertex3f(2.0, 0.0, 0.0)
    # Y轴 绿色
    glColor3f(0.0, 1.0, 0.0)
    glVertex3f(0.0, -2.0, 0.0)
    glVertex3f(0.0, 2.0, 0.0)
    # Z轴 蓝色
    glColor3f(0.0, 0.0, 1.0)
    glVertex3f(0.0, 0.0, -2.0)
    glVertex3f(0.0, 0.0, 2.0)
    glEnd()
    glLineWidth(1.0)

def draw_cube():
    size = 1.0  # 立方体大小
    
    # 启用光照
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glLightfv(GL_LIGHT0, GL_POSITION, (5.0, 5.0, 5.0, 1.0))
    
    # 绘制立方体面
    glBegin(GL_QUADS)
    for i, surface in enumerate(surfaces):
        glColor3fv(colors[i])
        for vertex in surface:
            x, y, z = vertices[vertex]
            glNormal3f(x, y, z)  # 添加法线以改善光照效果
            glVertex3f(x*size, y*size, z*size)
    glEnd()
    
    # 关闭光照
    glDisable(GL_LIGHTING)
    
    # 绘制立方体边框
    glLineWidth(2.0)
    glBegin(GL_LINES)
    glColor3f(1.0, 1.0, 1.0)
    for edge in edges:
        for vertex in edge:
            x, y, z = vertices[vertex]
            glVertex3f(x*size, y*size, z*size)
    glEnd()
    glLineWidth(1.0)

def main():
    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF|OPENGL)
    pygame.display.set_caption('BMI160 姿态可视化')
    
    # 设置视角
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, (display[0]/display[1]), 0.1, 50.0)
    glMatrixMode(GL_MODELVIEW)
    
    # 启用深度测试和反走样
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LINE_SMOOTH)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    print("OpenGL初始化完成")
    
    # 设置串口通信
    try:
        ser = serial.Serial('COM3', 115200, timeout=1)
        print("串口连接成功")
    except Exception as e:
        print(f"串口连接失败: {str(e)}")
        return

    # 等待Arduino重启并发送开始标记
    print("等待Arduino初始化...")
    data_started = False
    while not data_started:
        try:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                print(f"Arduino输出: {line}")
                if line == "DATA_BEGIN":
                    data_started = True
                    print("数据流开始，准备接收传感器数据")
        except Exception as e:
            print(f"等待过程中出错: {str(e)}")
        pygame.event.pump()  # 保持窗口响应
        time.sleep(0.1)

    # 欧拉角
    roll = pitch = yaw = 0.0
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                ser.close()
                return

        # 读取串口数据
        if ser.in_waiting:
            try:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                
                # 忽略非数据行
                if ',' not in line:
                    continue
                    
                data = [float(x) for x in line.split(',')]
                if len(data) == 6:
                    ax, ay, az, gx, gy, gz = data
                    print(f"接收数据: ax={ax:.2f}, ay={ay:.2f}, az={az:.2f}, gx={gx:.2f}, gy={gy:.2f}, gz={gz:.2f}")
                    
                    # 简单的互补滤波
                    dt = 0.01
                    # 降低角速度的增益，使旋转更接近实际
                    roll += gx * dt * 0.5  # 降低系数到0.5
                    pitch += gy * dt * 0.5
                    yaw += gz * dt * 0.5
                    
                    # 使用加速度计数据修正roll和pitch
                    roll_acc = math.atan2(ay, az) * 180/math.pi
                    pitch_acc = math.atan2(-ax, math.sqrt(ay*ay + az*az)) * 180/math.pi
                    
                    # 互补滤波系数，增加加速度计的权重
                    alpha = 0.8  # 降低从0.96到0.8，增加加速度计的影响
                    roll = alpha * roll + (1-alpha) * roll_acc
                    pitch = alpha * pitch + (1-alpha) * pitch_acc
                    
                    print(f"姿态角: roll={roll:.2f}, pitch={pitch:.2f}, yaw={yaw:.2f}")
            except Exception as e:
                print(f"数据处理错误: {str(e)}")
                continue

        # 清除缓冲区并设置背景色
        glClearColor(0.2, 0.2, 0.2, 1)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        
        # 重置视图
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -5.0)
        
        # 绘制参考坐标轴
        draw_axes()
        
        # 应用旋转
        glRotatef(roll, 1, 0, 0)
        glRotatef(pitch, 0, 1, 0)
        glRotatef(yaw, 0, 0, 1)
        
        # 绘制立方体
        draw_cube()
        
        # 刷新显示
        pygame.display.flip()
        pygame.time.wait(10)

if __name__ == "__main__":
    main() 