import serial
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
import itertools

# 初始化串口
ser = serial.Serial('COM3', 115200, timeout=1)

# 创建图形和三维子图
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# 设置坐标轴
ax.set_xlim([-10, 10])
ax.set_ylim([-10, 10])
ax.set_zlim([-10, 10])
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')

# 初始化图形
line, = ax.plot([], [], [], 'b-', label='Trajectory', lw=2)
point, = ax.plot([], [], [], 'ro')

# 存储轨迹的列表
trajectory_x, trajectory_y, trajectory_z = [], [], []

# 卡尔曼滤波器的初始设置
dt = 0.05  # 时间步长
# 初始估计误差矩阵
P = np.eye(3)
# 外部噪声协方差矩阵
Q = np.eye(3) * 0.01
# 测量噪声协方差矩阵
R = np.eye(3) * 0.02
# 初始位置和速度
position = np.zeros(3)
velocity = np.zeros(3)
X_est = np.zeros((3, 1))  # 状态估计
# 静止阈值和衰减因子
still_threshold = 0.05
decay_factor = 0.95  # 每帧速度和位置衰减的比例
# 静止状态加速度零偏
accel_bias = np.zeros((3, 1))

def kalman_filter(X_est, P, Z_meas, use_filter=True):
    if not use_filter:
        return Z_meas, P
    # 预测步骤
    X_pred = X_est
    P_pred = P + Q
    
    # 更新步骤
    K = P_pred @ np.linalg.inv(P_pred + R)  # 卡尔曼增益
    X_est = X_pred + K @ (Z_meas - X_pred)
    P = (np.eye(3) - K) @ P_pred
    
    return X_est, P

def update(frame):
    global X_est, P, velocity, position, trajectory_x, trajectory_y, trajectory_z
    if ser.inWaiting() > 0:
        data = ser.readline().decode('utf-8').strip()
        try:
            # 解析加速度、陀螺仪和磁力计数据
            ax_, ay_, az_, gx_, gy_, gz_, mx_, my_, mz_ = map(float, data.split())
            accel_measured = np.array([[ax_], [ay_], [az_]])
            
            # 减去估计的零偏
            accel_corrected = accel_measured - accel_bias

            # 使用卡尔曼滤波处理加速度数据
            X_est, P = kalman_filter(X_est, P, accel_corrected, np.linalg.norm(accel_corrected) > still_threshold)
            
            # 更新位置和速度
            if np.linalg.norm(accel_corrected) > still_threshold:
                velocity += X_est.ravel() * dt
                position += velocity * dt
            else:
                # 应用衰减因子
                velocity *= decay_factor
                position *= decay_factor
            
            trajectory_x.append(position[0])
            trajectory_y.append(position[1])
            trajectory_z.append(position[2])
            
            # 更新数据点
            line.set_data(trajectory_x, trajectory_y)
            line.set_3d_properties(trajectory_z)
            
            point.set_data([position[0]], [position[1]])
            point.set_3d_properties([position[2]])

        except ValueError:
            print("Error parsing data:", data)

    return line, point,

# 创建动画, 禁用缓存
ani = FuncAnimation(fig, update, frames=itertools.count(), blit=False, interval=50, cache_frame_data=False)

plt.show()
