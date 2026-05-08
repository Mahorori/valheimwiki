using BepInEx;
using BepInEx.Logging;
using HarmonyLib;
using MyFirstPlugin.Converter;
using Newtonsoft.Json;
using Newtonsoft.Json.Serialization;
using SoftReferenceableAssets;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.IO;
using System.Linq;
using System.Text;
using UnityEngine;
using UnityEngine.InputSystem.HID;
using static CharacterDrop;
using static DungeonDB;
using static DungeonGenerator;
using static Heightmap;
using static ZoneSystem;

namespace MyFirstPlugin;

[BepInPlugin(MyPluginInfo.PLUGIN_GUID, MyPluginInfo.PLUGIN_NAME, MyPluginInfo.PLUGIN_VERSION)]
public class Plugin : BaseUnityPlugin
{
    class WorkItem
    {
        public GameObject Obj;
        public bool AddToLocation;

        public WorkItem(GameObject obj, bool addToLocation)
        {
            Obj = obj;
            AddToLocation = addToLocation;
        }
    }

    internal static new ManualLogSource Logger;
    public static Harmony harmony = new Harmony("valheim.dumper");
    //private MobImageRenderer _renderer;

    private static String localizationDirectory = Path.Combine(Paths.BepInExRootPath, "localization");

    public static readonly List<string> emptyList = new List<string>();
    private Dictionary<string, object> birdList = new Dictionary<string, object>();
    private Dictionary<string, object> fishList = new Dictionary<string, object>();
    private Dictionary<string, object> mobList = new Dictionary<string, object>();

    static readonly HashSet<Type> InterestingTypes = new HashSet<Type>
    {
        typeof(ItemDrop),
        typeof(Trader),
        typeof(CreatureSpawner),
        typeof(Piece),
        typeof(Pickable),
        typeof(Container),
        typeof(MineRock),
        typeof(MineRock5),
        typeof(TreeBase),
        typeof(TreeLog),
        typeof(DropOnDestroyed),
        typeof(Destructible),
        typeof(OfferingBowl)
    };

    void Start()
    {
        StartCoroutine(WaitAndDump());
    }

    void Update()
    {
        // F10キーでダンプ開始
        if (UnityEngine.Input.GetKeyDown(KeyCode.F10))
        {
            //StartCoroutine(_renderer.DumpAllMobImagesCoroutine());
        }
    }

    void Awake()
    {
        // Plugin startup logic
        Logger = base.Logger;
        Logger.LogInfo($"Plugin {MyPluginInfo.PLUGIN_GUID} is loaded!");

        harmony.PatchAll();

        //_renderer = gameObject.AddComponent<MobImageRenderer>();
    }

    System.Collections.IEnumerator WaitAndDump()
    {
        while (ObjectDB.instance == null || ZNetScene.instance == null)
        {
            Logger.LogInfo("Waiting for game to load...");
            yield return new WaitForSeconds(1f);
        }

        while (Localization.instance == null)
        {
            Logger.LogInfo("Waiting for Localization...");
            yield return new WaitForSeconds(1f);
        }

        while (Patch.SpawnSystemAwakePatch.CurrentInstance == null)
        {
            Logger.LogInfo("Waiting for SpawnSystem...");
            yield return new WaitForSeconds(1f);
        }

        Logger.LogInfo("Game loaded, start dump");
        DumpAll();
    }

    void DumpBird(RandomFlyingBird bird)
    {
        float health = 1f;
        if (bird.GetComponent<Destructible>() is Destructible destructible)
        {
            health = destructible.m_health;
        }
        birdList.Add(bird.name, new
        {
            id = bird.name,
            name = bird.name, // bird has no name?
            hp = health
        });
    }

    void DumpFish(Fish fish)
    {
        float health = 1f;
        if (fish.GetComponent<Destructible>() is Destructible destructible)
        {
            health = destructible.m_health;
        }
        fishList.Add(fish.name, new
        {
            id = fish.name,
            name = fish.m_name,
            hp = health
        });
    }

    void DumpCharacter(Character c)
    {
        Dictionary<string, string> mods = new Dictionary<string, string>();
        mods.Add("blunt", c.m_damageModifiers.m_blunt.ToString());
        mods.Add("slash", c.m_damageModifiers.m_slash.ToString());
        mods.Add("pierce", c.m_damageModifiers.m_pierce.ToString());
        mods.Add("chop", c.m_damageModifiers.m_chop.ToString());
        mods.Add("pickaxe", c.m_damageModifiers.m_pickaxe.ToString());
        mods.Add("fire", c.m_damageModifiers.m_fire.ToString());
        mods.Add("frost", c.m_damageModifiers.m_frost.ToString());
        mods.Add("lightning", c.m_damageModifiers.m_lightning.ToString());
        mods.Add("poison", c.m_damageModifiers.m_poison.ToString());
        mods.Add("spirit", c.m_damageModifiers.m_spirit.ToString());
        mobList.Add(c.name, new
        {
            id = c.name,
            name = c.m_name,
            faction = c.m_faction.ToString(),
            boss = c.m_boss,

            // health & damage
            hp = c.m_health,
            damageModifiers = mods,
            tameable = c.GetComponent<Tameable>() != null

        });
    }

