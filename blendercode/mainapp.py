import sys
import os
import json
import logging

import bpy
import numpy as np
import serial

sys.path.append(os.path.join(bpy.path.abspath("//"), "scripts"))

from blenderport import UARTCommunicator

MCU_PORT_RIGHT_ARM = "COM7"
MCU_PORT_LEFT_ARM = "COM9"

#FPS = 30        # use 30 if system performance is poor
FPS = 60


# set up logging
logger = logging.getLogger("BlenderLogger")
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    stream_handler = logging.StreamHandler()
    stream_handler.setStream(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    # stream_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s::%(threadName)s]: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    stream_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s]: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(stream_handler)


# get scene armature object
armature = bpy.data.objects["Armature"]

# get the bones we need
bone_root = armature.pose.bones.get("Root")
bone_right_upper_arm = armature.pose.bones.get("J_Bip_R_UpperArm")
bone_right_lower_arm = armature.pose.bones.get("J_Bip_R_LowerArm")
bone_left_upper_arm = armature.pose.bones.get("J_Bip_L_UpperArm")
bone_left_lower_arm = armature.pose.bones.get("J_Bip_L_LowerArm")

uart_table_right_arm = UARTTable(MCU_PORT_RIGHT_ARM, logging_level=logging.DEBUG)
uart_table_left_arm = UARTTable(MCU_PORT_LEFT_ARM, logging_level=logging.DEBUG)

"""
@param bone: the bone object, obtained from armature.pose.bone["<bone_name>"]
@param rotation: rotation in quaternion (w, x, y, z)
"""
def set_bone_rotation(bone, rotation):
    w, x, y, z = rotation
    bone.rotation_quaternion[0] = w
    bone.rotation_quaternion[1] = x
    bone.rotation_quaternion[2] = y
    bone.rotation_quaternion[3] = z

"""
a piece of math code copied from StackOverflow
https://stackoverflow.com/questions/39000758/how-to-multiply-two-quaternions-by-python-or-numpy

@param q1: in form (w, x, y, z)
@param q0: @see q1
"""
def multiply_quaternions(q1, q0):
    w0, x0, y0, z0 = q0
    w1, x1, y1, z1 = q1
    return np.array([-x1 * x0 - y1 * y0 - z1 * z0 + w1 * w0,
                     x1 * w0 + y1 * z0 - z1 * y0 + w1 * x0,
                     -x1 * z0 + y1 * w0 + z1 * x0 + w1 * y0,
                     x1 * y0 - y1 * x0 + z1 * w0 + w1 * z0], dtype=np.float64)
                     

class ModalTimerOperator(bpy.types.Operator):
    # we need these two fields for Blender
    bl_idname = "wm.modal_timer_operator"
    bl_label = "Modal Timer Operator"
    
    _timer = None
    
    def modal(self, context, event):
        if event.type == "ESC":
            logger.info("BlenderTimer received ESC.")
            return self.cancel(context)
    
        if event.type == "TIMER":
            # this will eval true every Timer delay seconds
            quat_right_upper = uart_table_right_arm.get("/joint/0")
            quat_right_lower = uart_table_right_arm.get("/joint/1")
            quat_left_upper = uart_table_left_arm.get('/joint/2')
            quat_left_lower = uart_table_left_arm.get('/joint/3')
            
            if not quat_right_upper or not quat_right_lower or not quat_left_upper or not quat_left_lower:
                logger.warning("Invalid joint data")
                return {"PASS_THROUGH"}
            
            # convert data to numpy arrays
            quat_right_upper = np.array(quat_right_upper)
            quat_right_lower = np.array(quat_right_lower)
            quat_left_upper = np.array(quat_left_upper)
            quat_left_lower = np.array(quat_left_lower)
                        
            # get inverse transformation of right upper arm
            quat_right_upper_inv = quat_right_upper * np.array([1, -1, -1, -1])
            
            # rotate right lower arm relative to right upper arm
            quat_right_lower_rel = multiply_quaternions(quat_right_upper_inv, quat_right_lower)

            # get inverse transformation of left upper arm
            quat_left_upper_inv = quat_left_upper * np.array([1, -1, -1, -1])
            
            # rotate left lower arm relative to left upper arm
            quat_left_lower_rel = multiply_quaternions(quat_left_upper_inv, quat_left_lower)
            
            # apply transformation
            set_bone_rotation(bone_right_upper_arm, quat_right_upper)
            set_bone_rotation(bone_right_lower_arm, quat_right_lower_rel)

            # if refresh rate is too low, uncomment this line to force Blender to render viewport
#            bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP", iterations=1)
    
        return {"PASS_THROUGH"}

    def execute(self, context):
        # update rate is 0.01 second
        self._timer = context.window_manager.event_timer_add(1./FPS, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}
        
    def cancel(self, context):
        uart_table_right_arm.stop()
        uart_table_left_arm.stop()
        
        # reset joint position
        set_bone_rotation(bone_right_upper_arm, [1, 0, 0, 0])
        set_bone_rotation(bone_right_lower_arm, [1, 0, 0, 0])
        set_bone_rotation(bone_left_upper_arm, [1, 0, 0, 0])
        set_bone_rotation(bone_left_lower_arm, [1, 0, 0, 0])
        context.window_manager.event_timer_remove(self._timer)
        logger.info("BlenderTimer Stopped.")
        return {"CANCELLED"}


if __name__ == "__main__":
    try:
        logger.info("Starting services.")
        bpy.utils.register_class(ModalTimerOperator)
        
        # uart_table.start()
        uart_table_right_arm.startThreaded()
        uart_table_left_arm.startThreaded()
        
        # start Blender timer
        bpy.ops.wm.modal_timer_operator()
        
        logger.info("All started.")
    except KeyboardInterrupt:
        uart_table_right_arm.stop()
        uart_table_left_arm.stop()
        logger.info("Received KeyboardInterrupt, stopped.")
