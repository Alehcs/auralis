// Editor authoring only: all meshes/materials are created in Unity and exported by Needle.
// Browser behavior uses supported Needle runtime components; this class is not a runtime script.
using System;
using System.IO;
using System.Security.Cryptography;
using Needle.Engine;
using Needle.Engine.Core;
using Needle.Engine.Gltf;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
using System.Collections.Generic;
using UnityGLTF;
using UnityGLTF.Plugins;

public static class Phase5Solar
{
    const string ScenePath = "Assets/Scenes/Phase5Solar.unity";
    const string AssetsPath = "Assets/Phase5";
    static string WebPath => Path.GetFullPath(Path.Combine(Application.dataPath, "../../web"));
    const float Radius = .42f;

    static string Hash(byte[] bytes) { using var s = SHA256.Create(); return BitConverter.ToString(s.ComputeHash(bytes)).Replace("-", "").ToLowerInvariant(); }
    static void SaveAsset(UnityEngine.Object asset, string path)
    {
        var existing = AssetDatabase.LoadAssetAtPath<UnityEngine.Object>(path);
        if (existing) { EditorUtility.CopySerialized(asset, existing); UnityEngine.Object.DestroyImmediate(asset); }
        else AssetDatabase.CreateAsset(asset, path);
    }
    static Texture2D Texture(string path)
    {
        var importer = (TextureImporter)AssetImporter.GetAtPath(path);
        importer.textureCompression = TextureImporterCompression.Uncompressed;
        importer.maxTextureSize = 1024;
        importer.mipmapEnabled = true;
        importer.sRGBTexture = true;
        importer.alphaSource = TextureImporterAlphaSource.FromInput;
        importer.wrapMode = TextureWrapMode.Clamp;
        importer.filterMode = FilterMode.Bilinear;
        importer.SaveAndReimport();
        return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
    }
    static Material Material(string name, string image = null, bool transparent = false)
    {
        var mat = new Material(Shader.Find(transparent ? "Unlit/Transparent" : "Unlit/Texture"));
        mat.name = name;
        if (image != null) mat.mainTexture = Texture(image);
        SaveAsset(mat, AssetsPath + "/" + name + ".mat");
        return AssetDatabase.LoadAssetAtPath<Material>(AssetsPath + "/" + name + ".mat");
    }
    // Deterministic cellular granulation with fine/coarse modulation; entirely illustrative.
    static float Hash2(int x, int y, int seed)
    {
        unchecked { uint v = (uint)(x * 374761393 + y * 668265263 + seed * 1274126177); v = (v ^ (v >> 13)) * 1274126177; return (v ^ (v >> 16)) / (float)uint.MaxValue; }
    }
    static float Cell(float x, float y)
    {
        int ix = Mathf.FloorToInt(x), iy = Mathf.FloorToInt(y);
        float first = 100, second = 100;
        for (int j = -1; j <= 1; j++) for (int i = -1; i <= 1; i++)
        {
            float dx = ix + i + Hash2(ix + i, iy + j, 53) - x;
            float dy = iy + j + Hash2(ix + i, iy + j, 97) - y;
            float d = dx * dx + dy * dy;
            if (d < first) { second = first; first = d; } else if (d < second) second = d;
        }
        return Mathf.SmoothStep(0, 1, Mathf.Clamp01((Mathf.Sqrt(second) - Mathf.Sqrt(first)) * 5));
    }
    static void BakeIllustration()
    {
        Directory.CreateDirectory(AssetsPath);
        const int size = 1024;
        var tex = new Texture2D(size, size, TextureFormat.RGBA32, false);
        var pixels = new Color32[size * size];
        for (int y = 0; y < size; y++) for (int x = 0; x < size; x++)
        {
            float u = (x + .5f) / size, v = (y + .5f) / size;
            float r2 = Mathf.Pow((u - .5f) * 2, 2) + Mathf.Pow((v - .5f) * 2, 2);
            float limb = .48f + .52f * Mathf.Pow(Mathf.Clamp01(1 - r2), .28f);
            float broad = Mathf.PerlinNoise(u * 13 + 7.2f, v * 13 + 2.1f);
            float fine = Mathf.PerlinNoise(u * 390, v * 390);
            float granule = Cell(u * 160 + 3, v * 160 + 11);
            float level = (.48f + .27f * granule + .18f * broad + .07f * fine) * limb;
            // Restrained warm photospheric palette; no spots, loops, flares or neon bloom.
            pixels[y * size + x] = new Color(Mathf.Clamp01(level * 1.25f), Mathf.Pow(level, 1.35f) * .81f, Mathf.Pow(level, 2.0f) * .31f, 1);
        }
        tex.SetPixels32(pixels); tex.Apply();
        File.WriteAllBytes(AssetsPath + "/solar-illustration.png", tex.EncodeToPNG());
        UnityEngine.Object.DestroyImmediate(tex);
        // Small transparent limb, baked in Unity; no postprocess dependency in AR.
        tex = new Texture2D(256, 256, TextureFormat.RGBA32, false);
        pixels = new Color32[256 * 256];
        for (int y = 0; y < 256; y++) for (int x = 0; x < 256; x++)
        {
            float r = new Vector2((x + .5f) / 128 - 1, (y + .5f) / 128 - 1).magnitude;
            float a = r < .87f ? 0 : .15f * Mathf.Exp(-Mathf.Pow((r - .89f) / .027f, 2));
            pixels[y * 256 + x] = new Color(.94f, .52f, .16f, a);
        }
        tex.SetPixels32(pixels); tex.Apply();
        File.WriteAllBytes(AssetsPath + "/corona-illustration.png", tex.EncodeToPNG());
        UnityEngine.Object.DestroyImmediate(tex);
        tex = new Texture2D(4, 4, TextureFormat.RGB24, false);
        for (int y = 0; y < 4; y++) for (int x = 0; x < 4; x++) tex.SetPixel(x, y, new Color(.12f, .135f, .15f));
        tex.Apply(); File.WriteAllBytes(AssetsPath + "/no-data.png", tex.EncodeToPNG());
        UnityEngine.Object.DestroyImmediate(tex);
        AssetDatabase.Refresh();
    }
    static Mesh Hemisphere(string name, bool front)
    {
        const int rings = 48, segments = 128;
        var vertices = new Vector3[(rings + 1) * (segments + 1)];
        var uv = new Vector2[vertices.Length];
        var indices = new int[rings * segments * 6];
        for (int i = 0; i <= rings; i++) for (int j = 0; j <= segments; j++)
        {
            float theta = i * Mathf.PI * .5f / rings, phi = j * 2 * Mathf.PI / segments;
            float x = Mathf.Sin(theta) * Mathf.Cos(phi), y = Mathf.Sin(theta) * Mathf.Sin(phi);
            int at = i * (segments + 1) + j;
            vertices[at] = new Vector3(x, y, (front ? -1 : 1) * Mathf.Cos(theta)) * Radius;
            uv[at] = new Vector2((front ? x : -x) * .5f + .5f, y * .5f + .5f);
        }
        int k = 0;
        for (int i = 0; i < rings; i++) for (int j = 0; j < segments; j++)
        {
            int a = i * (segments + 1) + j, b = a + segments + 1;
            int[] face = front ? new[]{a, a+1, b, a+1, b+1, b} : new[]{a, b, a+1, a+1, b, b+1};
            foreach (var idx in face) indices[k++] = idx;
        }
        var mesh = new Mesh {name=name, vertices=vertices, uv=uv, triangles=indices};
        mesh.RecalculateNormals(); mesh.RecalculateBounds();
        SaveAsset(mesh, AssetsPath + "/" + name + ".asset");
        return AssetDatabase.LoadAssetAtPath<Mesh>(AssetsPath + "/" + name + ".asset");
    }
    static GameObject MeshObject(string name, Transform parent, Mesh mesh, Material material)
    {
        var go = new GameObject(name); go.transform.SetParent(parent, false);
        go.AddComponent<MeshFilter>().sharedMesh = mesh;
        go.AddComponent<MeshRenderer>().sharedMaterial = material;
        return go;
    }
    static GameObject Quad(string name, Transform parent, Material material, float size, float z)
    {
        var go = GameObject.CreatePrimitive(PrimitiveType.Quad); go.name = name;
        go.transform.SetParent(parent, false); go.transform.localScale = Vector3.one * size;
        go.transform.localPosition = new Vector3(0, 0, z);
        UnityEngine.Object.DestroyImmediate(go.GetComponent<Collider>());
        go.GetComponent<Renderer>().sharedMaterial = material; return go;
    }
    [MenuItem("Auralis/Phase 5/Create solar state scene")]
    public static void CreateScene()
    {
        if (File.Exists(ScenePath)) throw new InvalidOperationException("Phase5 scene exists. Open it, or explicitly use RebuildAndExport for Phase5 only.");
        BakeIllustration();
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var export = new GameObject("NeedleExport").AddComponent<ExportInfo>();
        export.DirectoryName = "../web"; export.ExportOnSave = false;
        var root = new GameObject("Phase5Placement");
        var ar = root.AddComponent<Needle.Engine.Components.WebARSessionRoot>();
        var content = new GameObject("SolarState"); content.transform.SetParent(root.transform, false);
        content.transform.localPosition = new Vector3(0, .5f, 0);
        var sun = new GameObject("SolarIllustration"); sun.transform.SetParent(content.transform, false);
        MeshObject("IllustrativeFront", sun.transform, Hemisphere("FrontHemisphere", true), Material("SolarUnlit", AssetsPath + "/solar-illustration.png"));
        MeshObject("UnobservedBack", sun.transform, Hemisphere("BackHemisphere", false), Material("NoData", AssetsPath + "/Data/no-data-label.png"));
        Quad("SubtleCorona", sun.transform, Material("CoronaUnlit", AssetsPath + "/corona-illustration.png", true), Radius * 2 / .89f, .015f);
        foreach (var name in new[]{"magnetogram", "bplus", "bminus"})
        {
            // Unlit data has opaque alpha. The scoped export callback below
            // explicitly forces PNG; the shader alone does not prevent JPEG.
            var layer = Quad("Layer_" + name, content.transform, Material("Data_" + name, AssetsPath + "/Data/" + name + ".png", true), .9f, 0);
            layer.SetActive(false);
        }
        // Reference back is a separate opaque unobserved surface, never a mirrored observation.
        var back = Quad("ReferenceBack", content.transform, Material("ReferenceNoData", AssetsPath + "/Data/no-data-label.png"), .9f, .002f);
        back.transform.localRotation = Quaternion.Euler(0, 180, 0); back.SetActive(false);
        var camera = new GameObject("Phase5 Camera").AddComponent<Camera>(); camera.tag = "MainCamera";
        camera.transform.position = new Vector3(0, .5f, -2.0f); camera.transform.LookAt(content.transform);
        camera.fieldOfView = 36; camera.nearClipPlane = .02f; camera.farClipPlane = 30;
        camera.clearFlags = CameraClearFlags.SolidColor; camera.backgroundColor = new Color(.025f, .03f, .04f, 0);
        var orbit = camera.gameObject.AddComponent<Needle.Engine.Components.OrbitControls>();
        orbit.autoTarget = false; orbit.lookAtTarget = content.transform;
        EditorSceneManager.SaveScene(scene, ScenePath); AssetDatabase.SaveAssets();
        Debug.Log("PHASE5_UNITY_SCENE_CREATED");
    }
    static void Capture()
    {
        var camera = Camera.main; var rt = new RenderTexture(1000, 850, 24);
        var image = new Texture2D(1000, 850, TextureFormat.RGB24, false);
        var previous = RenderTexture.active;
        try {
            camera.targetTexture = rt; camera.Render(); RenderTexture.active = rt;
            image.ReadPixels(new Rect(0, 0, 1000, 850), 0, 0); image.Apply();
            File.WriteAllBytes(Path.Combine(WebPath, "../evidence/phase5/unity-solar.png"), image.EncodeToPNG());
        } finally { camera.targetTexture = null; RenderTexture.active = previous; UnityEngine.Object.DestroyImmediate(image); UnityEngine.Object.DestroyImmediate(rt); }
    }
    static void ExportScene()
    {
        var target = Path.Combine(WebPath, "public/phase5/Phase5Solar.glb");
        Directory.CreateDirectory(Path.GetDirectoryName(target));
        var asset = AssetDatabase.LoadAssetAtPath<SceneAsset>(ScenePath);
        var context = new ObjectExportContext(BuildContext.LocalDevelopment, asset, WebPath, target);
        var settings = GLTFSettings.GetOrCreateSettings();
        var previousPlugins = settings.ExportPlugins;
        var lossless = ScriptableObject.CreateInstance<Phase5LosslessPlugin>();
        try {
            settings.ExportPlugins = new List<GLTFExportPlugin>(previousPlugins) { lossless };
            if (!Export.AsGlb(context, asset, out var uri, force:true) || !File.Exists(target)) throw new InvalidOperationException("Needle Phase5 export failed");
        } finally { settings.ExportPlugins = previousPlugins; UnityEngine.Object.DestroyImmediate(lossless); }
        var bytes = File.ReadAllBytes(target);
        var evidence = new Evidence {unityVersion=Application.unityVersion, exporterVersion="5.1.12", timestampUtc=DateTime.UtcNow.ToString("o"), scene=ScenePath, bytes=bytes.Length, sha256=Hash(bytes), sceneSha256=Hash(File.ReadAllBytes(ScenePath)), authoringSha256=Hash(File.ReadAllBytes("Assets/Editor/Phase5Solar.cs")), stateSha256=Hash(File.ReadAllBytes(Path.Combine(WebPath,"public/phase5/state.json"))), solarTextureSha256=Hash(File.ReadAllBytes(AssetsPath+"/solar-illustration.png"))};
        File.WriteAllText(Path.Combine(WebPath, "public/phase5/export-evidence.json"), JsonUtility.ToJson(evidence, true));
        Debug.Log("PHASE5_NEEDLE_EXPORT_SUCCEEDED " + evidence.sha256 + " bytes=" + evidence.bytes);
    }
    public static void BuildAndExport()
    {
        try { Directory.CreateDirectory(Path.Combine(WebPath, "../evidence/phase5")); if (!File.Exists(ScenePath)) CreateScene(); else EditorSceneManager.OpenScene(ScenePath); Capture(); ExportScene(); EditorApplication.Exit(0); }
        catch (Exception e) { Debug.LogException(e); EditorApplication.Exit(1); }
    }
    // Explicitly scoped refresh of generated Phase5 assets. Never touches the Phase4 scene.
    public static void RebuildAndExport()
    {
        try { if (File.Exists(ScenePath)) AssetDatabase.DeleteAsset(ScenePath); BuildAndExport(); }
        catch (Exception e) { Debug.LogException(e); EditorApplication.Exit(1); }
    }
    [Serializable] class Evidence { public string unityVersion, exporterVersion, timestampUtc, scene, sha256, sceneSha256, authoringSha256, stateSha256, solarTextureSha256; public int bytes; }
}

// Public exporter callback, enabled only for this export. No package patches or
// persistent project-setting changes. PNG avoids JPEG ringing in polarity data.
public class Phase5LosslessPlugin : GLTFExportPlugin
{
    public override string DisplayName => "Auralis Phase5 lossless scientific textures";
    public override bool EnabledByDefault => false;
    public override GLTFExportPluginContext CreateInstance(UnityGLTF.ExportContext context) => new LosslessContext();
    class LosslessContext : GLTFExportPluginContext
    {
        public override void BeforeTextureExport(GLTFSceneExporter exporter, ref GLTFSceneExporter.UniqueTexture texture, string slot)
        {
            var path = AssetDatabase.GetAssetPath(texture.Texture);
            if (!path.StartsWith("Assets/Phase5/Data/", StringComparison.Ordinal)) return;
            texture.ExportSettings.alphaMode = GLTFSceneExporter.TextureExportSettings.AlphaMode.Always;
            Debug.Log("PHASE5_LOSSLESS_TEXTURE " + path);
        }
    }
}
