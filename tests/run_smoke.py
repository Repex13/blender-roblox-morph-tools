"""Run the whole pipeline on a generated test rig and stop at the first failure.

python tests/run_smoke.py [--blender "C:/Program Files/Blender Foundation/Blender 5.3/blender.exe"]
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "out"


def find_blender():
    found = shutil.which("blender") or os.environ.get("BLENDER")
    if found:
        return found
    candidates = sorted(glob.glob(r"C:\Program Files\Blender Foundation\Blender *\blender.exe"))
    return candidates[-1] if candidates else None


def run(blender, script, *args):
    cmd = [blender, "--background", "--factory-startup", "--python-exit-code", "1",
           "--python", str(ROOT / script), "--", *map(str, args)]
    print(f"\n== {script} {' '.join(map(str, args))}")
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    lines = [l for l in proc.stdout.splitlines()
             if l.split(" ")[0] in {"ARMATURE", "MESH", "MATERIAL", "SIZE", "WARNING", "ERROR", "PREPARED", "MAPPED",
                                    "WEIGHTS", "EXPORTED", "PASS", "FAIL", "RESULT", "preset:", "built", "saved", "removed"}]
    print("\n".join(lines))
    if proc.returncode:
        print(proc.stderr[-3000:])
        sys.exit(f"{script} failed with exit code {proc.returncode}")


parser = argparse.ArgumentParser()
parser.add_argument("--blender", default=find_blender())
blender = parser.parse_args().blender
if not blender:
    sys.exit("Blender not found; pass --blender")
shutil.rmtree(OUT, ignore_errors=True)
run(blender, "tests/make_test_rig.py", OUT / "source.blend")
run(blender, "scripts/inspect.py", OUT / "source.blend", "--report", OUT / "inspect.json")
run(blender, "scripts/prepare.py", OUT / "source.blend", "--out", OUT / "prepared.blend", "--height", 5.3, "--remove", "Helper", "--rotate-z", -90)
run(blender, "scripts/map_rig.py", OUT / "prepared.blend", "--out", OUT / "rigged.blend")
run(blender, "scripts/weights.py", OUT / "rigged.blend", "--out", OUT / "weighted.blend")
run(blender, "scripts/materials.py", OUT / "weighted.blend", "--report", OUT / "materials.json", "--copy-textures", OUT / "textures")
run(blender, "scripts/verify.py", OUT / "weighted.blend", "--report", OUT / "verify-blend.json")
run(blender, "scripts/export_fbx.py", OUT / "weighted.blend", "--out", OUT / "export" / "model.fbx")
run(blender, "scripts/verify.py", OUT / "export" / "model.fbx", "--report", OUT / "verify-fbx.json")
print("\nSMOKE TEST PASSED")