    void DumpAll()
    {
        try
        {
            Logger.LogInfo("=== START DUMP ===");

            DumpItems();
            Logger.LogInfo("Items OK");

            DumpRecipes();
            Logger.LogInfo("Recipes OK");

            DumpDrops();
            Logger.LogInfo("Drops OK");

            DumpSpawnList();
            Logger.LogInfo("SpawnList OK");

            DumpLocalize();

            //
            var craftingStationIconDir = Path.Combine(Paths.BepInExRootPath, "icons/craftingStation");
            Directory.CreateDirectory(craftingStationIconDir);

            // Dump
            var craftingStations = new Dictionary<string, object>();
            foreach (var prefab in ZNetScene.instance.m_prefabs)
            {
                if (prefab.GetComponent<RandomFlyingBird>() is RandomFlyingBird bird)
                {
                    DumpBird(bird);
                }
                else if (prefab.GetComponent<Fish>() is Fish fish)
                {
                    DumpFish(fish);
                }
                else if (prefab.GetComponent<Character>() is Character c)
                {
                    DumpCharacter(c);
                }
                else if (prefab.GetComponent<CraftingStation>() is CraftingStation craftingStation)
                {
                    SaveIcon(craftingStation.m_icon, Path.Combine(craftingStationIconDir, craftingStation.name + ".png"));

                    craftingStations.Add(craftingStation.name, new
                    {
                        id = craftingStation.name,
                        name = craftingStation.m_name,
                        discoverRange = craftingStation.m_discoverRange,
                        rangeBuild = craftingStation.m_rangeBuild,
                        extraRangePerLevel = craftingStation.m_extraRangePerLevel,
                        craftRequireRoof = craftingStation.m_craftRequireRoof,
                        craftRequireFire = craftingStation.m_craftRequireFire,
                    });
                }
                else if (prefab.GetComponent<CookingStation>() is CookingStation cookingStation)
                {
                    var piece = prefab.GetComponent<Piece>();
                    if (piece != null && piece.m_icon != null)
                    {
                        // Do we have icon?
                        SaveIcon(piece.m_icon, Path.Combine(craftingStationIconDir, cookingStation.name + ".png"));
                    }

                    craftingStations.Add(cookingStation.name, new
                    {
                        id = cookingStation.name,
                        name = cookingStation.m_name
                    });
                }
                else if (prefab.GetComponent<Smelter>() is Smelter smelter)
                {
                    if (smelter.m_conversion == null)
                        continue;

                    var piece = prefab.GetComponent<Piece>();
                    if (piece != null && piece.m_icon != null)
                    {
                        // Do we have icon?
                        SaveIcon(piece.m_icon, Path.Combine(craftingStationIconDir, smelter.name + ".png"));
                    }

                    craftingStations.Add(smelter.name, new
                    {
                        id = smelter.name,
                        name = smelter.m_name
                    });
                }
                else if (prefab.GetComponent<Fermenter>() is Fermenter fermenter)
                {
                    if (fermenter.m_conversion == null)
                        continue;

                    var piece = prefab.GetComponent<Piece>();
                    if (piece != null && piece.m_icon != null)
                    {
                        // Do we have icon?
                        SaveIcon(piece.m_icon, Path.Combine(craftingStationIconDir, fermenter.name + ".png"));
                    }

                    craftingStations.Add(fermenter.name, new
                    {
                        id = fermenter.name,
                        name = fermenter.m_name
                    });
                }
            }

            WriteJson("birds.json", birdList);
            WriteJson("fish.json", fishList);
            WriteJson("mobs.json", mobList);
            WriteJson("craftingStations.json", craftingStations);

            Logger.LogInfo("=== DUMP COMPLETE ===");
        }
        catch (System.Exception e)
        {
            Logger.LogError("DUMP FAILED: " + e);
        }
    }

    static Dictionary<Texture2D, Texture2D> readableCache = new();

    public static Texture2D GetReadable(Texture2D source)
    {
        if (source == null) return null;

        // すでに作ってたら再利用
        if (readableCache.TryGetValue(source, out var cached))
            return cached;

        // RenderTexture作成
        RenderTexture rt = RenderTexture.GetTemporary(
            source.width,
            source.height,
            0,
            RenderTextureFormat.Default,
            RenderTextureReadWrite.Linear
        );

        // GPUコピー
        Graphics.Blit(source, rt);

        // アクティブ切り替え
        RenderTexture prev = RenderTexture.active;
        RenderTexture.active = rt;

        // 読み取り用Texture作成
        Texture2D readable = new Texture2D(
            source.width,
            source.height,
            TextureFormat.RGBA32,
            false
        );

        readable.ReadPixels(
            new Rect(0, 0, rt.width, rt.height),
            0,
            0
        );
        readable.Apply();

        // 後始末
        RenderTexture.active = prev;
        RenderTexture.ReleaseTemporary(rt);

        // キャッシュ保存
        readableCache[source] = readable;

        return readable;
    }

    public void SaveIcon(Sprite icon, string path)
    {
        if (icon != null)
        {
            var readable = GetReadable(icon.texture);

            Rect r = icon.textureRect; // ← ここ変更

            Texture2D cropped = new Texture2D((int)r.width, (int)r.height, TextureFormat.RGBA32, false);

            cropped.SetPixels(
                readable.GetPixels((int)r.x, (int)r.y, (int)r.width, (int)r.height)
            );
            cropped.Apply();

            File.WriteAllBytes(path, cropped.EncodeToPNG());
        }
    }

    public object DumpStatusEffect(StatusEffect SE)
    {
        if (SE == null) return null;

        if (SE is SE_Burning burning)
        {

        }
        /*else if (SE is SE_Cozy cozy)
        {

        }*/
        else if (SE is SE_Demister demister)
        {

        }
        else if (SE is SE_Finder finder)
        {

        }
        else if (SE is SE_Frost frost)
        {

        }
        else if (SE is SE_Harpooned harpooned)
        {

        }
        else if (SE is SE_HealthUpgrade healthUpgrade)
        {

        }
        else if (SE is SE_Poison poison)
        {

        }
        /*else if (SE is SE_Puke puke)
        {

        }*/
        /*else if (SE is SE_Rested rested)
        {

        }*/
        else if (SE is SE_Shield shield)
        {

        }
        else if (SE is SE_Smoke smoke)
        {

        }
        else if (SE is SE_Spawn spawn)
        {

        }
        else if (SE is SE_Stats stats)
        {
            return new
            {
                runStaminaDrainModifier = stats.m_runStaminaDrainModifier,
                healthUpFront = stats.m_healthUpFront,
                healthOverTime = stats.m_healthOverTime,
                healthRegenMultiplier = stats.m_healthRegenMultiplier,
                staminaUpFront = stats.m_staminaUpFront,
                staminaOverTime = stats.m_staminaOverTime,
                staminaRegenMultiplier = stats.m_staminaRegenMultiplier,
                eitrUpFront = stats.m_eitrUpFront,
                eitrOverTime = stats.m_eitrOverTime,
                eitrRegenMultiplier = stats.m_eitrRegenMultiplier,
                addArmor = stats.m_addArmor,
                armorMultiplier = stats.m_armorMultiplier,
                addMaxCarryWeight = stats.m_addMaxCarryWeight,

                noiseModifier = stats.m_noiseModifier,
                stealthModifier = stats.m_stealthModifier,
                speedModifier = stats.m_speedModifier,
                swimSpeedModifier = stats.m_swimSpeedModifier,

                maxMaxFallSpeed = stats.m_maxMaxFallSpeed,
                fallDamageModifier = stats.m_fallDamageModifier,
                jumpModifier = stats.m_jumpModifier,
                jumpStaminaUseModifier = stats.m_jumpStaminaUseModifier,
                attackStaminaUseModifier = stats.m_attackStaminaUseModifier,
                blockStaminaUseModifier = stats.m_blockStaminaUseModifier,
                blockStaminaUseFlatValue = stats.m_blockStaminaUseFlatValue,

                adrenalineUpFront = stats.m_adrenalineUpFront,
                adrenalineModifier = stats.m_adrenalineModifier,

                staggerModifier = stats.m_staggerModifier,
                timedBlockBonus = stats.m_timedBlockBonus,

                dodgeStaminaUseModifier = stats.m_dodgeStaminaUseModifier,
                swimStaminaUseModifier = stats.m_swimStaminaUseModifier,
                homeItemStaminaUseModifier = stats.m_homeItemStaminaUseModifier,
                sneakStaminaUseModifier = stats.m_sneakStaminaUseModifier,
                runStaminaUseModifier = stats.m_runStaminaUseModifier,

                skillLevel = stats.m_skillLevel.ToString(),
                skillLevelModifier = stats.m_skillLevelModifier,
                skillLevel2 = stats.m_skillLevel2.ToString(),
                skillLevelModifier2 = stats.m_skillLevelModifier2,

                mods = stats.m_mods,

                percentigeDamageModifiers = stats.m_percentigeDamageModifiers,

                ttl = stats.m_ttl
            };
        }
        /*else if (SE is SE_Wet wet)
        {

        }*/

