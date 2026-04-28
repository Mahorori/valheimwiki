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
    }
}
