# Blender → Roblox morph tools

Blender scripts that turn a rigged character model into a Roblox R15 morph, plus the Roblox scripts to use it in game. They automate the steps I repeat on every conversion: clean up the import, scale it to Roblox size, rename the rig to R15, keep skinning within Roblox's limits, export, and check the result before it ever reaches Studio.

Bring your own model and respect its license. No character models are included.

## What's here

| File | What it does |
| --- | --- |
| `scripts/inspect.py` | Audits a model: armature and detected rig type, meshes, triangle counts, bone influences, unweighted vertices, materials, size. |
| `scripts/prepare.py` | Removes props and helpers by name, resets the rest pose, applies transforms, scales to a height in studs, stands the model on the ground and centers it. |
| `scripts/map_rig.py` | Renames the main bones to R15 names (presets: Source/ValveBiped, Mixamo, VRoid/VRM, Unity humanoid, or your own JSON map) and makes `HumanoidRootPart` the root. Extra bones such as hair, wings and tails keep deforming. |
| `scripts/weights.py` | Limits every vertex to 4 bone influences and normalizes the weights. |
| `scripts/materials.py` | Lists textures, flags materials that need `SurfaceAppearance.AlphaMode = Transparency`, and can copy every texture into one folder for uploading. |
| `scripts/export_fbx.py` | Exports armature and meshes as FBX with Roblox's recommended Blender settings. |
| `scripts/verify.py` | Checks a `.blend` or the exported FBX: all 16 R15 bones, a single `HumanoidRootPart` root, ≤ 4 influences, every vertex weighted, ≤ 20,000 triangles per mesh, feet on the ground. Exits 1 on failure. |
| `roblox/MorphPad.server.luau` | Morph pads: touching a tagged part swaps the player's character for a morph model. |
| `roblox/AccessoryFlap.client.luau` | Flaps named bones (wings, ears, tails) on a skinned morph, configured with attributes. |

## Requirements

- Blender 4.2 or newer (tested on 5.3), run from the command line
- Roblox Studio

## Converting a model

Run each step with Blender in the background. Every step writes a new file, so the original is never touched.

```bash
B="C:/Program Files/Blender Foundation/Blender 5.3/blender.exe"

"$B" -b --python scripts/inspect.py   -- model.glb --report work/inspect.json
"$B" -b --python scripts/prepare.py   -- model.glb --out work/prepared.blend --height 5.3 --remove "Book|Helper"
"$B" -b --python scripts/map_rig.py   -- work/prepared.blend --out work/rigged.blend
"$B" -b --python scripts/weights.py   -- work/rigged.blend   --out work/weighted.blend
"$B" -b --python scripts/materials.py -- work/weighted.blend --copy-textures work/textures
"$B" -b --python scripts/verify.py    -- work/weighted.blend
"$B" -b --python scripts/export_fbx.py -- work/weighted.blend --out export/model.fbx
"$B" -b --python scripts/verify.py    -- export/model.fbx
```

- **Facing:** the model should face −Y in Blender (front view). Use `prepare.py --rotate-z 180` (or 90/−90) to turn it.
- **Unknown rigs:** pass `--preset` or a `--map` JSON like `{"Hips": "LowerTorso", "Chest": "UpperTorso", ...}`.

## Importing into Studio

1. Open the 3D Importer and choose `export/model.fbx`.
2. Use **Import Only as Model**, **Upload**, **Add to Workspace**, **Keep Zero Influence Bones**, creator set to you, and **Anchored** off.
3. Set the model's `PrimaryPart` to `HumanoidRootPart`.
4. For each material that `materials.py` flagged, set the `SurfaceAppearance`'s `AlphaMode` to `Transparency`.

## Fixes for common problems

- **Black patches on the face or eyes:** an overlay texture with alpha came in opaque. Set that `SurfaceAppearance.AlphaMode` to `Transparency`.
- **Feet sinking or floating:** run `prepare.py`, which stands the lowest point on the ground. Then check `verify.py`'s "feet on the ground" result.
- **Mesh tearing when moving:** more than 4 influences or unweighted vertices. Run `weights.py`, and weight-paint anything `verify.py` reports as unweighted.
- **Import rejected for size:** a mesh is over 20,000 triangles. Decimate or split it.
- **Wings, ears or tails don't move:** add `AccessoryFlap.client.luau` inside the morph with `Bones = "LeftWing,RightWing"`.

## Using morphs in game

1. Put finished morph models, each with a `Humanoid` and a `HumanoidRootPart`, in `ServerStorage.Morphs`.
2. Add `roblox/MorphPad.server.luau` to `ServerScriptService`.
3. Tag any part `MorphPad` and give it a `Morph` attribute with the model's name.

## Smoke test

`tests/run_smoke.py` builds a Source-style test rig with the usual problems: wrong scale and position, a stray prop, 5-influence vertices and an alpha texture. It then runs every script on it and verifies the exported FBX.

```bash
python tests/run_smoke.py --blender "C:/Program Files/Blender Foundation/Blender 5.3/blender.exe"
```