        return SE.GetType().FullName;
    }

    // ===== アイテム =====
    void DumpItems()
    {
        var list = new Dictionary<string, object>();
        var iconDir = Path.Combine(Paths.BepInExRootPath, "icons");
        Directory.CreateDirectory(iconDir);

        foreach (var prefab in ObjectDB.instance.m_items)
        {
            var itemDrop = prefab.GetComponent<ItemDrop>();
            if (itemDrop == null) continue;

            var data = itemDrop.m_itemData.m_shared;

            var icon = data.m_icons != null && data.m_icons.Length > 0
                ? data.m_icons[0]
                : null;

            if (icon != null)
            {
                var readable = GetReadable(icon.texture);

                Rect r = icon.textureRect; // ← ここ変更

                Texture2D cropped = new Texture2D((int)r.width, (int)r.height, TextureFormat.RGBA32, false);

                cropped.SetPixels(
                    readable.GetPixels((int)r.x, (int)r.y, (int)r.width, (int)r.height)
                );
                cropped.Apply();

                var path = Path.Combine(iconDir, prefab.name + ".png");
                File.WriteAllBytes(path, cropped.EncodeToPNG());
            }

            var exportData = new Dictionary<string, object>()
            {
                ["id"] = prefab.name,
                ["type"] = data.m_itemType.ToString(),
                ["name"] = data.m_name,
                ["description"] = data.m_description,
                ["icon"] = $"icons/{prefab.name}.png",
                ["maxStackSize"] = data.m_maxStackSize,
                ["maxQuality"] = data.m_maxQuality,
                ["weight"] = data.m_weight,
                ["teleportable"] = data.m_teleportable, // maybe useful
                ["setStatusEffect"] = DumpStatusEffect(data.m_setStatusEffect),
                ["equipStatusEffect"] = DumpStatusEffect(data.m_equipStatusEffect),
            };

            var buildPieces = new List<object>();
            if (data.m_buildPieces)
            {
                foreach (var piece in data.m_buildPieces.m_pieces)
                {
                    var p = piece.GetComponent<Piece>();
                    if (p == null) continue;

                    var requirements = new Dictionary<string, object>();
                    if (p.m_craftingStation) requirements.Add("craftingStation", p.m_craftingStation.name);

                    var resources = new List<object>();
                    foreach (var r in p.m_resources)
                    {
                        if (r == null) continue;
                        if (r.m_resItem == null) continue;

                        resources.Add(new
                        {
                            item = r.m_resItem.name,
                            amount = r.m_amount,
                            amountPerLevel = r.m_amountPerLevel
                        });
                    }
                    requirements.Add("resources", resources);

                    buildPieces.Add(new
                    {
                        // Basic stuffs
                        id = p.name,
                        name = p.m_name,
                        description = p.m_description,
                        category = p.m_category.ToString(),

                        // Comfort
                        comfort = p.m_comfort,
                        comfortGroup = p.m_comfortGroup.ToString(),

                        // Requirements
                        requirements = requirements
                    });
                }

                exportData.Add("buildPieces", buildPieces);
            }
            // Stat modifiers
            exportData.Add("eitrRegenModifier", data.m_eitrRegenModifier);
            exportData.Add("movementModifier", data.m_movementModifier);
            exportData.Add("homeItemsStaminaModifier", data.m_homeItemsStaminaModifier);
            exportData.Add("heatResistanceModifier", data.m_heatResistanceModifier);
            exportData.Add("jumpStaminaModifier", data.m_jumpStaminaModifier);
            exportData.Add("attackStaminaModifier", data.m_attackStaminaModifier);
            exportData.Add("blockStaminaModifier", data.m_blockStaminaModifier);
            exportData.Add("dodgeStaminaModifier", data.m_dodgeStaminaModifier);
            exportData.Add("swimStaminaModifier", data.m_swimStaminaModifier);
            exportData.Add("sneakStaminaModifier", data.m_sneakStaminaModifier);
            exportData.Add("runStaminaModifier", data.m_runStaminaModifier);
            // food
            if (data.m_food > 0f) exportData.Add("food", data.m_food);
            if (data.m_foodStamina > 0f) exportData.Add("foodStamina", data.m_foodStamina);
            if (data.m_foodEitr > 0f) exportData.Add("foodEitr", data.m_foodEitr);
            if (data.m_food > 0f || data.m_foodStamina > 0f || data.m_foodEitr > 0f || data.m_isDrink)
            {
                exportData.Add("isDrink", data.m_isDrink);
                exportData.Add("foodBurnTime", data.m_foodBurnTime);
                exportData.Add("foodRegen", data.m_foodRegen);
                exportData.Add("foodEatAnimTime", data.m_foodEatAnimTime);
            }
            // armor
            if (data.m_armor != 0) exportData.Add("armor", data.m_armor);
            if (data.m_armorPerLevel != 0) exportData.Add("armorPerLevel", data.m_armorPerLevel);
            if (data.m_damageModifiers != null) exportData.Add("damageModifiers", data.m_damageModifiers);
            // shield
            if (data.m_blockPower != 0) exportData.Add("blockPower", data.m_blockPower);
            if (data.m_blockPowerPerLevel != 0) exportData.Add("blockPowerPerLevel", data.m_blockPowerPerLevel);
            if (data.m_deflectionForce != 0) exportData.Add("deflectionForce", data.m_deflectionForce);
            if (data.m_deflectionForcePerLevel != 0) exportData.Add("deflectionForcePerLevel", data.m_deflectionForcePerLevel);
            if (data.m_timedBlockBonus != 0) exportData.Add("timedBlockBonus", data.m_timedBlockBonus);
            if (data.m_perfectBlockStaminaRegen != 0) exportData.Add("perfectBlockStaminaRegen", data.m_perfectBlockStaminaRegen);
            //if (data.m_perfectBlockStaminaRegen != 0) exportData.Add("armor", data.m_perfectBlockStaminaRegen);

            // Adrenaline
            if (data.m_maxAdrenaline != 0) exportData.Add("maxAdrenaline", data.m_maxAdrenaline);
            if (data.m_blockAdrenaline != 0) exportData.Add("blockAdrenaline", data.m_blockAdrenaline);
            if (data.m_perfectBlockAdrenaline != 0) exportData.Add("perfectBlockAdrenaline", data.m_perfectBlockAdrenaline);
            if (data.m_fullAdrenalineSE) exportData.Add("fullAdrenalineSE", DumpStatusEffect(data.m_fullAdrenalineSE));

            // Weapon
            if (itemDrop.m_itemData.IsWeapon())
            {
                exportData.Add("skillType", data.m_skillType.ToString());
                exportData.Add("toolTier", data.m_toolTier);
                exportData.Add("attackStatusEffect", DumpStatusEffect(data.m_attackStatusEffect));
                exportData.Add("attackStatusEffectChance", data.m_attackStatusEffectChance);
            }

            Dictionary<string, float> damages = new();
            if (data.m_damages.m_damage != 0) damages.Add("damage", data.m_damages.m_damage);
            if (data.m_damages.m_blunt != 0) damages.Add("blunt", data.m_damages.m_blunt);
            if (data.m_damages.m_slash != 0) damages.Add("slash", data.m_damages.m_slash);
            if (data.m_damages.m_pierce != 0) damages.Add("pierce", data.m_damages.m_pierce);
            if (data.m_damages.m_chop != 0) damages.Add("chop", data.m_damages.m_chop);
            if (data.m_damages.m_pickaxe != 0) damages.Add("pickaxe", data.m_damages.m_pickaxe);
            if (data.m_damages.m_fire != 0) damages.Add("fire", data.m_damages.m_fire);
            if (data.m_damages.m_frost != 0) damages.Add("frost", data.m_damages.m_frost);
            if (data.m_damages.m_lightning != 0) damages.Add("lightning", data.m_damages.m_lightning);
            if (data.m_damages.m_poison != 0) damages.Add("poison", data.m_damages.m_poison);
            if (data.m_damages.m_spirit != 0) damages.Add("spirit", data.m_damages.m_spirit);
            if (damages.Count > 0) exportData.Add("damages", damages);

            Dictionary<string, float> damagesPerLevel = new();
            if (data.m_damagesPerLevel.m_damage != 0) damagesPerLevel.Add("damage", data.m_damagesPerLevel.m_damage);
            if (data.m_damagesPerLevel.m_blunt != 0) damagesPerLevel.Add("blunt", data.m_damagesPerLevel.m_blunt);
            if (data.m_damagesPerLevel.m_slash != 0) damagesPerLevel.Add("slash", data.m_damagesPerLevel.m_slash);
            if (data.m_damagesPerLevel.m_pierce != 0) damagesPerLevel.Add("pierce", data.m_damagesPerLevel.m_pierce);
            if (data.m_damagesPerLevel.m_chop != 0) damagesPerLevel.Add("chop", data.m_damagesPerLevel.m_chop);
            if (data.m_damagesPerLevel.m_pickaxe != 0) damagesPerLevel.Add("pickaxe", data.m_damagesPerLevel.m_pickaxe);
            if (data.m_damagesPerLevel.m_fire != 0) damagesPerLevel.Add("fire", data.m_damagesPerLevel.m_fire);
            if (data.m_damagesPerLevel.m_frost != 0) damagesPerLevel.Add("frost", data.m_damagesPerLevel.m_frost);
            if (data.m_damagesPerLevel.m_lightning != 0) damagesPerLevel.Add("lightning", data.m_damagesPerLevel.m_lightning);
            if (data.m_damagesPerLevel.m_poison != 0) damagesPerLevel.Add("poison", data.m_damagesPerLevel.m_poison);
            if (data.m_damagesPerLevel.m_spirit != 0) damagesPerLevel.Add("spirit", data.m_damagesPerLevel.m_spirit);
            if (damagesPerLevel.Count > 0) exportData.Add("damagesPerLevel", damagesPerLevel);

            // Ammo
            if (data.m_ammoType != "") exportData.Add("ammoType", data.m_ammoType);

            // Durability
            if (data.m_useDurability)
            {
                exportData.Add("maxDurability", data.m_maxDurability);
                exportData.Add("durabilityPerLevel", data.m_durabilityPerLevel);
            }

            // Consumable
            if (data.m_consumeStatusEffect)
            {
                exportData.Add("consumeStatusEffect", DumpStatusEffect(data.m_consumeStatusEffect));
            }

            list.Add(prefab.name, exportData);
        }

        WriteJson("items.json", list);
    }

