"""Check a model against Roblox's skinned-character rules; exits 1 if anything fails.

blender --background --python scripts/verify.py -- export/model.fbx [--report verify.json]

Works on the exported FBX (re-imported into an empty scene) or on any .blend.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from morphtools import common as c  # noqa: E402


def configure(p):
    p.add_argument("input")
    p.add_argument("--report")


args = c.parse("verify.py", __doc__.splitlines()[0], configure)
c.load(args.input)
checks = []


def check(name, ok, detail=""):
    checks.append({"check": name, "ok": bool(ok), "detail": detail})


arms = c.armatures()
arm = arms[0] if len(arms) == 1 else None
check("exactly one armature", arm, f"found {len(arms)}")
if arm:
    bones = arm.data.bones
    missing = [b for b in c.R15 if b not in bones]
    check("all 16 R15 bones present", not missing, f"missing {missing}" if missing else f"{len(bones)} bones")
    root = bones.get("HumanoidRootPart")
    check("HumanoidRootPart is the root bone", root and root.parent is None)
    lower = bones.get("LowerTorso")
    check("LowerTorso is parented to HumanoidRootPart", lower and lower.parent and lower.parent.name == "HumanoidRootPart")
    roots = [b.name for b in bones if b.parent is None]
    check("single root bone", len(roots) == 1, f"roots {roots}")

objs = c.meshes()
check("has meshes", objs, f"{len(objs)} meshes")
for obj in objs:
    counts = c.influences(obj, arm)
    tris = c.triangles(obj)
    check(f"{obj.name}: <= {c.MAX_TRIANGLES} triangles", tris <= c.MAX_TRIANGLES, f"{tris}")
    check(f"{obj.name}: <= {c.MAX_INFLUENCES} influences per vertex", max(counts, default=0) <= c.MAX_INFLUENCES, f"max {max(counts, default=0)}")
    check(f"{obj.name}: every vertex weighted", counts and all(counts), f"{sum(1 for n in counts if n == 0)} unweighted")

size = None
if objs:
    lo, hi = c.world_bounds(objs)
    size = {"height": round(hi.z - lo.z, 4), "lowest_z": round(lo.z, 4)}
    check("feet on the ground (lowest point ~0)", abs(lo.z) <= 0.02 * max(hi.z - lo.z, 1e-6), f"lowest z {lo.z:.4f}")

failed = [x for x in checks if not x["ok"]]
for x in checks:
    print(f"{'PASS' if x['ok'] else 'FAIL'}  {x['check']}  {x['detail']}")
if size:
    print(f"SIZE height {size['height']} (in this file's units)")
print(f"RESULT {'FAIL' if failed else 'PASS'} ({len(checks) - len(failed)}/{len(checks)} checks)")
c.write_report(args.report, {"input": args.input, "checks": checks, "size": size, "passed": not failed})
if failed:
    raise SystemExit(1)
