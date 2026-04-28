using BepInEx;
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.Rendering;

public class MobImageRenderer : MonoBehaviour
{
    // 保存先フォルダ (BepInEx/plugins/MobImages)
    private static readonly string OutputFolder = Path.Combine(Paths.PluginPath, "MobImages");

    // レンダリング用の解像度
    private const int ImageSize = 512;

    /// <summary>
    /// ZNetSceneに登録されているすべてのMob Prefabをレンダリングして保存します。
    /// コルーチンとして実行する必要があります。
    /// </summary>
    public IEnumerator DumpAllMobImagesCoroutine()
    {
        if (ZNetScene.instance == null)
        {
            Debug.LogError("ZNetScene is null");
            yield break;
        }

        if (!Directory.Exists(OutputFolder))
            Directory.CreateDirectory(OutputFolder);

        // =========================
        // 🔧 GLOBAL SETUP
        // =========================
        RenderSettings.ambientMode = AmbientMode.Flat;
        RenderSettings.ambientLight = new Color(0.6f, 0.6f, 0.6f);
        QualitySettings.shadows = ShadowQuality.Disable;

        int tempLayer = 31;

        // =========================
        // 📷 CAMERA
        // =========================
        GameObject camObj = new GameObject("IconCamera");
        Camera cam = camObj.AddComponent<Camera>();

        cam.clearFlags = CameraClearFlags.SolidColor;
        cam.backgroundColor = new Color(0, 0, 0, 0);
        cam.orthographic = true;
        cam.nearClipPlane = 0.01f;
        cam.farClipPlane = 100f;
        cam.cullingMask = 1 << tempLayer;

        RenderTexture rt = new RenderTexture(ImageSize, ImageSize, 24, RenderTextureFormat.ARGB32);
        rt.antiAliasing = 4;
        cam.targetTexture = rt;

        // =========================
        // 💡 LIGHTS (KEY / FILL / RIM)
        // =========================

        GameObject keyObj = new GameObject("KeyLight");
        Light key = keyObj.AddComponent<Light>();
        key.type = LightType.Directional;
        key.intensity = 3.0f;
        key.transform.rotation = Quaternion.Euler(50, -30, 0);

        GameObject fillObj = new GameObject("FillLight");
        Light fill = fillObj.AddComponent<Light>();
        fill.type = LightType.Directional;
        fill.intensity = 1.5f;
        fill.transform.rotation = Quaternion.Euler(0, 150, 0);

        GameObject rimObj = new GameObject("RimLight");
        Light rim = rimObj.AddComponent<Light>();
        rim.type = LightType.Directional;
        rim.intensity = 1.0f;
        rim.transform.rotation = Quaternion.Euler(-30, 180, 0);

        GameObject omniObj = new GameObject("OmniLight");
        Light omni = omniObj.AddComponent<Light>();

        omni.type = LightType.Point;
        omni.range = 10f;
        omni.intensity = 1.5f;
        omni.transform.position = Vector3.up * 2f;

        // =========================
        // LOOP PREFABS
        // =========================
        foreach (GameObject prefab in ZNetScene.instance.m_prefabs)
        {
            if (prefab.GetComponent<Character>() == null)
                continue;

            string name = prefab.name.Replace("(Clone)", "");
            Debug.Log($"Rendering {name}");

            GameObject instance = Instantiate(prefab, Vector3.zero, Quaternion.identity);
            SetLayerRecursively(instance, tempLayer);

            // =========================
            // 🔥 FIX SHADER / LIGHTING
            // =========================
            foreach (var r in instance.GetComponentsInChildren<Renderer>())
            {
                r.lightProbeUsage = UnityEngine.Rendering.LightProbeUsage.Off;
                r.reflectionProbeUsage = UnityEngine.Rendering.ReflectionProbeUsage.Off;

                foreach (var m in r.materials)
                {
                    m.shader = Shader.Find("Unlit/Texture");
                    m.EnableKeyword("_EMISSION");
                    m.SetColor("_EmissionColor", Color.white * 0.1f);
                    m.globalIlluminationFlags = MaterialGlobalIlluminationFlags.RealtimeEmissive;
                }
            }

            // =========================
            // 📏 BOUNDS AUTO FRAME
            // =========================
            Bounds b = CalculateBounds(instance);
            float size = Mathf.Max(b.size.x, b.size.y, b.size.z);

            cam.transform.position = b.center + new Vector3(0, 0, -size * 2.2f);
            cam.transform.LookAt(b.center);
            cam.orthographicSize = size * 0.6f;

            instance.transform.rotation = Quaternion.Euler(0, 150, 0);

            // =========================
            // FRAME SYNC
            // =========================
            yield return null;
            yield return new WaitForEndOfFrame();

            // =========================
            // RENDER
            // =========================
            RenderTexture.active = rt;

            Texture2D tex = new Texture2D(ImageSize, ImageSize, TextureFormat.ARGB32, false);
            tex.ReadPixels(new Rect(0, 0, ImageSize, ImageSize), 0, 0);
            tex.Apply();

            RenderTexture.active = null;

            byte[] png = tex.EncodeToPNG();
            File.WriteAllBytes(Path.Combine(OutputFolder, $"{name}.png"), png);

            DestroyImmediate(tex);
            DestroyImmediate(instance);

            yield return null;
        }

        // =========================
        // CLEANUP
        // =========================
        DestroyImmediate(camObj);
        DestroyImmediate(keyObj);
        DestroyImmediate(fillObj);
        DestroyImmediate(rimObj);
        DestroyImmediate(omniObj);

        rt.Release();
        DestroyImmediate(rt);

        Debug.Log("Done rendering icons");
    }

    // 子オブジェクト含めてレイヤーを変更するヘルパー
    private void SetLayerRecursively(GameObject obj, int layer)
    {
        obj.layer = layer;
        foreach (Transform child in obj.transform)
        {
            SetLayerRecursively(child.gameObject, layer);
        }
    }

    // オブジェクト全体のRendererからBoundsを計算する
    private Bounds CalculateBounds(GameObject obj)
    {
        Renderer[] renderers = obj.GetComponentsInChildren<Renderer>();
        if (renderers.Length == 0) return new Bounds(obj.transform.position, Vector3.zero);

        Bounds bounds = renderers[0].bounds;
        foreach (Renderer r in renderers)
        {
            bounds.Encapsulate(r.bounds);
        }
        return bounds;
    }
}