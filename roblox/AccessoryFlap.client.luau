--!strict
-- Flaps named bones on a skinned morph: wings, ears, tails. Put this LocalScript inside the
-- morph model (it runs once the model is the player's character) and set attributes on it:
--   Bones      (string)  comma-separated bone names, e.g. "LeftWing,RightWing"
--   BaseAngle  (number)  resting angle in degrees (default 0)
--   Amplitude  (number)  swing either side in degrees (default 25)
--   Speed      (number)  flaps per second (default 1.5)
--   Axis       (string)  "X", "Y" or "Z" (default "Z")
-- Bones whose names contain "Right", "_R" or ".R" swing mirrored.

local RunService = game:GetService("RunService")

local model = script:FindFirstAncestorOfClass("Model")
local bones: { Bone } = {}
local mirror: { number } = {}
for name in string.gmatch(tostring(script:GetAttribute("Bones") or ""), "[^,%s]+") do
	local bone = model and model:FindFirstChild(name, true)
	if bone and bone:IsA("Bone") then
		table.insert(bones, bone)
		local right = name:find("Right") or name:find("_R$") or name:find("%.R$")
		table.insert(mirror, if right then -1 else 1)
	else
		warn(`AccessoryFlap: no bone called {name}`)
	end
end

local base = math.rad(tonumber(script:GetAttribute("BaseAngle")) or 0)
local amplitude = math.rad(tonumber(script:GetAttribute("Amplitude")) or 25)
local speed = tonumber(script:GetAttribute("Speed")) or 1.5
local axis = tostring(script:GetAttribute("Axis") or "Z")

local function rotation(angle: number): CFrame
	if axis == "X" then
		return CFrame.Angles(angle, 0, 0)
	elseif axis == "Y" then
		return CFrame.Angles(0, angle, 0)
	end
	return CFrame.Angles(0, 0, angle)
end

local elapsed = 0
local connection = RunService.PreSimulation:Connect(function(dt: number)
	elapsed += dt
	local wave = math.sin(elapsed * speed * 2 * math.pi)
	for i, bone in bones do
		bone.Transform = rotation(mirror[i] * (base + amplitude * wave))
	end
end)

script.Destroying:Connect(function()
	connection:Disconnect()
end)
