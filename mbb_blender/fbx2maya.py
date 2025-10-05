import sys
import os
import maya.standalone
import maya.cmds as cmds

# How to run this in command line?
# "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" "C:\Users\_\Desktop\mbb\fbx2maya.py" C:\Users\_\Desktop\mbb\monke.fbx C:\Users\_\Desktop\mbb\temp.ma

# Converts fbx file to maya and store it in a temp file
def convert(input_fbx_file_path, output_fbx_file_path):
    print(f"Starting conversion:\n  Input: {input_fbx_file_path}\n  Output: {output_fbx_file_path}")
    maya.standalone.initialize()

    try:
        # Load FBX plugin if needed
        if not cmds.pluginInfo('fbxmaya', query=True, loaded=True):
            cmds.loadPlugin('fbxmaya')
            print("FBX plugin loaded successfully.")

        # Import FBX
        cmds.file(input_fbx_file_path, i=True, ignoreVersion=True, ra=True, mergeNamespacesOnClash=False, pr=True)

        # Get objects in scene. Assemblies means "List top level transform Dag objects"
        top_nodes = cmds.ls(assemblies=True)
        print(f"Found {len(top_nodes)} top-level nodes.")

        # Loop through the nodes to apply modifications.
        for node in top_nodes:
            try:
                # Reset the transformation.
                print(f"Reset the xform for {node}")
                cmds.xform(node, translation=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1))
            except Exception as e:
                print(f"Skipping {node} due to error: {e}")

        # Save as .ma in the output path
        cmds.file(rename=output_fbx_file_path)
        cmds.file(save=True, type='mayaAscii')

        print(f"Conversion complete and transforms resetted.")

    except Exception as e:
        print(f"Error during conversion:", e)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: mayapy fbx2maya.py <input_fbx_file_path_file_path> <output_fbx_file_path_file_path>")
        sys.exit(1)

    input_fbx_file_path = sys.argv[1] # input file path
    output_fbx_file_path = sys.argv[2] # output file path

    convert(input_fbx_file_path, output_fbx_file_path)