    void DumpSpawnList()
    {
        var exportedSpawnList = new List<object>();
        var spawnSystem = Patch.SpawnSystemAwakePatch.CurrentInstance;
        if (spawnSystem != null)
        {
            foreach (var spawnList in spawnSystem.m_spawnLists)
            {
                foreach (var spawnData in spawnList.m_spawners)
                {
                    var biomes = new List<string>();
                    foreach (Heightmap.Biome biome in Enum.GetValues(typeof(Heightmap.Biome)))
                    {
                        if (biome == Heightmap.Biome.None) continue;
                        if (spawnData.m_biome.HasFlag(biome)) biomes.Add(biome.ToString());
                    }

                    exportedSpawnList.Add(new
                    {
                        name = spawnData.m_prefab.name,
                        biome = biomes,
                        maxSpawned = spawnData.m_maxSpawned,
                        spawnInterval = spawnData.m_spawnInterval,
                        spawnChance = spawnData.m_spawnChance,
                        requiredGlobalKey = spawnData.m_requiredGlobalKey,
                        requiredEnvironments = spawnData.m_requiredEnvironments,
                        spawnAtNight = spawnData.m_spawnAtNight,
                        spawnAtDay = spawnData.m_spawnAtDay,
                        enabled = spawnData.m_enabled,
                        min_lvl = spawnData.m_minLevel,
                        max_lvl = spawnData.m_maxLevel,
                    });
                }
            }
        }
        else
        {
            Logger.LogError("SpawnSystem instance is null");
        }

        WriteJson("spawnLocations.json", exportedSpawnList);
    }

