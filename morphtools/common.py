"""Shared helpers for the Blender scripts. Runs inside Blender's bundled Python."""
import argparse
import json
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

R15 = [
    "HumanoidRootPart", "LowerTorso", "UpperTorso", "Head",
    "LeftUpperArm", "LeftLowerArm", "LeftHand", "RightUpperArm", "RightLowerArm", "RightHand",
    "LeftUpperLeg", "LeftLowerLeg", "LeftFoot", "RightUpperLeg", "RightLowerLeg", "RightFoot",
]
MAX_INFLUENCES = 4      # Roblox skinning reads at most 4 bones per vertex
MAX_TRIANGLES = 20000   # Roblox's per-mesh triangle limit for imported meshes
IMPORTERS = {".fbx": "fbx", ".glb": "gltf", ".gltf": "gltf", ".obj": "obj"}


def parse(prog, description, configure):
    """Parse the arguments Blender passes after `--`."""
    parser = argparse.ArgumentParser(prog=prog, description=description)
    configure(parser)
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return parser.parse_args(argv)


def fail(message):
    print(f"ERROR: {message}")
    raise SystemExit(1)


def load(path):
    """Open a .blend, or import FBX/GLB/glTF/OBJ into an empty scene."""
    path = Path(path).resolve()
    if not path.exists():
        fail(f"{path} does not exist")
    if path.suffix.lower() == ".blend":
        bpy.ops.wm.open_mainfile(filepath=str(path))
        return
    kind = IMPORTERS.get(path.suffix.lower())
    if not kind:
        fail(f"unsupported input {path.suffix}; use .blend, .fbx, .glb, .gltf or .obj")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if kind == "gltf":
        bpy.ops.import_scene.gltf(filepath=str(path))
    elif kind == "obj":
        bpy.ops.wm.obj_import(filepath=str(path))
    elif hasattr(bpy.ops.import_scene, "fbx"):
        bpy.ops.import_scene.fbx(filepath=str(path), use_custom_normals=True, automatic_bone_orientation=False)
    else:
        bpy.ops.wm.fbx_import(filepath=str(path))


def save(path, source=None):
    """Save to a new .blend; refuses to overwrite the source file."""
    path = Path(path).resolve()
    if source and path == Path(source).resolve():
        fail("--out must differ from the input so the original is never overwritten")
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(path), copy=False)
    print(f"saved {path}")


def armatures():
    return [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]


def the_armature():
    found = armatures()
    if len(found) != 1:
        fail(f"expected exactly 1 armature, found {len(found)}: {[o.name for o in found]}")
    return found[0]


def meshes():
    return [o for o in bpy.context.scene.objects if o.type == "MESH" and len(o.data.vertices)]


def triangles(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def world_bounds(objects, evaluated=True):
    """World-space bounds of mesh vertices, with armature deformation if evaluated."""
    graph = bpy.context.evaluated_depsgraph_get()
    lo, hi = Vector((1e30,) * 3), Vector((-1e30,) * 3)
    for obj in objects:
        source = obj.evaluated_get(graph) if evaluated else obj
        mesh = source.to_mesh()
        for v in mesh.vertices:
            p = source.matrix_world @ v.co
            lo = Vector(map(min, lo, p))
            hi = Vector(map(max, hi, p))
        source.to_mesh_clear()
    return lo, hi


def rest_pose(armature):
    for bone in armature.pose.bones:
        bone.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()


def select_only(objects, active=None):
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.context.object and bpy.context.object.mode != "OBJECT" else None
    for obj in bpy.context.view_layer.objects:
        obj.select_set(obj in objects)
    bpy.context.view_layer.objects.active = active or (objects[0] if objects else None)


def influences(obj, armature=None):
    """Per-vertex counts of non-zero deform weights; bone groups only when an armature is given."""
    names = {g.index: g.name for g in obj.vertex_groups}
    bones = set(armature.data.bones.keys()) if armature else None
    counts = []
    for v in obj.data.vertices:
        counts.append(sum(1 for g in v.groups if g.weight > 1e-6 and (bones is None or names.get(g.group) in bones)))
    return counts


def write_report(path, data):
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"report: {path}")
