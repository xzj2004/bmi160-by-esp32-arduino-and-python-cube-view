import numpy as np
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import serial
import math
import time
from collections import deque
import os

# 轨迹历史数据，保存最近的位置点
MAX_TRAIL_LENGTH = 1000
position_history = deque(maxlen=MAX_TRAIL_LENGTH)

# 初始位置
position = [0.0, 0.0, 0.0]
velocity = [0.0, 0.0, 0.0]

# 设置中文字体路径
def get_font():
    # 尝试加载系统中文字体
    if os.path.exists('C:/Windows/Fonts/simhei.ttf'):
        return pygame.font.Font('C:/Windows/Fonts/simhei.ttf', 24)
    elif os.path.exists('C:/Windows/Fonts/msyh.ttc'):
        return pygame.font.Font('C:/Windows/Fonts/msyh.ttc', 24)
    else:
        # 如果找不到中文字体，使用默认字体
        return pygame.font.Font(None, 24)

# 坐标系绘制
def draw_axes():
    glLineWidth(3.0)
    glBegin(GL_LINES)
    # X轴 红色
    glColor3f(1.0, 0.0, 0.0)
    glVertex3f(-10.0, 0.0, 0.0)
    glVertex3f(10.0, 0.0, 0.0)
    # Y轴 绿色
    glColor3f(0.0, 1.0, 0.0)
    glVertex3f(0.0, -10.0, 0.0)
    glVertex3f(0.0, 10.0, 0.0)
    # Z轴 蓝色
    glColor3f(0.0, 0.0, 1.0)
    glVertex3f(0.0, 0.0, -10.0)
    glVertex3f(0.0, 0.0, 10.0)
    glEnd()
    glLineWidth(1.0)

# 绘制网格
def draw_grid():
    glLineWidth(1.0)
    glBegin(GL_LINES)
    glColor3f(0.3, 0.3, 0.3)
    
    # 绘制地面网格
    grid_size = 10
    grid_step = 1.0
    
    for i in range(-grid_size, grid_size + 1):
        # X方向线
        glVertex3f(i * grid_step, 0.0, -grid_size * grid_step)
        glVertex3f(i * grid_step, 0.0, grid_size * grid_step)
        # Z方向线
        glVertex3f(-grid_size * grid_step, 0.0, i * grid_step)
        glVertex3f(grid_size * grid_step, 0.0, i * grid_step)
    
    glEnd()
    glLineWidth(1.0)

# 绘制当前位置的球体
def draw_position_sphere():
    # 禁用深度测试，确保球体始终可见
    glDisable(GL_DEPTH_TEST)
    
    glPushMatrix()
    glTranslatef(position[0], position[1], position[2])
    
    # 使用更明亮的颜色
    glColor4f(1.0, 0.5, 0.0, 0.8)  # 亮橙色
    
    # 增大球体尺寸
    quad = gluNewQuadric()
    gluSphere(quad, 0.5, 16, 16)  # 球体半径从0.2增加到0.5
    gluDeleteQuadric(quad)
    
    # 绘制三个轴向线，显示当前朝向
    glLineWidth(2.0)
    glBegin(GL_LINES)
    # X轴 红色
    glColor3f(1.0, 0.0, 0.0)
    glVertex3f(0, 0, 0)
    glVertex3f(1.0, 0, 0)
    # Y轴 绿色
    glColor3f(0.0, 1.0, 0.0)
    glVertex3f(0, 0, 0)
    glVertex3f(0, 1.0, 0)
    # Z轴 蓝色
    glColor3f(0.0, 0.0, 1.0)
    glVertex3f(0, 0, 0)
    glVertex3f(0, 0, 1.0)
    glEnd()
    glLineWidth(1.0)
    
    glPopMatrix()
    
    # 重新启用深度测试
    glEnable(GL_DEPTH_TEST)

# 绘制移动轨迹
def draw_trail():
    if len(position_history) < 2:
        return
    
    # 禁用深度测试，确保轨迹始终可见
    glDisable(GL_DEPTH_TEST)    
    glLineWidth(3.0)  # 增加线宽
    glBegin(GL_LINE_STRIP)
    
    # 使用更亮的渐变色显示轨迹
    for i, pos in enumerate(position_history):
        # 根据点的新旧程度设置颜色
        alpha = i / len(position_history)
        glColor3f(1.0, alpha, 0.0)  # 从红色到黄色的渐变
        glVertex3f(pos[0], pos[1], pos[2])
    
    glEnd()
    glLineWidth(1.0)
    
    # 重新启用深度测试
    glEnable(GL_DEPTH_TEST)