    DropTable GetDropTable(UnityEngine.Component comp)
    {
        if (comp is MineRock rock) return rock.m_dropItems;
        if (comp is MineRock5 rock5) return rock5.m_dropItems;
        if (comp is TreeBase tree) return tree.m_dropWhenDestroyed;
        if (comp is TreeLog treeLog) return treeLog.m_dropWhenDestroyed;
        if (comp is DropOnDestroyed dropOnDestroyed) return dropOnDestroyed.m_dropWhenDestroyed;
        if (comp is Pickable pickable) return pickable.m_extraDrops;
        if (comp is Container container) return container.m_defaultItems;
        if (comp is Destructible destructible)
        {
            if (destructible.m_spawnWhenDestroyed)
                return GetDropTable(destructible.m_spawnWhenDestroyed);
        }

        // do not log those
        if (comp.GetType() == typeof(UnityEngine.MeshFilter)) return null;
        if (comp.GetType() == typeof(UnityEngine.MeshRenderer)) return null;
        if (comp.GetType() == typeof(UnityEngine.Transform)) return null;

        //Logger.LogInfo($"  GetDropTable {comp.GetType().FullName} returns null.");

        return null;
    }
    string GetPrefabString(GameObject prefab)
    {
        var rock = prefab.GetComponent<MineRock>();
        if (rock != null) return rock.m_name;

        var rock5 = prefab.GetComponent<MineRock5>();
        if (rock5 != null) return rock5.m_name;

        var pickable = prefab.GetComponent<Pickable>();
        if (pickable != null) return pickable.GetHoverName();

        var hoverText = prefab.GetComponent<HoverText>();
        if (hoverText)
        {
            return hoverText.m_text;
        }

        return prefab.name;
    }
    DropTable GetDropTable(GameObject prefab)
    {
        // rock
        var rock = prefab.GetComponent<MineRock>();
        if (rock != null) return rock.m_dropItems;

        var rock5 = prefab.GetComponent<MineRock5>();
        if (rock5 != null) return rock5.m_dropItems;

        // tree
        var tree = prefab.GetComponent<TreeBase>();
        if (tree != null) return tree.m_dropWhenDestroyed;

        // tree
        var treeLog = prefab.GetComponent<TreeLog>();
        if (treeLog != null) return treeLog.m_dropWhenDestroyed;

        // idk
        var dropOnDestroyed = prefab.GetComponent<DropOnDestroyed>();
        if (dropOnDestroyed != null) return dropOnDestroyed.m_dropWhenDestroyed;

        var pickable = prefab.GetComponent<Pickable>();
        if (pickable != null) return pickable.m_extraDrops;

        var lootSpawner = prefab.GetComponent<LootSpawner>();
        if (lootSpawner != null) return lootSpawner.m_items;

        return null;
    }

    void AddDrops(DropTable dropTable, List<object> drops)
    {
        if (dropTable != null)
        {
            foreach (var drop in dropTable.m_drops)
            {
                drops.Add(new
                {
                    name = drop.m_item.name,
                    stackMin = drop.m_stackMin,
                    stackMax = drop.m_stackMax
                });
            }
        }
    }

    // I think this is fine but maybe use worklist and iterate locations first
    void AddDrops(GameObject prefab, Dictionary<string, object> entities, List<string> biomes = null)
    {
        if (!prefab)
            return;

        if (entities.ContainsKey(prefab.name))
        {
            // merge biomes
            return;
        }

        var drops = new List<object>();
        List<string> spawnWhenDestroyed = new List<string>();

        // pickable.itemPrefab + extra
        var pickable = prefab.GetComponent<Pickable>();
        if (pickable != null)
        {
            ItemDrop component = pickable.m_itemPrefab.GetComponent<ItemDrop>();
            drops.Add(new
            {
                name = component.name,
                stackMin = 1,
                stackMax = 1
            });
        }

        if (prefab.GetComponent<Destructible>() is Destructible destructible)
        {
            if (destructible.m_spawnWhenDestroyed)
            {
                spawnWhenDestroyed.Add(destructible.m_spawnWhenDestroyed.name);
                AddDrops(destructible.m_spawnWhenDestroyed, entities);
            }
        }

        // 木
        if (prefab.GetComponent<TreeBase>() is TreeBase treeBase)
        {
            // 丸太
            if (treeBase.m_logPrefab)
            {
                spawnWhenDestroyed.Add(treeBase.m_logPrefab.name);
                AddDrops(treeBase.m_logPrefab, entities);
            }

            // 切り株
            if (treeBase.m_stubPrefab)
            {
                spawnWhenDestroyed.Add(treeBase.m_stubPrefab.name);
                AddDrops(treeBase.m_stubPrefab, entities);
            }
        }

        // 丸太
        if (prefab.GetComponent<TreeLog>() is TreeLog treeLog)
        {
            // 丸太のさらに半分
            if (treeLog.m_subLogPrefab)
            {
                spawnWhenDestroyed.Add(treeLog.m_subLogPrefab.name);
                AddDrops(treeLog.m_subLogPrefab, entities);
            }
        }

        var dropTable = GetDropTable(prefab);
        if (dropTable != null)
        {
            AddDrops(dropTable, drops);
        }
        else
        {
            //Logger.LogWarning($"{name} does not have DropTable");
        }

        entities.Add(prefab.name, new
        {
            id = prefab.name,
            name = GetPrefabString(prefab),
            spawnWhenDestroyed = spawnWhenDestroyed,
            drops = drops,
            biomes = biomes != null ? biomes : emptyList
        });
    }

