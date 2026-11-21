--!strict
-- Morph pads. Tag a part "MorphPad" and give it a string attribute "Morph" naming a model in
-- ServerStorage.Morphs. Touching the pad swaps the player's character for a copy of that model.
-- Each morph model needs a Humanoid and a HumanoidRootPart (the root bone's part).

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ServerStorage = game:GetService("ServerStorage")

local MORPHS = ServerStorage:WaitForChild("Morphs")
local COOLDOWN = 3
local lastMorph: { [Player]: number } = {}

local function applyMorph(player: Player, morphName: string)
	local template = MORPHS:FindFirstChild(morphName)
	if not (template and template:IsA("Model")) then
		warn(`MorphPad: no model called {morphName} in ServerStorage.Morphs`)
		return
	end
	local morph = template:Clone()
	local humanoid = morph:FindFirstChildOfClass("Humanoid")
	local root = morph:FindFirstChild("HumanoidRootPart")
	if not (humanoid and root and root:IsA("BasePart")) then
		warn(`MorphPad: {morphName} needs a Humanoid and a HumanoidRootPart`)
		morph:Destroy()
		return
	end
	for _, part in morph:GetDescendants() do
		if part:IsA("BasePart") then
			part.Anchored = false
		end
	end
	morph.Name = player.Name
	morph.PrimaryPart = root

	local old = player.Character
	local oldRoot = old and old:FindFirstChild("HumanoidRootPart")
	if oldRoot and oldRoot:IsA("BasePart") then
		morph:PivotTo(oldRoot.CFrame)
	end
	player.Character = morph
	morph.Parent = workspace
	if old then
		old:Destroy()
	end
end

local function hookPad(pad: Instance)
	if not pad:IsA("BasePart") then
		return
	end
	pad.Touched:Connect(function(hit: BasePart)
		local morphName = pad:GetAttribute("Morph")
		local character = hit:FindFirstAncestorOfClass("Model")
		local player = character and Players:GetPlayerFromCharacter(character)
		if not player or typeof(morphName) ~= "string" then
			return
		end
		local now = os.clock()
		if (lastMorph[player] or 0) + COOLDOWN > now then
			return
		end
		lastMorph[player] = now
		applyMorph(player, morphName)
	end)
end

for _, pad in CollectionService:GetTagged("MorphPad") do
	hookPad(pad)
end
CollectionService:GetInstanceAddedSignal("MorphPad"):Connect(hookPad)
Players.PlayerRemoving:Connect(function(player)
	lastMorph[player] = nil
end)
