using BepInEx.Logging;
using HarmonyLib;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Threading.Tasks;

namespace MyFirstPlugin
{
    internal class Patch
    {
        [HarmonyPatch(typeof(SpawnSystem), "Awake")]
        public static class SpawnSystemAwakePatch
        {
            public static SpawnSystem CurrentInstance;

            static void Postfix(SpawnSystem __instance)
            {
                // 最後にAwakeされたインスタンスを保持
                CurrentInstance = __instance;
            }
        }

        [HarmonyPatch(typeof(EntryPointSceneLoader), "Start")]
        public static class EntryPointSceneLoaderPatch
        {
            static bool Prefix(EntryPointSceneLoader __instance)
            {
                // https://www.valheimgame.com/ja/support/modding-faq-for-the-asset-bundle-update-0-217-40
                SoftReferenceableAssets.Runtime.MakeAllAssetsLoadable();

                // - returns a boolean that controls if original is executed (true) or not (false)
                return true;
            }
        }
    }
}