    void DumpCookingStationConversion(CookingStation cookingStation)
    {
        var list = new List<object>();
        foreach (var conv in cookingStation.m_conversion)
        {
            list.Add(new
            {
                from = conv.m_from,
                to = conv.m_to,
                cookTime = conv.m_cookTime
            });
        }
        WriteJson("cooking.json", list);
    }
    // ===== レシピ =====
    void DumpRecipes()
    {
        if (ObjectDB.instance == null)
        {
            Logger.LogWarning("ObjectDB null");
            return;
        }

        var iconDir = Path.Combine(Paths.BepInExRootPath, "icons/craftingStation");
        Directory.CreateDirectory(iconDir);

        var list = new List<object>();
        var traderList = new Dictionary<string, object>();

        // Normal recipes
        foreach (var recipe in ObjectDB.instance.m_recipes)
        {
            if (recipe == null) continue;
            if (recipe.m_item == null) continue;
            if (recipe.m_resources == null) continue;

            var resources = new List<object>();

            foreach (var r in recipe.m_resources)
            {
                if (r == null) continue;
                if (r.m_resItem == null) continue;

                resources.Add(new
                {
                    item = r.m_resItem.name,
                    amount = r.m_amount,
                    amountPerLevel = r.m_amountPerLevel
                });
            }

            var exportData = new Dictionary<string, object>()
            {
                ["result"] = recipe.m_item.name,
                ["amount"] = recipe.m_amount,
                ["enabled"] = recipe.m_enabled,
                ["qualityResultAmountMultiplier"] = recipe.m_qualityResultAmountMultiplier,
                ["listSortWeight"] = recipe.m_listSortWeight,
                ["requirements"] = resources
            };
            if (recipe.m_craftingStation)
            {
                exportData.Add("craftingStation", recipe.m_craftingStation.name);
            }
            if (recipe.m_repairStation)
            {
                exportData.Add("repairStation", recipe.m_repairStation.name);
            }
            if (recipe.m_minStationLevel != 0) exportData.Add("minStationLevel", recipe.m_minStationLevel);

            list.Add(exportData);
        }

        // Trader, Smelter, CookingStation
        // TODO: Incinerator, Charcoal kiln, Windmill, Spinning wheel, Incinerator, furnace?
        // SapExtractor
        foreach (var prefab in ZNetScene.instance.m_prefabs)
        {
            var trader = prefab.GetComponent<Trader>();
            var cookingStation = prefab.GetComponent<CookingStation>();
            var smelter = prefab.GetComponent<Smelter>();
            var fermenter = prefab.GetComponent<Fermenter>();

            if (trader != null)
            {
                var traderItemList = new List<object>();
                foreach (Trader.TradeItem item in trader.m_items)
                {
                    traderItemList.Add(new
                    {
                        id = item.m_prefab.name,
                        stack = item.m_stack,
                        price = item.m_price,
                        requiredGlobalKey = string.IsNullOrEmpty(item.m_requiredGlobalKey) ? "" : item.m_requiredGlobalKey,
                    });
                }
                traderList.Add(prefab.name, new
                {
                    name = trader.m_name,
                    items = traderItemList
                });
            }
            else if (cookingStation != null)
            {
                foreach (var conv in cookingStation.m_conversion)
                {
                    var resources = new List<object>();
                    resources.Add(conv.m_from.name);

                    list.Add(new
                    {
                        enabled = true,
                        result = conv.m_to.name,
                        amount = 1,
                        requirements = resources,
                        cookTime = conv.m_cookTime,
                        craftingStation = cookingStation.name
                    });
                }
            }
            else if (smelter != null)
            {
                if (smelter.m_conversion == null)
                    continue;

                foreach (var conv in smelter.m_conversion)
                {
                    string from = conv.m_from ? conv.m_from.name : "null";
                    string to = conv.m_to ? conv.m_to.name : "null";

                    var resources = new List<object>();
                    resources.Add(from);

                    list.Add(new
                    {
                        enabled = true,
                        result = to,
                        amount = 1,
                        requirements = resources,
                        craftingStation = smelter.name
                    });
                }
            }
            else if (fermenter != null)
            {
                if (fermenter.m_conversion == null)
                    continue;

                foreach (var conv in fermenter.m_conversion)
                {
                    string from = conv.m_from ? conv.m_from.name : "null";
                    string to = conv.m_to ? conv.m_to.name : "null";

                    var resources = new List<object>();
                    resources.Add(from);

                    list.Add(new
                    {
                        enabled = true,
                        result = to,
                        amount = conv.m_producedItems,
                        requirements = resources,
                        craftingStation = fermenter.name
                    });
                }
            }
        }

        WriteJson("recipes.json", list);
        WriteJson("traders.json", traderList);
    }

    object SerializeComponent(UnityEngine.Component component, bool log = false)
    {
        var result = new List<object>();
        var entities = new Dictionary<string, object>();

        if (component is OfferingBowl offeringBowl)
        {
            return (new
            {
                type = "OfferingBowl",
                id = offeringBowl.name,
                name = offeringBowl.m_name,
                bossItem = offeringBowl.m_bossItem?.name,
                bossItems = offeringBowl.m_bossItems,
                bossPrefab = offeringBowl.m_bossPrefab?.name,
                itemPrefab = offeringBowl.m_itemPrefab?.name,
                setGlobalKey = offeringBowl.m_setGlobalKey
            });
        }
        else if (component is ItemDrop itemDrop)
        {
            return (new
            {
                type = "ItemDrop",
                id = itemDrop.name,
                stack = itemDrop.m_itemData.m_stack,
                durability = itemDrop.m_itemData.m_durability,
                quality = itemDrop.m_itemData.m_quality
            });
        }
        else if (component is Trader trader)
        {
            return (new
            {
                type = "Trader",
                id = trader.name,
                name = trader.m_name,
            });
        }
        else if (component is CreatureSpawner spawner)
        {
            return (new
            {
                type = "CreatureSpawner",
                id = spawner.name,
                mob_id = spawner.m_creaturePrefab.name,
                maxLevel = spawner.m_maxLevel,
                minLevel = spawner.m_minLevel,
                levelupChance = spawner.m_levelupChance,
                spawnAtNight = spawner.m_spawnAtNight,
                spawnAtDay = spawner.m_spawnAtDay,
                spawnInterval = spawner.m_spawnInterval,
                requiredGlobalKey = spawner.m_requiredGlobalKey,
                blockingGlobalKey = spawner.m_blockingGlobalKey,
            });
        }
        else if (component is Piece piece)
        {
            return (new
            {
                type = "Piece",
                id = component.name,
                name = piece.m_name
            });
        }
        else if (component is Pickable pickable)
        {
            var drops = new List<object>();
            foreach (var drop in pickable.m_extraDrops.m_drops)
            {
                drops.Add(new
                {
                    id = drop.m_item.name,
                    stackMin = drop.m_stackMin,
                    stackMax = drop.m_stackMax
                });
            }
            drops.Add(new
            {
                id = pickable.m_itemPrefab.name,
                stackMin = pickable.m_amount,
                stackMax = pickable.m_amount
            });

            return (new
            {
                type = "Pickable",
                id = component.name,
                drops = drops,
            });
        }
        else if (component is Container container)
        {
            var items = new List<object>();
            foreach (var drop in container.m_defaultItems.m_drops)
            {
                items.Add(new
                {
                    name = component.name,
                    id = drop.m_item.name,
                    stackMin = drop.m_stackMin,
                    stackMax = drop.m_stackMax
                });
            }
            return (new
            {
                type = "Container",
                name = container.name,
                drops = items
            });
        }
        else
        {
            var items = new List<object>();
            var dropTable = GetDropTable(component);
            if (dropTable != null)
            {
                foreach (var drop in dropTable.m_drops)
                {
                    items.Add(new
                    {
                        name = component.name,
                        id = drop.m_item.name,
                        stackMin = drop.m_stackMin,
                        stackMax = drop.m_stackMax
                    });
                }
                return (new
                {
                    type = "Drop",
                    name = component.name,
                    drops = items
                });
            }
            else if (component is Destructible destructible)
            {
                if (destructible.m_spawnWhenDestroyed)
                {
                    return (new
                    {
                        type = "Destructible",
                        name = component.name,
                        spawnWhenDestroyed = destructible.m_spawnWhenDestroyed.name
                    });
                }
            }
        }
        return null;
    }

    void PrintGameObjectRecursive(GameObject obj, int depth = 0)
    {
        if (obj == null) return;

        string indent = new string(' ', depth * 2);

        // GameObject名
        Logger.LogInfo($"{indent}[GameObject] {obj.name}");

        // Component一覧
        var components = obj.GetComponents<UnityEngine.Component>();
        foreach (var comp in components)
        {
            if (comp == null) continue; // missing script対策
            Logger.LogInfo($"{indent}  - {comp.GetType().Name}");
        }

        // 子を再帰
        foreach (Transform child in obj.transform)
        {
            PrintGameObjectRecursive(child.gameObject, depth + 1);
        }
    }

