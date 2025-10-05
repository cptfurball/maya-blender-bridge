import maya.api.OpenMaya as om
import mbb_ui

# ---------------------------------------------------------------------------
# Required entry point
# ---------------------------------------------------------------------------
def maya_useNewAPI():
    pass

# ---------------------------------------------------------------------------
# Called when Maya loads the plugin.
# ---------------------------------------------------------------------------
def initializePlugin(plugin):
    plugin_fn = om.MFnPlugin(plugin, "Edward Lim Yee Siang", "1.2", "Any")
    om.MGlobal.displayInfo("[MBB Plugin] Loaded successfully.")
    mbb_ui.show()

# ---------------------------------------------------------------------------
# Called when Maya unloads the plugin.
# ---------------------------------------------------------------------------
def uninitializePlugin(plugin):
    plugin_fn = om.MFnPlugin(plugin)
    om.MGlobal.displayInfo("[MBB Plugin] Unloaded successfully.")
