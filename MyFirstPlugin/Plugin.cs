using BepInEx;
using BepInEx.Logging;
using HarmonyLib;
using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Xml;
using UnityEngine;
using UnityEngine.Windows;
using static MyFirstPlugin.Patch;
using static Turret;

namespace MyFirstPlugin;

[BepInPlugin(MyPluginInfo.PLUGIN_GUID, MyPluginInfo.PLUGIN_NAME, MyPluginInfo.PLUGIN_VERSION)]
public class Plugin : BaseUnityPlugin
{
    internal static new ManualLogSource Logger;
    public static Harmony harmony = new Harmony("valheim.dumper");
    private MobImageRenderer _renderer;

    void Start()
    {
        StartCoroutine(WaitAndDump());
    }

    void Update()
    {
        // F10キーでダンプ開始
        if (UnityEngine.Input.GetKeyDown(KeyCode.F10))
        {
            StartCoroutine(_renderer.DumpAllMobImagesCoroutine());
        }
    }

    void Awake()
    {
        // Plugin startup logic
        Logger = base.Logger;
        Logger.LogInfo($"Plugin {MyPluginInfo.PLUGIN_GUID} is loaded!");

        harmony.PatchAll();

        _renderer = gameObject.AddComponent<MobImageRenderer>();
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

    void DumpAll()
    {
        try
        {
            Logger.LogInfo("=== START DUMP ===");

            DumpItems();
            Logger.LogInfo("Items OK");

            DumpMobs();
            Logger.LogInfo("Mobs OK");

            DumpRecipes();
            Logger.LogInfo("Recipes OK");

            DumpDrops();
            Logger.LogInfo("Drops OK");

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

    // ===== アイテム =====
    void DumpItems()
    {
        var list = new List<object>();
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
                ["name"] = Localize(data.m_name),
                ["description"] = Localize(data.m_description),
                ["icon"] = $"icons/{prefab.name}.png",
            };
            // food
            if (data.m_food != 0) exportData.Add("food", data.m_food);
            if (data.m_foodStamina != 0) exportData.Add("foodStamina", data.m_foodStamina);
            if (data.m_foodEitr != 0) exportData.Add("foodEitr", data.m_foodEitr);
            if (data.m_foodBurnTime != 0) exportData.Add("foodBurnTime", data.m_foodBurnTime);
            if (data.m_foodRegen != 0) exportData.Add("foodRegen", data.m_foodRegen);
            if (data.m_foodEatAnimTime != 0) exportData.Add("foodEatAnimTime", data.m_foodEatAnimTime);
            if (data.m_isDrink) exportData.Add("isDrink", data.m_isDrink);
            // armor
            if (data.m_armor != 0) exportData.Add("armor", data.m_armor);
            // shield
            if (data.m_blockPower != 0) exportData.Add("blockPower", data.m_blockPower);
            if (data.m_blockPowerPerLevel != 0) exportData.Add("blockPowerPerLevel", data.m_blockPowerPerLevel);
            if (data.m_deflectionForce != 0) exportData.Add("deflectionForce", data.m_deflectionForce);
            if (data.m_deflectionForcePerLevel != 0) exportData.Add("deflectionForcePerLevel", data.m_deflectionForcePerLevel);
            if (data.m_timedBlockBonus != 0) exportData.Add("timedBlockBonus", data.m_timedBlockBonus);
            if (data.m_perfectBlockStaminaRegen != 0) exportData.Add("perfectBlockStaminaRegen", data.m_perfectBlockStaminaRegen);
            //if (data.m_perfectBlockStaminaRegen != 0) exportData.Add("armor", data.m_perfectBlockStaminaRegen);
            // ammo
            if (data.m_ammoType != "") exportData.Add("ammoType", data.m_ammoType);
            // damage
            if (data.m_damages.m_damage != 0) exportData.Add("damage", data.m_damages.m_damage);
            if (data.m_damages.m_blunt != 0) exportData.Add("blunt", data.m_damages.m_blunt);
            if (data.m_damages.m_slash != 0) exportData.Add("slash", data.m_damages.m_slash);
            if (data.m_damages.m_pierce != 0) exportData.Add("pierce", data.m_damages.m_pierce);
            if (data.m_damages.m_chop != 0) exportData.Add("chop", data.m_damages.m_chop);
            if (data.m_damages.m_pickaxe != 0) exportData.Add("pickaxe", data.m_damages.m_pickaxe);
            if (data.m_damages.m_fire != 0) exportData.Add("fire", data.m_damages.m_fire);
            if (data.m_damages.m_frost != 0) exportData.Add("frost", data.m_damages.m_frost);
            if (data.m_damages.m_lightning != 0) exportData.Add("lightning", data.m_damages.m_lightning);
            if (data.m_damages.m_poison != 0) exportData.Add("poison", data.m_damages.m_poison);
            if (data.m_damages.m_spirit != 0) exportData.Add("spirit", data.m_damages.m_spirit);

            list.Add(exportData);
        }

        WriteJson("items.json", list);
    }
    void DumpMobs()
    {
        var exportedSpawnList = new List<object>();
        var mobList = new Dictionary<string, object>();

        var spawnSystem = Patch.SpawnSystemAwakePatch.CurrentInstance;
        if (spawnSystem != null)
        {
            foreach (var spawnList in spawnSystem.m_spawnLists)
            {
                foreach (var spawnData in spawnList.m_spawners)
                {
                    var biomes = new List<string>();
                    foreach (Heightmap.Biome biome in Enum.GetValues(typeof(Heightmap.Biome)))
                        if (spawnData.m_biome.HasFlag(biome)) biomes.Add(biome.ToString());

                    exportedSpawnList.Add(new
                    {
                        name = spawnData.m_prefab.name,
                        biome = biomes,
                        enabled = spawnData.m_enabled,
                        min_lvl = spawnData.m_minLevel,
                        max_lvl = spawnData.m_maxLevel,
                        spawn_chance = spawnData.m_spawnChance
                    });
                }
            }
        }
        else
        {
            Logger.LogError("SpawnSystem instance is null");
        }

        /*foreach (var location in ZoneSystem.instance.m_locationLists)
        {
            var c = location.GetComponent<ZoneSystem.ZoneLocation>();
            if (c == null) continue;
        }*/
        WriteJson("spawnLocations.json", exportedSpawnList);

        foreach (var prefab in ZNetScene.instance.m_prefabs)
        {
            var c = prefab.GetComponent<Character>();
            if (c == null) continue;

            var drop = prefab.GetComponent<CharacterDrop>();
            var tame = prefab.GetComponent<Tameable>();

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
            mobList.Add(prefab.name, new
            {
                id = prefab.name,
                name = Localize(c.m_name),
                faction = c.m_faction.ToString(),
                boss = c.m_boss,

                // health & damage
                hp = c.m_health,
                damageModifiers = mods,
                tameable = tame != null

            });
        }

        WriteJson("mobs.json", mobList);
    }

    // ===== レシピ =====
    void DumpRecipes()
    {
        if (ObjectDB.instance == null)
        {
            Logger.LogWarning("ObjectDB null");
            return;
        }

        var list = new List<object>();
        var destructibles = new List<object>();

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
                    count = r.m_amount
                });
            }

            list.Add(new
            {
                result = recipe.m_item.name,
                amount = recipe.m_amount,
                requirements = resources
            });
        }

        foreach (var vegetation in ZoneSystem.instance.m_vegetation)
        {
            Logger.LogInfo(vegetation.m_name);
            Logger.LogInfo(vegetation.m_prefab.name);
            Logger.LogInfo(vegetation.m_prefab.ToString());
            Logger.LogInfo(vegetation.m_prefab.GetType());

            // すべてのコンポーネントを取得
            Component[] components = vegetation.m_prefab.GetComponents<Component>();

            foreach (var comp in components)
            {
                // これが「X」の正体（Type型）
                Type type = comp.GetType();

                Logger.LogInfo($"見つかったコンポーネント: {type.FullName}");
            }
        }

        // Smelter
        foreach (var prefab in ZNetScene.instance.m_prefabs)
        {
            var smelter = prefab.GetComponent<Smelter>();
            if (smelter == null) continue;

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
                    result = to,
                    amount = 1,
                    requirements = resources
                });
            }
        }

        WriteJson("recipes.json", list);
        WriteJson("destructibles.json", destructibles);
    }

    // ===== ドロップ =====
    void DumpDrops()
    {
        var list = new List<object>();

        foreach (var prefab in ZNetScene.instance.m_prefabs)
        {
            var cd = prefab.GetComponent<CharacterDrop>();
            if (cd == null) continue;

            var drops = cd.m_drops.Select(d => new
            {
                item = d.m_prefab.name,
                chance = d.m_chance,
                min = d.m_amountMin,
                max = d.m_amountMax
            }).ToList();

            list.Add(new
            {
                name = prefab.name,
                drops = drops
            });
        }

        WriteJson("drops.json", list);
    }

    // ===== ユーティリティ =====
    void WriteJson(string name, object data)
    {
        var path = Path.Combine(Paths.BepInExRootPath, name);
        File.WriteAllText(path, JsonConvert.SerializeObject(data, Newtonsoft.Json.Formatting.Indented));
        Logger.LogInfo($"Wrote {name}");
    }

    string Localize(string key)
    {
        if (Localization.instance == null) return key;
        return Localization.instance.Localize(key);
    }
}
