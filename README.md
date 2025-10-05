How to install

Maya:
1. Copy all the scripts into `C:\Users\_\Documents\maya\2024\plug-ins\`. Do not put them into folders or Maya will not detect this.
2. Open up plugin manager and load the plugin.
3. If the MBB menu does not show up, try run this code below in the script.

```
import mbb_ui
mbb_ui.show();
```

Blender:
1. Zip the mbb_blender folder up.
2. Go to Blender preferences > addons > install from disk.
3. Select the zipped plugin.
4. Make sure to set the temp folder correctly. Also check if you have permission to that folder.