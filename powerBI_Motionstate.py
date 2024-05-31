# 下面用于创建数据帧并删除重复行的代码始终执行，并用作脚本报头: 

# dataset = pandas.DataFrame(EventTime, JointKey, w, x, y, z)
# dataset = dataset.drop_duplicates()

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = dataset
df = df.tail(50)

def quaternion_to_euler(w, x, y, z):
    """
    Convert quaternion (w, x, y, z) to Euler angles (roll, pitch, yaw)
    """
    t0 = +2.0 * (w * x + y * z)
    t1 = +1.0 - 2.0 * (x * x + y * y)
    roll_x = np.arctan2(t0, t1)

    t2 = +2.0 * (w * y - z * x)
    t2 = np.clip(t2, -1.0, +1.0)
    pitch_y = np.arcsin(t2)

    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (y * y + z * z)
    yaw_z = np.arctan2(t3, t4)

    return roll_x, pitch_y, yaw_z

# Convert quaternion data to Euler angles
df[['roll', 'pitch', 'yaw']] = df.apply(
    lambda row: quaternion_to_euler(row['w'], row['x'], row['y'], row['z']),
    axis=1, result_type='expand'
)

# Calculate the combined motion state as the Euclidean distance from the origin
df['motion_state'] = np.sqrt(df['roll']**2 + df['pitch']**2 + df['yaw']**2)

# Plot combined motion state over time for each joint
plt.figure(figsize=(10, 5))
for joint in df['JointKey'].unique():
    joint_data = df[df['JointKey'] == joint]
    plt.plot(joint_data['EventTime'], joint_data['motion_state'], label=f'Motion State {joint}')

plt.xlabel('Time')
plt.ylabel('Motion State')
plt.legend()
plt.title('Motion State Over Time')
plt.show()