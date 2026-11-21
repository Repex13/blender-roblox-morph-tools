"""List materials and textures, flag the ones that need SurfaceAppearance AlphaMode = Transparency
in Studio, and optionally copy every texture into one folder for uploading.

blender --background --python scripts/materials.py -- work/weighted.blend [--report materials.json] [--copy-textures textures/]

Black patches over faces or eyes after import usually mean an overlay texture with alpha came in
opaque: set that SurfaceAppearance's AlphaMode to Transparency.
"""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bpy  # noqa: E402
from morphtools import common as c  # noqa: E402


def configure(p):
    p.add_argument("input")
    p.add_argument("--report")
    p.add_argument("--copy-textures", help="folder to copy (or unpack) every texture into")


def uses_alpha(mat):
    if not (mat.use_nodes and mat.node_tree):
        return False
    for node in mat.node_tree.nodes:
        if node.type == "BSDF_PRINCIPLED":
            alpha = node.inputs.get("Alpha")
            if alpha and (alpha.is_linked or alpha.default_value < 0.999):
                return True
    return False


args = c.parse("materials.py", __doc__.splitlines()[0], configure)
c.load(args.input)
report = []
for mat in bpy.data.materials:
    if not mat.users:
        continue
    images = [n.image for n in (mat.node_tree.nodes if mat.use_nodes and mat.node_tree else [])
              if n.type == "TEX_IMAGE" and n.image]
    entry = {"material": mat.name, "textures": [i.name for i in images],
             "needs_transparency": uses_alpha(mat) or any(i.channels == 4 for i in images)}
    report.append(entry)
    flag = "  -> SurfaceAppearance.AlphaMode = Transparency" if entry["needs_transparency"] else ""
    print(f"MATERIAL {mat.name}: {entry['textures'] or 'no textures'}{flag}")

if args.copy_textures:
    out = Path(args.copy_textures)
    out.mkdir(parents=True, exist_ok=True)
    for img in bpy.data.images:
        if img.source != "FILE":
            continue
        name = Path(bpy.path.basename(img.filepath) or f"{img.name}.png").name
        target = out / name
        if img.packed_file:
            target.write_bytes(img.packed_file.data)
        else:
            src = Path(bpy.path.abspath(img.filepath))
            if src.exists():
                shutil.copy2(src, target)
            else:
                print(f"WARNING missing texture file for {img.name}: {src}")
                continue
        print(f"copied {target}")
c.write_report(args.report, report)