    List<string> LocationRecursive(
        GameObject obj,
        Dictionary<string, Dictionary<string, object>> entities,
        bool addToLocation = true)
    {
        var result = new List<string>();

        // Skip room roots
        if (obj.GetComponent<Room>() != null)
            return result;

        var worklist = new Queue<WorkItem>();

        // Components
        foreach (var comp in obj.GetComponents<UnityEngine.Component>())
        {
            if (comp == null ||
                comp is Room ||
                comp is Transform ||
                comp is Location)
            {
                continue;
            }

            // Traverse spawned objects,
            // but don't add them to location list
            var destructible = comp as Destructible;
            if (destructible != null &&
                destructible.m_spawnWhenDestroyed != null)
            {
                worklist.Enqueue(
                    new WorkItem(
                        destructible.m_spawnWhenDestroyed,
                        false));
            }

            var serialized = SerializeComponent(comp);
            if (serialized == null)
                continue;

            string componentType = serialized.GetType().GetProperty("type")?.GetValue(serialized).ToString();
            if (!entities.ContainsKey(comp.name))
            {
                entities.Add(comp.name, new Dictionary<string, object> { { componentType, serialized } });
            }
            else
            {
                // add component
                if (!entities[comp.name].ContainsKey(componentType))
                {
                    entities[comp.name].Add(componentType, serialized);
                }
                else
                {
                    //Logger.LogWarning($"{comp.name} already has {componentType} so didn't add {serialized}");
                }
            }

            if (addToLocation)
            {
                result.Add(comp.name);
            }
        }

        // Real hierarchy children ARE part of location
        foreach (Transform child in obj.transform)
        {
            worklist.Enqueue(
                new WorkItem(child.gameObject, true));
        }

        // Recursive traversal
        while (worklist.Count > 0)
        {
            var item = worklist.Dequeue();

            result.AddRange(
                LocationRecursive(
                    item.Obj,
                    entities,
                    item.AddToLocation));
        }

        return result;
    }

