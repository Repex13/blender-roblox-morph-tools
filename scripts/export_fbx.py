"""Export the armature and meshes as an FBX using Roblox's recommended Blender settings.

blender --background --python scripts/export_fbx.py -- work/weighted.blend --out export/model.fbx
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bpy  # noqa: E402
from morphtools import common as c  # noqa: E402


def configure(p):
    p.add_argument("input")
    p.add_argument("--out", required=True, help="FBX file to write")


args = c.parse("export_fbx.py", __doc__.splitlines()[0], configure)
c.load(args.input)
arm = c.the_armature()
c.rest_pose(arm)

units = bpy.context.scene.unit_settings
units.system = "METRIC"
units.scale_length = 0.01  # Roblox's Blender setup: 1 Blender unit comes in as 1 stud

out = Path(args.out).resolve()
out.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.fbx(
    filepath=str(out),
    use_selection=False,
    object_types={"ARMATURE", "MESH"},
    apply_unit_scale=True,
    apply_scale_options="FBX_SCALE_ALL",
    use_space_transform=True,
    axis_forward="-Z",
    axis_up="Y",
    use_mesh_modifiers=True,  # Armature modifiers are kept as skinning, not applied
    mesh_smooth_type="FACE",
    add_leaf_bones=False,
    primary_bone_axis="Y",
    secondary_bone_axis="X",
    use_armature_deform_only=False,
    bake_anim=False,
    path_mode="COPY",
    embed_textures=True,
)
print(f"EXPORTED {out} ({out.stat().st_size} bytes)")
