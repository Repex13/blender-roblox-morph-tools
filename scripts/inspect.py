"""Audit a model before converting it: rig, meshes, weights, materials and size.

blender --background --python scripts/inspect.py -- model.fbx [--report inspect.json]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bpy  # noqa: E402
from morphtools import common as c, rigmaps  # noqa: E402


def configure(p):
    p.add_argument("input", help=".blend, .fbx, .glb, .gltf or .obj")
    p.add_argument("--report", help="write the findings as JSON")


args = c.parse("inspect.py", __doc__.splitlines()[0], configure)
c.load(args.input)
arms, objs = c.armatures(), c.meshes()
arm = arms[0] if len(arms) == 1 else None
report = {"input": args.input, "armatures": [], "meshes": [], "materials": [], "warnings": []}

for a in arms:
    names = list(a.data.bones.keys())
    report["armatures"].append({"name": a.name, "bones": len(names), "preset": rigmaps.detect(names),
                                "r15_present": [b for b in c.R15 if b in names], "first_bones": names[:12]})
if len(arms) != 1:
    report["warnings"].append(f"{len(arms)} armatures; the converter needs exactly 1")

for obj in objs:
    counts = c.influences(obj, arm)
    entry = {"name": obj.name, "vertices": len(obj.data.vertices), "triangles": c.triangles(obj),
             "max_influences": max(counts, default=0), "unweighted": sum(1 for n in counts if n == 0),
             "materials": [s.material.name for s in obj.material_slots if s.material]}
    report["meshes"].append(entry)
    if entry["triangles"] > c.MAX_TRIANGLES:
        report["warnings"].append(f"{obj.name}: {entry['triangles']} triangles, over Roblox's {c.MAX_TRIANGLES} per mesh")
    if entry["max_influences"] > c.MAX_INFLUENCES:
        report["warnings"].append(f"{obj.name}: up to {entry['max_influences']} bone influences; run weights.py")
    if arm and entry["unweighted"]:
        report["warnings"].append(f"{obj.name}: {entry['unweighted']} vertices have no bone weight")

for mat in bpy.data.materials:
    nodes = mat.node_tree.nodes if mat.use_nodes and mat.node_tree else []
    images = [n.image for n in nodes if n.type == "TEX_IMAGE" and n.image]
    report["materials"].append({"name": mat.name, "textures": [i.name for i in images],
                                "alpha_channel": any(i.channels == 4 for i in images)})

if objs:
    lo, hi = c.world_bounds(objs)
    report["size"] = {"height": round(hi.z - lo.z, 4), "lowest_z": round(lo.z, 4),
                      "width": round(hi.x - lo.x, 4), "depth": round(hi.y - lo.y, 4)}

for a in report["armatures"]:
    print(f"ARMATURE {a['name']}: {a['bones']} bones, preset={a['preset']}, R15 names present={len(a['r15_present'])}/16")
for m in report["meshes"]:
    print(f"MESH {m['name']}: {m['vertices']} verts, {m['triangles']} tris, max influences {m['max_influences']}, unweighted {m['unweighted']}")
for m in report["materials"]:
    print(f"MATERIAL {m['name']}: textures={m['textures']} alpha={m['alpha_channel']}")
if "size" in report:
    print(f"SIZE height={report['size']['height']} lowest_z={report['size']['lowest_z']}")
for w in report["warnings"]:
    print(f"WARNING {w}")
c.write_report(args.report, report)