    // ===== ドロップ =====
    void DumpDrops()
    {
        var drops = new Dictionary<string, object>();

        foreach (var prefab in ZNetScene.instance.m_prefabs)
        {
            if (prefab.GetComponent<CharacterDrop>() is CharacterDrop cd)
            {
                drops.Add(prefab.name, cd.m_drops.Select(d => new
                {
                    item = d.m_prefab.name,
                    chance = d.m_chance,
                    min = d.m_amountMin,
                    max = d.m_amountMax
                }).ToList());
            }
            else if (prefab.GetComponent<RandomFlyingBird>() is RandomFlyingBird bird)
            {
                if (bird.GetComponent<DropOnDestroyed>() is DropOnDestroyed dropOnDestroyed)
                {
                    drops.Add(prefab.name, dropOnDestroyed.m_dropWhenDestroyed.m_drops.Select(d => new
                    {
                        item = d.m_item.name,
                        chance = dropOnDestroyed.m_dropWhenDestroyed.m_dropChance,
                        min = d.m_stackMin,
                        max = d.m_stackMax
                    }).ToList());
                }
            }
            else if (prefab.GetComponent<Fish>() is Fish fish)
            {
                var fishDrops = new List<object>();
                if (fish.GetComponent<ItemDrop>() is ItemDrop d)
                {
                    fishDrops.Add(new
                    {
                        item = d.name,
                        chance = 1f,
                        min = 1, // maybe not correct
                        max = 1 // maybe not correct
                    });
                }
                if (fish.m_extraDrops != null)
                {
                    foreach (var extraDrop in fish.m_extraDrops.m_drops)
                    {
                        fishDrops.Add(new
                        {
                            item = extraDrop.m_item.name,
                            chance = fish.m_extraDrops.m_dropChance,
                            min = extraDrop.m_stackMin,
                            max = extraDrop.m_stackMax
                        });
                    }
                }
            }
        }
        WriteJson("drops.json", drops);

        // vegetation drops
        //var entities = new Dictionary<string, object>();
        var entities = new Dictionary<string, object>();
        foreach (var vegetation in ZoneSystem.instance.m_vegetation)
        {
            var prefab = vegetation.m_prefab;
            var name = prefab.name;

            var biomes = new List<string>();
            foreach (Heightmap.Biome biome in Enum.GetValues(typeof(Heightmap.Biome)))
            {
                if (biome == Heightmap.Biome.None) continue;
                if (vegetation.m_biome.HasFlag(biome)) biomes.Add(biome.ToString());
            }

            AddDrops(prefab, entities, biomes);
        }
        WriteJson("vegetations.json", entities);

        // location drops
        var locationEntities = new Dictionary<string, Dictionary<string, object>>();
        var locations = new Dictionary<string, object>();
        foreach (var zoneLocation in ZoneSystem.instance.m_locations)
        {
            try
            {
                if (!zoneLocation.m_enable) continue;

                var refPrefab = zoneLocation.m_prefab;
                refPrefab.Load();

                var prefab = refPrefab.Asset;
                var name = prefab.name;

                var biomes = new List<string>();
                foreach (Heightmap.Biome biome in Enum.GetValues(typeof(Heightmap.Biome)))
                {
                    if (biome == Heightmap.Biome.None) continue;
                    if (zoneLocation.m_biome.HasFlag(biome)) biomes.Add(biome.ToString());
                }

                if (prefab.GetComponent<Location>() is Location location)
                {
                    if (location.name == "Eikthyrnir")
                    {
                        PrintGameObjectRecursive(prefab);
                    }

                    var worklist = new Queue<UnityEngine.Component>();
                    var rooms = new List<object>();
                    DungeonGenerator dg = null;
                    if (location.m_generator)
                        dg = location.m_generator;
                    else
                    {
                        var dgs = location.GetComponentsInChildren<DungeonGenerator>();
                        if (dgs.Length > 0)
                            dg = dgs[0];
                    }

                    var loaded = new List<SoftReference<GameObject>>();
                    if (dg)
                    {
                        foreach (DungeonDB.RoomData roomData in DungeonDB.GetRooms())
                        {
                            if ((roomData.m_theme & dg.m_themes) != 0 && roomData.m_enabled)
                            {
                                roomData.m_prefab.Load();
                                loaded.Add(roomData.m_prefab);
                                Room room = roomData.m_prefab.Asset.GetComponent<Room>();
                                if (room)
                                {
                                    if (room.name == "gobvill_flax")
                                    {
                                        PrintGameObjectRecursive(room.gameObject);
                                    }

                                    // Room has Walls, Connection, Loot, Roof, Etc..
                                    var roomComponents = new HashSet<string>();
                                    foreach (var c in room.GetComponentsInChildren<UnityEngine.Component>(true))
                                    {
                                        if (c == null || c == room)
                                        {
                                            //Logger.LogInfo("c == room");
                                            continue;
                                        }

                                        if (InterestingTypes.Contains(c.GetType()))
                                        {
                                            worklist.Enqueue(c);
                                            roomComponents.Add(c.name);
                                        }
                                    }
                                    rooms.Add(new
                                    {
                                        name = room.name,
                                        components = roomComponents
                                    });
                                }
                            }
                        }
                    }
                    else
                    {
                        if (false)
                        {
                            Logger.LogWarning($"{location.name} has no generator");
                            Logger.LogWarning($"  m_hasInterior: {location.m_hasInterior}");
                            Logger.LogWarning($"  m_interiorEnvironment: {location.m_interiorEnvironment}");
                            Logger.LogWarning($"  m_interiorTransform: {location.m_interiorTransform}");
                            Logger.LogWarning($"  m_useCustomInteriorTransform: {location.m_useCustomInteriorTransform}");
                            Logger.LogWarning($"  m_interiorPrefab: {location.m_interiorPrefab}");
                            if (location.m_interiorPrefab)
                            {
                                PrintGameObjectRecursive(location.m_interiorPrefab, 2);
                            }
                            PrintGameObjectRecursive(location.gameObject, 1);
                        }
                    }

                    // Recursive traversal
                    while (worklist.Count > 0)
                    {
                        var item = worklist.Dequeue();
                        if (item == null)
                            continue;

                        var serialized = SerializeComponent(item);
                        if (serialized != null)
                        {
                            string componentType = serialized.GetType().GetProperty("type")?.GetValue(serialized).ToString();
                            if (!locationEntities.ContainsKey(item.name))
                            {
                                locationEntities.Add(item.name, new Dictionary<string, object> { { componentType, serialized } });
                            }
                            else
                            {
                                // add component
                                if (locationEntities[item.name].ContainsKey(componentType))
                                {
                                    //Logger.LogWarning($"{item.name} already has {componentType} so didn't add {serialized}");
                                }
                                else
                                {
                                    locationEntities[item.name].Add(componentType, serialized);
                                }
                            }
                        }

                        if (item is Destructible destructible)
                        {
                            if (destructible.m_spawnWhenDestroyed != null)
                            {
                                foreach (var spawnedComp in
                                    destructible.m_spawnWhenDestroyed
                                        .GetComponentsInChildren<UnityEngine.Component>(true))
                                {
                                    if (spawnedComp == null)
                                        continue;

                                    if (InterestingTypes.Contains(spawnedComp.GetType()))
                                        worklist.Enqueue(spawnedComp);
                                }
                            }
                        }
                    }

                    var exteriors = LocationRecursive(location.gameObject, locationEntities);

                    locations.Add(location.name, new
                    {
                        id = location.name,
                        biomes = biomes,
                        exteriors = exteriors,
                        rooms = rooms
                    });

                    foreach (var reference in loaded)
                    {
                        reference.Release();
                    }
                }

                refPrefab.Release();
            }
            catch (Exception ex)
            {
                Logger.LogError("LOCATION DUMP FAILED: " + ex);
            }
        }
        WriteJson("locations.json", new
        {
            locations = locations,
            entities = locationEntities
        });
    }
    private List<List<string>> DoQuoteLineSplit(StringReader reader)
    {
        List<List<string>> list = new List<List<string>>();
        List<string> list2 = new List<string>();
        StringBuilder stringBuilder = new StringBuilder();
        bool flag = false;
        while (true)
        {
            int num = reader.Read();
            switch (num)
            {
                case -1:
                    list2.Add(stringBuilder.ToString());
                    list.Add(list2);
                    return list;
                case 34:
                    flag = !flag;
                    continue;
                case 44:
                    if (!flag)
                    {
                        list2.Add(stringBuilder.ToString());
                        stringBuilder.Length = 0;
                        continue;
                    }

                    break;
            }

            if (num == 10 && !flag)
            {
                list2.Add(stringBuilder.ToString());
                stringBuilder.Length = 0;
                list.Add(list2);
                list2 = new List<string>();
            }
            else
            {
                stringBuilder.Append((char)num);
            }
        }
    }
    private string StripCitations(string s)
    {
        if (Utils.CustomStartsWith(s, "\""))
        {
            s = s.Remove(0, 1);
            if (Utils.CustomEndsWith(s, "\""))
            {
                s = s.Remove(s.Length - 1, 1);
            }
        }

        return s;
    }
    void DumpLocalize()
    {
        if (Localization.instance == null)
        {
            Logger.LogError("Localization.instance is null");
            return;
        }

        // LoadCSV
        var localizationSettings = Resources.Load<LocalizationSettings>("LocalizationSettings");
        if (!localizationSettings)
        {
            Logger.LogError("Failed to load LocalizationSettings.");
            return;
        }

        var localizations = new Dictionary<string, Dictionary<string, string>>();
        Directory.CreateDirectory(localizationDirectory);

        foreach (var language in Localization.instance.GetLanguages())
        {
            for (int i = 0; i < localizationSettings.Localizations.Count; i++)
            {
                TextAsset file = localizationSettings.Localizations[i];
                if (file == null)
                {
                    continue;
                }

                StringReader stringReader = new StringReader(file.text);
                string[] array = stringReader.ReadLine().Split(',');
                int num = -1;
                for (int j = 0; j < array.Length; j++)
                {
                    if (StripCitations(array[j]) == language)
                    {
                        num = j;
                        break;
                    }
                }

                if (num == -1)
                {
                    Logger.LogWarning((object)("Failed to find language '" + language + "' in file '" + file.name + "'"));
                    continue;
                }

                Dictionary<string, string> translations;
                if (!localizations.TryGetValue(language, out translations))
                {
                    translations = new Dictionary<string, string>();
                    localizations.Add(language, translations);
                }

                foreach (List<string> item in DoQuoteLineSplit(stringReader))
                {
                    if (item.Count == 0)
                    {
                        continue;
                    }

                    string text = item[0];
                    if (!Utils.CustomStartsWith(text, "//") && text.Length != 0 && item.Count > num)
                    {
                        string text2 = item[num].Trim();
                        if (string.IsNullOrEmpty(text2) || text2[0] == '\r')
                        {
                            text2 = item[1];
                        }

                        // this is default implementation of Localization.AddWord
                        translations.Remove(text);
                        translations.Add(text, text2);
                    }
                }
            }
        }

        foreach (var pair in localizations)
        {
            WriteJson(Path.Combine(localizationDirectory, pair.Key + ".json"), pair.Value);
        }
    }

    // ===== ユーティリティ =====
    void WriteJson(string name, object data)
    {
        var path = Path.Combine(Paths.BepInExRootPath, name);
        File.WriteAllText(path, JsonConvert.SerializeObject(data, Newtonsoft.Json.Formatting.Indented, new JsonSerializerSettings
        {
            Converters = new List<JsonConverter> { new Vector3Converter(), new DamageModifierConverter(), new DamageTypeConverter() },
            //ContractResolver = shapeResolver,
        }));
        Logger.LogInfo($"Wrote {name}");
    }
}
