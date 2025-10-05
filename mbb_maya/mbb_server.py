# mbb_server.py
# ---------------------------------------------------------------------------
# Maya <-> Blender Bridge
# ---------------------------------------------------------------------------

import socket
import threading
import traceback
import maya.utils
import maya.cmds as cmds
import maya.mel as mel
from pathlib import Path

_server = None
_running = False

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def log(msg):
    print(f"[MBB] {msg}")


# ---------------------------------------------------------------------------
# Import maya file as reference | Deprecated
# ---------------------------------------------------------------------------
"""
def import_reference(path):
    try:
        if not path.lower().endswith((".ma", ".mb")):
            return f"Unsupported file type: {path}"

        cmds.file(path, reference=True, ignoreVersion=True, mergeNamespacesOnClash=False, namespace="ref_%s" % path.split("/")[-1].split(".")[0])
        return f"Imported"

    except Exception as e:
        traceback.print_exc()
        return f"Failed to import: {e}"
"""


# ---------------------------------------------------------------------------
# Import fbx file
# ---------------------------------------------------------------------------
def import_fbx(path):
    try:
        # Import FBX
        cmds.file(path, i=True, type="FBX", ignoreVersion=True, ra=True)
        return f"IMPORT_SUCCESS"
    except Exception as e:
        traceback.print_exc()
        return f"IMPORT_FAILED: {e}"

# ---------------------------------------------------------------------------
# Export fbx file
# ---------------------------------------------------------------------------
def export_fbx(path):
    try:
        # Load FBX plugin if needed
        if not cmds.pluginInfo('fbxmaya', query=True, loaded=True):
            cmds.loadPlugin('fbxmaya')
            print("FBX plugin loaded successfully.")

        # We are using MEL eval to suppress the export dialog which is important
        # so that Maya can successfully export the FBX before Blender starts the 
        # import process.
        mel.eval('FBXResetExport')
        mel.eval('FBXExportInAscii -v false')
        mel.eval('FBXExportSmoothingGroups -v true')
        mel.eval('FBXExportTangents -v true')
        mel.eval('FBXExportSkins -v true')
        mel.eval('FBXExportShapes -v true')
        mel.eval('FBXExportConstraints -v false')
        mel.eval('FBXExportCameras -v false')
        mel.eval('FBXExportLights -v false')
        mel.eval('FBXExportEmbeddedTextures -v false')
        mel.eval('FBXExportFileVersion -v "FBX202000"')
        mel.eval("FBXExportShowUI -v false")

        # Using path convert because regular path.replace() gives shitty result.
        pathconvert = Path(path)
        escaped_path = pathconvert.as_posix()
        mel.eval(f'FBXExport -f "{escaped_path}" -s')

        # This line is deprecated but let's keep it here for future reference.
        # This method causes FBX export dialog to pop up. Not the desired outcome.
        # cmds.file(path, force=True, options="v=0;", type="FBX", pr=True, es=True)

        return f"EXPORT_SUCCESS: {path}"

    except Exception as e:
        traceback.print_exc()
        return f"Failed to import: {e}"


# ---------------------------------------------------------------------------
# Client handler
# ---------------------------------------------------------------------------
def handle_client(conn, addr):
    log(f"Connection from {addr}")
    with conn:
        while _running:
            try:
                # Read the data sent from the connection.
                data = conn.recv(1024)
                if not data:
                    break

                # Decode it with utf8.
                msg = data.decode("utf-8").strip()
                log(f"Received: {msg}")

                # Process the response.
                response = process_message(msg)

                # Return response to all the connection.
                # TODO: Identify which connection to reply to. Otherwise all the 
                # blender instances will get this response.
                conn.sendall((response + "\n").encode("utf-8"))

            except Exception as e:
                log(f"Error: {e}")
                try:
                    # TODO: Identify which connection to reply to. Otherwise all the 
                    # blender instances will get this response.
                    conn.sendall(f"Error: {e}\n".encode("utf-8"))
                except Exception:
                    pass
                break
    
    log(f"Client {addr} disconnected")


# ---------------------------------------------------------------------------
# Command dispatcher: Based on the command given by client, this server will
# perform different tasks.
# ---------------------------------------------------------------------------
def process_message(msg):
    log(f"processing message!")

    # Format of the command should always be {CMD} {arg1} {arg2}.
    # This format is case insensitive.
    parts = msg.strip().split(" ", 1)
    cmd = parts[0].lower()

    # Gets only the first argument.
    # TODO: In future may need support for more than one arguments.
    arg = parts[1].strip() if len(parts) > 1 else ""

    # Simple reply message to test connection.
    if cmd == "ping":
        return "pong"
    
    # Imports FBX into current Maya scene.
    elif cmd == "import_fbx":
        # Must run in Maya's main thread
        def _do_import():
            result = import_fbx(arg)
            log(result)
            return result

        future = maya.utils.executeInMainThreadWithResult(_do_import)
        return future
    
    # Exports current selected meshes as FBX.
    elif cmd == "export_selected":
        # Must run in Maya's main thread
        def _do_export():
            result = export_fbx(arg)
            log(result)
            return result

        future = maya.utils.executeInMainThreadWithResult(_do_export)
        return future

    # This is deprecated. Keeping it here for future reference.
    """
    elif cmd == "import_ref":
        # Must run in Maya's main thread
        def _do_import():
            result = import_reference(arg)
            log(result)
            return result

        future = maya.utils.executeInMainThreadWithResult(_do_import)
        return future
    """

    return f"UNKNOWN_COMMAND: {cmd}"


# ---------------------------------------------------------------------------
# Starts a socket connection for communication between external software with Maya
# ---------------------------------------------------------------------------
def start_server(host="0.0.0.0", port=50008):
    global _server, _running

    # If it is running, skip this process.
    if _running:
        log("Already running.")
        return

    # Sets the required properties for server to start.
    _running = True
    _server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    _server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    _server.bind((host, port))
    _server.listen(1)

    log(f"Listening on {host}:{port}")

    # Not sure what these does, took it from stackoverflow.
    def accept_loop():
        while _running:
            try:
                conn, addr = _server.accept()
                threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
            except OSError:
                break

    threading.Thread(target=accept_loop, daemon=True).start()


# ---------------------------------------------------------------------------
# Stops the socket connection.
# ---------------------------------------------------------------------------
def stop_server():
    global _server, _running
    if not _running:
        log("Not running.")
        return
    _running = False
    if _server:
        try:
            _server.close()
        except Exception:
            pass
        _server = None
        
    log("Stopped.")