def main():
    global position, velocity
    
    # 调试信息
    print("程序启动，准备初始化...")
    
    # 初始化图形
    pygame.init()
    display = (1024, 768)
    screen = pygame.display.set_mode(display, DOUBLEBUF|OPENGL)
    pygame.display.set_caption('BMI160 空间位移跟踪')
    
    print("pygame窗口已创建")
    
    # 设置视角
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, (display[0]/display[1]), 0.1, 50.0)
    glMatrixMode(GL_MODELVIEW)
    
    # 设置初始视图位置
    glLoadIdentity()
    glTranslatef(0.0, 0.0, -15.0)
    
    print("OpenGL视角已设置")
    
    # 启用深度测试和透明
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # 设置光照，使物体更容易看见
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    light_position = [10.0, 10.0, 10.0, 1.0]
    glLightfv(GL_LIGHT0, GL_POSITION, light_position)
    
    # 绘制一个测试场景确认OpenGL工作正常
    glClearColor(0.1, 0.1, 0.2, 1)
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glTranslatef(0.0, 0.0, -15.0)
    draw_axes()
    draw_grid()
    pygame.display.flip()
    print("测试场景已渲染，检查窗口是否显示坐标轴和网格")
    
    print("OpenGL初始化完成")
    
    # 设置串口通信
    try:
        # 尝试多个COM端口
        ports_to_try = ['COM3', 'COM4', 'COM5', 'COM6', 'COM7']
        ser = None
        
        for port in ports_to_try:
            try:
                ser = serial.Serial(port, 115200, timeout=1)
                print(f"串口连接成功：{port}")
                break
            except:
                print(f"尝试连接端口 {port} 失败")
        
        if ser is None:
            raise Exception("所有COM端口连接失败")
    except Exception as e:
        print(f"串口连接失败: {str(e)}")
        # 启用演示模式，不使用真实传感器数据
        ser = None
        print("启用演示模式，使用模拟数据")

    # 等待Arduino初始化
    print("等待Arduino初始化...")
    data_started = False
    
    # 设置超时
    start_wait_time = time.time()
    max_wait_time = 10  # 最多等待10秒
    
    while not data_started:
        # 检查是否超时
        if time.time() - start_wait_time > max_wait_time:
            print("等待Arduino初始化超时，跳过等待DATA_BEGIN标记")
            data_started = True
            break
        
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
    
    # 相机控制参数
    camera_distance = 20.0  # 增加相机距离，扩大视野
    camera_yaw = 0
    camera_pitch = 30
    clock = pygame.time.Clock()
    
    # 是否自动重置轨迹
    auto_reset = True
    last_reset_time = time.time()
    
    # 键盘控制位置重置的变量
    reset_key_pressed = False
    reset_ball_position = False
    
    # 键盘控制缩放因子的变量
    current_scale_factor = 2.0  # 默认缩放因子
    
    # 上一次时间戳，用于计算时间间隔
    last_time = time.time()
    
    # 重力补偿，假设开始时传感器处于静止状态
    gravity_offset = [0, 0, 0]
    gravity_samples = []
    calibration_count = 0
    is_calibrating = True
    
    # 模拟演示模式的变量
    demo_mode = ser is None
    demo_angle = 0
    
    # 主循环
    while True:
        current_time = time.time()
        dt = min(current_time - last_time, 0.1)  # 限制最大时间步长为0.1秒
        last_time = current_time
        
        # 处理键盘和鼠标事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                ser.close()
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # 手动重置轨迹
                    position = [0.0, 0.0, 0.0]
                    velocity = [0.0, 0.0, 0.0]
                    position_history.clear()
                    reset_ball_position = True
                    reset_key_pressed = True
                elif event.key == pygame.K_a:  # 切换自动重置
                    auto_reset = not auto_reset
                    print(f"自动重置: {'开启' if auto_reset else '关闭'}")
                elif event.key == pygame.K_c:  # 重新校准
                    is_calibrating = True
                    calibration_count = 0
                    gravity_samples = []
                    print("开始重新校准...")
                elif event.key == pygame.K_UP:  # 增加敏感度
                    current_scale_factor *= 1.2
                    print(f"增加敏感度，当前比例: {current_scale_factor:.2f}")
                elif event.key == pygame.K_DOWN:  # 降低敏感度
                    current_scale_factor /= 1.2
                    print(f"降低敏感度，当前比例: {current_scale_factor:.2f}")
                elif event.key == pygame.K_ESCAPE:  # 退出
                    pygame.quit()
                    if ser: ser.close()
                    return
            
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_r:
                    reset_key_pressed = False
            
            # 鼠标拖动旋转相机
            elif event.type == pygame.MOUSEMOTION:
                if pygame.mouse.get_pressed()[0]:  # 左键按下拖动
                    dx, dy = event.rel
                    camera_yaw += dx * 0.5
                    camera_pitch -= dy * 0.5
                    camera_pitch = max(-89, min(89, camera_pitch))
            
            # 鼠标滚轮调整相机距离
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # 滚轮上滚
                    camera_distance = max(5, camera_distance - 1)
                elif event.button == 5:  # 滚轮下滚
                    camera_distance = min(30, camera_distance + 1)

        # 如果R键被按住，持续重置球的位置
        if reset_key_pressed:
            position = [0.0, 0.0, 0.0]
            reset_ball_position = True
        
        # 自动重置轨迹（每30秒）
        if auto_reset and time.time() - last_reset_time > 30:
            position = [0.0, 0.0, 0.0]
            velocity = [0.0, 0.0, 0.0]
            position_history.clear()
            last_reset_time = time.time()
        
        # 读取串口数据或使用演示数据
        data_processed = False
        
        if demo_mode:
            # 演示模式：生成模拟数据
            demo_angle += 3  # 加快旋转速度
            ax = 0.3 * math.sin(math.radians(demo_angle))  # 增大幅度
            ay = 0.3 * math.cos(math.radians(demo_angle))
            az = 0.98  # 模拟重力
            gx = gy = gz = 0
            
            # 加入随机震动，更剧烈
            if pygame.time.get_ticks() % 2000 < 200:  # 每2秒震动0.2秒
                ax += (np.random.random() - 0.5) * 0.8
                ay += (np.random.random() - 0.5) * 0.8
            
            if is_calibrating:
                gravity_samples.append([ax, ay, az])
                calibration_count += 1
                
                if calibration_count >= 30:  # 演示模式下只收集30个样本
                    gravity_offset = np.mean(gravity_samples, axis=0)
                    is_calibrating = False
                    print(f"演示模式校准完成，重力偏移: {gravity_offset}")
                    position = [0.0, 0.0, 0.0]
                    velocity = [0.0, 0.0, 0.0]
                    position_history.clear()
            else:
                # 补偿重力
                ax -= gravity_offset[0]
                ay -= gravity_offset[1]
                az -= gravity_offset[2]
                
                # 设置一个死区，忽略极小的加速度变化
                dead_zone = 0.001  # 大幅降低死区，几乎立即响应任何移动
                if abs(ax) < dead_zone: ax = 0
                if abs(ay) < dead_zone: ay = 0
                if abs(az) < dead_zone: az = 0
                
                # 应用加速度积分获得速度（演示模式下更敏感）
                scale_factor = current_scale_factor  # 使用当前缩放因子
                
                # 调整坐标映射，BMI160的坐标系可能与OpenGL不同
                # 进行坐标系转换: BMI160 -> OpenGL
                ax_mapped = -ax  # 翻转X轴
                ay_mapped = az   # BMI160的Z轴映射到OpenGL的Y轴
                az_mapped = ay   # BMI160的Y轴映射到OpenGL的Z轴
                
                # 直接影响速度，但使用较小的缩放因子
                velocity[0] = ax_mapped * scale_factor
                velocity[1] = ay_mapped * scale_factor
                velocity[2] = az_mapped * scale_factor
                
                # 限制最大速度，防止飞出视野
                max_velocity = 5.0
                velocity[0] = max(min(velocity[0], max_velocity), -max_velocity)
                velocity[1] = max(min(velocity[1], max_velocity), -max_velocity)
                velocity[2] = max(min(velocity[2], max_velocity), -max_velocity)
                
                # 应用阻尼，略微增大阻尼以增加控制性
                damping = 0.95
                velocity[0] *= damping
                velocity[1] *= damping
                velocity[2] *= damping
                
                # 应用速度积分获得位置
                position[0] += velocity[0] * dt
                position[1] += velocity[1] * dt
                position[2] += velocity[2] * dt
                
                # 限制最大位置范围，防止飞出视野
                max_position = 10.0
                position[0] = max(min(position[0], max_position), -max_position)
                position[1] = max(min(position[1], max_position), -max_position)
                position[2] = max(min(position[2], max_position), -max_position)
                
                # 打印加速度和位置，用于调试
                if pygame.time.get_ticks() % 1000 < 16:  # 每秒打印一次
                    print(f"原始加速度: ({ax:.3f}, {ay:.3f}, {az:.3f})")
                    print(f"映射加速度: ({ax_mapped:.3f}, {ay_mapped:.3f}, {az_mapped:.3f})")
                    print(f"当前速度: ({velocity[0]:.3f}, {velocity[1]:.3f}, {velocity[2]:.3f})")
                    print(f"当前位置: ({position[0]:.3f}, {position[1]:.3f}, {position[2]:.3f})")
                
                # 只在移动时才记录位置历史，并且降低记录频率，避免轨迹过密
                if (abs(velocity[0]) > 0.01 or abs(velocity[1]) > 0.01 or abs(velocity[2]) > 0.01) and pygame.time.get_ticks() % 2 == 0:
                    position_history.append(position.copy())
            
            data_processed = True
        
        elif ser and ser.in_waiting:  # 有串口且有数据
            try:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                
                # 忽略非数据行
                if ',' not in line:
                    continue
                    
                data = [float(x) for x in line.split(',')]
                if len(data) == 6:
                    ax, ay, az, gx, gy, gz = data
                    
                    # 校准阶段：收集初始重力样本
                    if is_calibrating:
                        gravity_samples.append([ax, ay, az])
                        calibration_count += 1
                        
                        # 在校准过程中绘制当前收集的样本数量
                        glClearColor(0.1, 0.1, 0.2, 1)
                        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
                        glLoadIdentity()
                        gluLookAt(cx, cy, cz, 0, 0, 0, 0, 1, 0)
                        draw_grid()
                        draw_axes()
                        
                        # 在屏幕上显示校准进度
                        font = get_font()
                        progress_text = f"校准中... {calibration_count}/100"
                        textSurface = font.render(progress_text, True, (255, 255, 255))
                        textData = pygame.image.tostring(textSurface, "RGBA", True)
                        glWindowPos2d(display[0]//2 - 100, display[1]//2)
                        glDrawPixels(textSurface.get_width(), textSurface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, textData)
                        
                        pygame.display.flip()
                        
                        if calibration_count >= 100:  # 收集100个样本
                            # 计算平均重力偏移
                            gravity_offset = np.mean(gravity_samples, axis=0)
                            is_calibrating = False
                            print(f"校准完成，重力偏移: {gravity_offset}")
                            position = [0.0, 0.0, 0.0]
                            velocity = [0.0, 0.0, 0.0]
                            position_history.clear()
                            
                            # 显示校准完成信息
                            font = get_font()
                            complete_text = f"校准完成! 重力偏移: {gravity_offset[0]:.4f}, {gravity_offset[1]:.4f}, {gravity_offset[2]:.4f}"
                            textSurface = font.render(complete_text, True, (0, 255, 0))
                            textData = pygame.image.tostring(textSurface, "RGBA", True)
                            glWindowPos2d(display[0]//2 - 200, display[1]//2)
                            glDrawPixels(textSurface.get_width(), textSurface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, textData)
                            
                            pygame.display.flip()
                            time.sleep(2)  # 显示2秒校准结果
                        continue
                    
                    # 补偿重力
                    ax -= gravity_offset[0]
                    ay -= gravity_offset[1]
                    az -= gravity_offset[2]
                    
                    # 设置一个死区，忽略极小的加速度变化
                    dead_zone = 0.001  # 大幅降低死区，几乎立即响应任何移动
                    if abs(ax) < dead_zone: ax = 0
                    if abs(ay) < dead_zone: ay = 0
                    if abs(az) < dead_zone: az = 0
                    
                    # 应用加速度积分获得速度
                    scale_factor = current_scale_factor  # 使用当前缩放因子
                    
                    # 调整坐标映射，BMI160的坐标系可能与OpenGL不同
                    # 进行坐标系转换: BMI160 -> OpenGL
                    ax_mapped = -ax  # 翻转X轴
                    ay_mapped = az   # BMI160的Z轴映射到OpenGL的Y轴
                    az_mapped = ay   # BMI160的Y轴映射到OpenGL的Z轴
                    
                    # 直接影响速度
                    velocity[0] = ax_mapped * scale_factor
                    velocity[1] = ay_mapped * scale_factor
                    velocity[2] = az_mapped * scale_factor
                    
                    # 限制最大速度，防止飞出视野
                    max_velocity = 5.0
                    velocity[0] = max(min(velocity[0], max_velocity), -max_velocity)
                    velocity[1] = max(min(velocity[1], max_velocity), -max_velocity)
                    velocity[2] = max(min(velocity[2], max_velocity), -max_velocity)
                    
                    # 应用阻尼，略微增大阻尼以增加控制性
                    damping = 0.95
                    velocity[0] *= damping
                    velocity[1] *= damping
                    velocity[2] *= damping
                    
                    # 应用速度积分获得位置
                    position[0] += velocity[0] * dt
                    position[1] += velocity[1] * dt
                    position[2] += velocity[2] * dt
                    
                    # 限制最大位置范围，防止飞出视野
                    max_position = 10.0
                    position[0] = max(min(position[0], max_position), -max_position)
                    position[1] = max(min(position[1], max_position), -max_position)
                    position[2] = max(min(position[2], max_position), -max_position)
                    
                    # 打印加速度和位置，用于调试
                    if pygame.time.get_ticks() % 1000 < 16:  # 每秒打印一次
                        print(f"原始加速度: ({ax:.3f}, {ay:.3f}, {az:.3f})")
                        print(f"映射加速度: ({ax_mapped:.3f}, {ay_mapped:.3f}, {az_mapped:.3f})")
                        print(f"当前速度: ({velocity[0]:.3f}, {velocity[1]:.3f}, {velocity[2]:.3f})")
                        print(f"当前位置: ({position[0]:.3f}, {position[1]:.3f}, {position[2]:.3f})")
                    
                    # 只在移动时才记录位置历史，并且降低记录频率，避免轨迹过密
                    if (abs(velocity[0]) > 0.01 or abs(velocity[1]) > 0.01 or abs(velocity[2]) > 0.01) and pygame.time.get_ticks() % 2 == 0:
                        position_history.append(position.copy())
                    
                    data_processed = True
                    
            except Exception as e:
                print(f"数据处理错误: {str(e)}")
                continue

        # 清除缓冲区并设置背景色
        glClearColor(0.1, 0.1, 0.2, 1)  # 稍微亮一点的背景
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        
        # 重置视图
        glLoadIdentity()
        
        # 根据球形坐标系计算相机位置
        cx = camera_distance * math.cos(math.radians(camera_pitch)) * math.sin(math.radians(camera_yaw))
        cy = camera_distance * math.sin(math.radians(camera_pitch))
        cz = camera_distance * math.cos(math.radians(camera_pitch)) * math.cos(math.radians(camera_yaw))
        
        # 设置相机位置和朝向
        gluLookAt(cx, cy, cz, 0, 0, 0, 0, 1, 0)
        
        # 每100帧打印一次坐标确认渲染位置
        if pygame.time.get_ticks() % 3000 < 16:  # 每3秒打印一次
            print(f"渲染位置: {position}, 相机位置: ({cx:.1f}, {cy:.1f}, {cz:.1f})")
        
        # 绘制场景
        draw_grid()
        draw_axes()
        draw_trail()
        draw_position_sphere()
        
        # 在屏幕上显示当前位置文本
        def draw_text(text, position, color=(255, 255, 255)):
            font = get_font()
            textSurface = font.render(text, True, color)
            textData = pygame.image.tostring(textSurface, "RGBA", True)
            glWindowPos2d(position[0], position[1])
            glDrawPixels(textSurface.get_width(), textSurface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, textData)
        
        # 显示状态信息
        status_text = []
        status_text.append(f"位置: X={position[0]:.2f} Y={position[1]:.2f} Z={position[2]:.2f}")
        status_text.append(f"速度: X={velocity[0]:.2f} Y={velocity[1]:.2f} Z={velocity[2]:.2f}")
        status_text.append(f"敏感度: {current_scale_factor:.2f}")
        status_text.append(f"自动重置: {'开启' if auto_reset else '关闭'}")
        status_text.append(f"{'校准中...' if is_calibrating else '运行中'}")
        status_text.append("按键: R-重置轨迹 A-切换自动重置 C-重新校准")
        status_text.append("上/下箭头-调整敏感度 ESC-退出")
        
        for i, text in enumerate(status_text):
            draw_text(text, (10, display[1] - 30 * (i + 1)))
        
        # 刷新显示
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main() 