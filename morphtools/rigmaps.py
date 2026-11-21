"""Source-rig bone names mapped to Roblox R15 bone names.

Only the bones Roblox's Humanoid needs are renamed; everything else (extra
spine bones, fingers, hair, wings, tails) keeps its name and still deforms.
"""

PRESETS = {
    # Source engine / Garry's Mod workshop models
    "valve": {
        "ValveBiped.Bip01_Pelvis": "LowerTorso",
        "ValveBiped.Bip01_Spine2": "UpperTorso",
        "ValveBiped.Bip01_Head1": "Head",
        "ValveBiped.Bip01_L_UpperArm": "LeftUpperArm",
        "ValveBiped.Bip01_L_Forearm": "LeftLowerArm",
        "ValveBiped.Bip01_L_Hand": "LeftHand",
        "ValveBiped.Bip01_R_UpperArm": "RightUpperArm",
        "ValveBiped.Bip01_R_Forearm": "RightLowerArm",
        "ValveBiped.Bip01_R_Hand": "RightHand",
        "ValveBiped.Bip01_L_Thigh": "LeftUpperLeg",
        "ValveBiped.Bip01_L_Calf": "LeftLowerLeg",
        "ValveBiped.Bip01_L_Foot": "LeftFoot",
        "ValveBiped.Bip01_R_Thigh": "RightUpperLeg",
        "ValveBiped.Bip01_R_Calf": "RightLowerLeg",
        "ValveBiped.Bip01_R_Foot": "RightFoot",
    },
    # Mixamo auto-rigger output
    "mixamo": {
        "mixamorig:Hips": "LowerTorso",
        "mixamorig:Spine2": "UpperTorso",
        "mixamorig:Head": "Head",
        "mixamorig:LeftArm": "LeftUpperArm",
        "mixamorig:LeftForeArm": "LeftLowerArm",
        "mixamorig:LeftHand": "LeftHand",
        "mixamorig:RightArm": "RightUpperArm",
        "mixamorig:RightForeArm": "RightLowerArm",
        "mixamorig:RightHand": "RightHand",
        "mixamorig:LeftUpLeg": "LeftUpperLeg",
        "mixamorig:LeftLeg": "LeftLowerLeg",
        "mixamorig:LeftFoot": "LeftFoot",
        "mixamorig:RightUpLeg": "RightUpperLeg",
        "mixamorig:RightLeg": "RightLowerLeg",
        "mixamorig:RightFoot": "RightFoot",
    },
    # VRoid / VRM humanoids
    "vrm": {
        "J_Bip_C_Hips": "LowerTorso",
        "J_Bip_C_UpperChest": "UpperTorso",
        "J_Bip_C_Head": "Head",
        "J_Bip_L_UpperArm": "LeftUpperArm",
        "J_Bip_L_LowerArm": "LeftLowerArm",
        "J_Bip_L_Hand": "LeftHand",
        "J_Bip_R_UpperArm": "RightUpperArm",
        "J_Bip_R_LowerArm": "RightLowerArm",
        "J_Bip_R_Hand": "RightHand",
        "J_Bip_L_UpperLeg": "LeftUpperLeg",
        "J_Bip_L_LowerLeg": "LeftLowerLeg",
        "J_Bip_L_Foot": "LeftFoot",
        "J_Bip_R_UpperLeg": "RightUpperLeg",
        "J_Bip_R_LowerLeg": "RightLowerLeg",
        "J_Bip_R_Foot": "RightFoot",
    },
    # Unity humanoid naming (many marketplace and Sketchfab rigs)
    "unity": {
        "Hips": "LowerTorso",
        "Chest": "UpperTorso",
        "Head": "Head",
        "LeftUpperArm": "LeftUpperArm",
        "LeftLowerArm": "LeftLowerArm",
        "LeftHand": "LeftHand",
        "RightUpperArm": "RightUpperArm",
        "RightLowerArm": "RightLowerArm",
        "RightHand": "RightHand",
        "LeftUpperLeg": "LeftUpperLeg",
        "LeftLowerLeg": "LeftLowerLeg",
        "LeftFoot": "LeftFoot",
        "RightUpperLeg": "RightUpperLeg",
        "RightLowerLeg": "RightLowerLeg",
        "RightFoot": "RightFoot",
    },
}

# Fallbacks when a rig lacks the preferred torso bone (e.g. no Spine2 / UpperChest).
FALLBACKS = {
    "valve": {"UpperTorso": ["ValveBiped.Bip01_Spine1", "ValveBiped.Bip01_Spine"], "Head": ["ValveBiped.Bip01_Head"]},
    "mixamo": {"UpperTorso": ["mixamorig:Spine1", "mixamorig:Spine"]},
    "vrm": {"UpperTorso": ["J_Bip_C_Chest", "J_Bip_C_Spine"]},
    "unity": {"UpperTorso": ["UpperChest", "Spine"]},
}


def detect(bone_names):
    """The preset whose bones best match the rig, or None."""
    names = set(bone_names)
    scored = sorted(((sum(1 for b in m if b in names), p) for p, m in PRESETS.items()), reverse=True)
    best_score, best = scored[0]
    return best if best_score >= 8 else None


def mapping_for(preset, bone_names):
    """Concrete {source: R15} mapping for this rig, applying torso/head fallbacks."""
    names = set(bone_names)
    result = {src: dst for src, dst in PRESETS[preset].items() if src in names}
    for dst, candidates in FALLBACKS.get(preset, {}).items():
        if dst not in result.values():
            for candidate in candidates:
                if candidate in names and candidate not in result:
                    result[candidate] = dst
                    break
    return result
