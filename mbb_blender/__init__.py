bl_info = {
    "name": "Maya Blender Bridge (MBB)",
    "author": "Edward Lim",
    "version": (1, 5),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar > Maya Tools",
    "description": "Runs a client that connects to Maya socket to automate import/export",
    "category": "Import-Export",
}

import bpy
import os
from datetime import datetime
import socket

HOST = '127.0.0.1'

addon_dir = os.path.dirname(__file__)
# fbx2maya_script_path = os.path.join(addon_dir, "fbx2maya.py")

class MBB_CONFIG(bpy.types.PropertyGroup):
    connection_port: bpy.props.IntProperty(
        name = "Port",
        description = "Insert port number. Preferably from 1024 - 65535. Note that some of the ports might not work if it is being occupied",
        default = 50008
    )

# ------------------------------------------------------------------------
# Addon Preferences (for storing Maya paths)
# ------------------------------------------------------------------------
class MBB_ADDON_PREF(bpy.types.AddonPreferences):
    bl_idname = __name__

    temp_fbx_output_dir: bpy.props.StringProperty(
        name="Temp FBX output dir",
        description="Path to store temp fbx file",
        subtype='DIR_PATH',
        default=r"C:\temp"
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Maya Bridge Settings")
        #layout.prop(self, "mayapy_path")
        layout.prop(self, "temp_fbx_output_dir")
        #layout.prop(self, "temp_maya_output_dir")


# ------------------------------------------------------------------------
# Operator
# ------------------------------------------------------------------------
class PORT_TEST_PROC(bpy.types.Operator):
    bl_idname = "proc.port_test"
    bl_label = "Test the connection to Maya with the specified port"

    def execute(self, context):
        try:
            # Try to send data to Maya. This is to tell Maya to import the FBX file that we 
            # have just exported.
            data = send_to_maya(f"PING", context.scene.mbb_config.connection_port)

            # Log the response from Maya.
            self.report({'INFO'}, f"[MBB Client] Received: {data.decode('utf-8')}")

        except Exception as e:
            self.report({'ERROR'}, f"[MBB Client] Process failed: {e}")
        return {'FINISHED'}

class EXPORT_SELECTION_PROC(bpy.types.Operator):
    bl_idname = "proc.export_selection"
    bl_label = "Send selected meshes to Maya"

    def execute(self, context):
        prefs = bpy.context.preferences.addons[__name__].preferences
        scene = context.scene

        # Construct temp output file name.
        output_file_name = int(datetime.now().timestamp() * 1000)
        temp_fbx_output_file_path = os.path.join(prefs.temp_fbx_output_dir, f"{output_file_name}.fbx")

        # Maya uses centimeter. We should temporarily set our scene to use centimeter (0.01) for the export.
        scene.unit_settings.scale_length = 0.01

        # Get all selected objects.
        selected_objects = bpy.context.selected_objects
        if not selected_objects:
            print("No objects selected for export.")
            return
        
        bpy.ops.export_scene.fbx(
            filepath=temp_fbx_output_file_path,
            use_selection=True,
            global_scale=1.0,
            # 'FBX_SCALE_ALL' + apply_unit_scale=True converts Blender Meters to Maya Centimeters
            apply_unit_scale=True,
            apply_scale_options='FBX_SCALE_ALL', 
            axis_forward='-Z',
            axis_up='Y',
            bake_space_transform=True,
            object_types={'MESH'},
            mesh_smooth_type='OFF',
            add_leaf_bones=False, # Maya doesn't need extra leaf bones
            path_mode='AUTO',
        )

        # Reset unit scale back to meter.
        scene.unit_settings.scale_length = 1.0

        try:
            # Try to send data to Maya. This is to tell Maya to import the FBX file that we 
            # have just exported.
            data = send_to_maya(f"IMPORT_FBX {temp_fbx_output_file_path}", context.scene.mbb_config.connection_port)

            # Log the response from Maya.
            self.report({'INFO'}, f"[MBB Client] Received: {data.decode('utf-8')}")

        except Exception as e:
            self.report({'ERROR'}, f"[MBB Client] Process failed: {e}")
        return {'FINISHED'}

class IMPORT_SELECTION_PROC(bpy.types.Operator):
    bl_idname = "proc.import_selection"
    bl_label = "Import selected Maya mesh to Blender"

    def execute(self, context):
        prefs = bpy.context.preferences.addons[__name__].preferences
        scene = context.scene

        # Construct temp output file name.
        output_file_name = int(datetime.now().timestamp() * 1000)
        temp_fbx_output_file_path = os.path.join(prefs.temp_fbx_output_dir, f"{output_file_name}.fbx")

        # Runs the process scripts.
        try:
            # Provide Maya with the file output path.
            # It is easier if one side of the communication decides this rather than
            # having both side to decide independently and having to sync it.
            data = send_to_maya(f"EXPORT_SELECTED {temp_fbx_output_file_path}", context.scene.mbb_config.connection_port)
            
            # Response from Maya.
            self.report({'INFO'}, f"[MBB Client] Received: {data.decode('utf-8')}")

            # Maya uses centimeter. We should temporarily set our scene to use centimeter (0.01) for the import.
            scene.unit_settings.scale_length = 0.01

            # Import the temp FBX file generated by Maya.
            filepath = temp_fbx_output_file_path.replace("\\", "/")
            bpy.ops.import_scene.fbx(filepath=filepath)

            # Reset unit scale back to meter.
            scene.unit_settings.scale_length = 1.0

            # Get imported objects (the importer auto-selects them).
            imported_objects = bpy.context.selected_objects

            # Reset scale to 1.0 for all imported objects. For some reason it auto scales to 100.
            for obj in imported_objects:
                # obj.scale = (1.0, 1.0, 1.0)
                obj.select_set(True)

        except Exception as e:
            self.report({'ERROR'}, f"Process failed: {e}")
        return {'FINISHED'}

# ------------------------------------------------------------------------
# Creates a Panel in the N tool sidebar.
# ------------------------------------------------------------------------
class MAYA_BRIDGE_PANEL(bpy.types.Panel):
    bl_label = "Maya Bridge"
    bl_idname = "MAYA_BRIDGE_PANEL"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Maya Bridge"

    def draw(self, context):
        layout = self.layout

        layout.prop(context.scene.mbb_config, "connection_port")
        layout.operator("proc.port_test", text="Port Test", icon='ARROW_LEFTRIGHT')
        layout.separator()
        layout.operator("proc.export_selection", text="Export Selection", icon='EXPORT')
        layout.operator("proc.import_selection", text="Import Selection", icon='IMPORT')


# ------------------------------------------------------------------------
# Registration
# ------------------------------------------------------------------------
classes = (
    MBB_CONFIG,
    MBB_ADDON_PREF,
    PORT_TEST_PROC,
    EXPORT_SELECTION_PROC,
    IMPORT_SELECTION_PROC,
    MAYA_BRIDGE_PANEL,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.mbb_config = bpy.props.PointerProperty(type=MBB_CONFIG)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

def send_to_maya(message, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(3.0)  
        s.connect((HOST, port))
        s.sendall(message.encode('utf-8'))
        data = s.recv(4000)
        return data

if __name__ == "__main__":
    register()