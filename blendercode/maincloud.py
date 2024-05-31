import sys
import os
import logging
import time
import numpy as np
import bpy

# Ensure the current directory is in the sys.path
sys.path.append(os.path.join(bpy.path.abspath("//"), "scripts"))


from blendercloud import data_table, EventHubReceiver

CONNECTION_STR = "Endpoint=sb://iothub-ns-515final-59809961-b011f7395d.servicebus.windows.net/;SharedAccessKeyName=iothubowner;SharedAccessKey=clhmjirbSGom9Dq/kBXCu5SjBPj/EMlcTAIoTPFpYZ0=;EntityPath=515final"
EVENTHUB_NAME = "515final"
FPS = 60

# Set up logging
logger = logging.getLogger("BPY")
logger.setLevel(logging.INFO)

if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setStream(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s]: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(ch)

# Get scene armature object
armature = bpy.data.objects["Armature"]

# Get the bones we need
bone_root = armature.pose.bones.get("Root")
bone_right_upper_arm = armature.pose.bones.get("J_Bip_R_UpperArm")
bone_right_lower_arm = armature.pose.bones.get("J_Bip_R_LowerArm")

def setBoneRotation(bone, rotation):
    w, x, y, z = rotation
    bone.rotation_quaternion[0] = w
    bone.rotation_quaternion[1] = x
    bone.rotation_quaternion[2] = y
    bone.rotation_quaternion[3] = z

def multiply_quaternions(q1, q0):
    w0, x0, y0, z0 = q0
    w1, x1, y1, z1 = q1
    return np.array([-x1 * x0 - y1 * y0 - z1 * z0 + w1 * w0,
                     x1 * w0 + y1 * z0 - z1 * y0 + w1 * x0,
                     -x1 * z0 + y1 * w0 + z1 * x0 + w1 * y0,
                     x1 * y0 - y1 * x0 + z1 * w0 + w1 * z0], dtype=np.float64)


class ModalTimerOperator(bpy.types.Operator):
    # We need these two fields for Blender
    bl_idname = "wm.modal_timer_operator"
    bl_label = "Modal Timer Operator"
    
    _timer = None
    
    def modal(self, context, event):
        if event.type == "ESC":
            logger.info("BlenderTimer received ESC.")
            return self.cancel(context)
    
        if event.type == "TIMER":
            # This will eval true every Timer delay seconds
            quat_right_upper = data_table.get("/joint/0")
            quat_right_lower = data_table.get("/joint/1")
            
            if not quat_right_upper or not quat_right_lower:
                logger.warning("Invalid joint data")
                return {"PASS_THROUGH"}
            
            # Convert data to numpy arrays
            quat_right_upper = np.array(quat_right_upper)
            quat_right_lower = np.array(quat_right_lower)
            
            # get inverse transformation of right upper arm
            quat_right_upper_inv = quat_right_upper * np.array([1, -1, -1, -1])
            
            # rotate right lower arm relative to right upper arm
            quat_right_lower_rel = multiply_quaternions(quat_right_upper_inv, quat_right_lower)

            # apply transformation
            setBoneRotation(bone_right_upper_arm, quat_right_upper)
            setBoneRotation(bone_right_lower_arm, quat_right_lower_rel)
    
        return {"PASS_THROUGH"}

    def execute(self, context):
        # Update rate is 0.01 second
        self._timer = context.window_manager.event_timer_add(1./FPS, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}
        
    def cancel(self, context):
        eventhub_receiver.stop()
        
        # Reset joint position
        setBoneRotation(bone_right_upper_arm, [1, 0, 0, 0])
        setBoneRotation(bone_right_lower_arm, [1, 0, 0, 0])
        context.window_manager.event_timer_remove(self._timer)
        logger.info("BlenderTimer Stopped.")
        return {"CANCELLED"}


if __name__ == "__main__":
    try:
        logger.info("Starting services.")
        bpy.utils.register_class(ModalTimerOperator)
        
        eventhub_receiver = EventHubReceiver(CONNECTION_STR, EVENTHUB_NAME)
        eventhub_receiver.startThreaded()
        
        # Start Blender timer
        bpy.ops.wm.modal_timer_operator()
        
        logger.info("All started.")
    except KeyboardInterrupt:
        eventhub_receiver.stop()
        logger.info("Received KeyboardInterrupt, stopped.")
