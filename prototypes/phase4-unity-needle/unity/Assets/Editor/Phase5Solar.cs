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
        importer.maxTextureSize = 2048;
        importer.mipmapEnabled = true;
        importer.sRGBTexture = true;
        importer.alphaSource = TextureImporterAlphaSource.FromInput;
        importer.wrapMode = path.EndsWith("solar-illustration.png") ? TextureWrapMode.Repeat : TextureWrapMode.Clamp;
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
    // Procedural full-sphere illustration. Evaluating in 3D avoids a longitude
    // seam or a different material on the far side. No observational features.
    static float Noise(Vector3 p) => (Mathf.PerlinNoise(p.x + 17.1f, p.y + p.z * .37f + 23.7f)
        + Mathf.PerlinNoise(p.y + 51.3f, p.z + p.x * .41f + 19.6f)
        + Mathf.PerlinNoise(p.z + 11.5f, p.x + p.y * .29f + 71.2f)) / 3f;
    static float Fbm(Vector3 p)
    {
        float v = 0, a = .57f;
        for (int i = 0; i < 4; i++) { v += a * Noise(p); p = p * 2.07f + new Vector3(7.3f, 1.8f, 3.7f); a *= .48f; }
        return v;
    }
    static Vector3 Warp(Vector3 p) => new Vector3(Noise(p), Noise(p + Vector3.one * 19), Noise(p + Vector3.one * 37)) - Vector3.one * .5f;
    static void BakeIllustration()
    {
        Directory.CreateDirectory(AssetsPath);
        const int width = 2048, height = 1024;
        var tex = new Texture2D(width, height, TextureFormat.RGBA32, false);
        var pixels = new Color32[width * height];
        for (int y = 0; y < height; y++) for (int x = 0; x < width; x++)
        {
            // Endpoints intentionally identical: the texture is continuous at u=0/1.
            float longitude = x / (float)(width - 1) * Mathf.PI * 2;
            float latitude = (y / (float)(height - 1) - .5f) * Mathf.PI;
            var n = new Vector3(Mathf.Cos(latitude) * Mathf.Cos(longitude), Mathf.Sin(latitude), Mathf.Cos(latitude) * Mathf.Sin(longitude));
            var p = n * 5.2f;
            var w = Warp(p * 1.7f);
            float broad = Fbm(p + w * 1.6f);
            float filament = 1 - Mathf.Abs(Fbm(n * 32 + Warp(p * 2.3f) * 7) * 2 - 1);
            filament = Mathf.Pow(Mathf.Clamp01((filament - .62f) / .36f), 3.2f);
            float grain = Noise(n * 235 + Warp(n * 57) * 3);
            float cells = Mathf.SmoothStep(0, 1, Mathf.Clamp01((Noise(n * 96 + w * 4) - .32f) * 2.7f));
            float network = Mathf.SmoothStep(0, 1, Mathf.Clamp01((broad - .44f) * 7));
            float level = Mathf.Clamp01(.12f + .31f * cells + .16f * grain + .24f * filament + .25f * network);
            var color = Color.Lerp(new Color(.23f, .025f, .004f), new Color(.96f, .34f, .035f), Mathf.SmoothStep(0, 1, level * 1.5f));
            color = Color.Lerp(color, new Color(1, .75f, .25f), Mathf.SmoothStep(0, 1, (level - .43f) * 2.7f));
            color = Color.Lerp(color, new Color(1, .95f, .72f), Mathf.SmoothStep(0, 1, (level - .70f) * 4));
            pixels[y * width + x] = color;
        }
        tex.SetPixels32(pixels); tex.Apply();
        File.WriteAllBytes(AssetsPath + "/solar-illustration.png", tex.EncodeToPNG());
        UnityEngine.Object.DestroyImmediate(tex);
        const int size = 512;
        tex = new Texture2D(size, size, TextureFormat.RGBA32, false);
        pixels = new Color32[size * size];
        for (int y = 0; y < size; y++) for (int x = 0; x < size; x++)
        {
            var q = new Vector2((x + .5f) / size * 2 - 1, (y + .5f) / size * 2 - 1);
            float r = q.magnitude, angle = Mathf.Atan2(q.y, q.x);
            float directional = Noise(new Vector3(Mathf.Cos(angle) * 9, Mathf.Sin(angle) * 9, r * 12));
            float edge = r - .70f;
            float wisps = .5f + .5f * Mathf.Pow(Mathf.Max(0, Mathf.Sin(angle * 53 + directional * 14)), 3);
            float a = edge < -.015f ? 0 : Mathf.SmoothStep(0, 1, (edge + .015f) / .018f)
                * (.45f * Mathf.Exp(-Mathf.Max(0, edge) * 25) + .25f * wisps * Mathf.Exp(-Mathf.Max(0, edge) * 10));
            a *= 1 - Mathf.SmoothStep(0, 1, Mathf.InverseLerp(.90f, 1, r));
            pixels[y * size + x] = new Color(1, .47f + directional * .18f, .10f, a);
        }
        tex.SetPixels32(pixels); tex.Apply();
        File.WriteAllBytes(AssetsPath + "/corona-illustration.png", tex.EncodeToPNG());
        UnityEngine.Object.DestroyImmediate(tex);
        AssetDatabase.Refresh();
    }
    static Mesh Sphere()
    {
        const int rings = 96, segments = 128;
        var vertices = new Vector3[(rings + 1) * (segments + 1)];
        var normals = new Vector3[vertices.Length];
        var uv = new Vector2[vertices.Length];
        var indices = new int[rings * segments * 6];
        for (int i = 0; i <= rings; i++) for (int j = 0; j <= segments; j++)
        {
            float theta = i * Mathf.PI / rings, phi = j * 2 * Mathf.PI / segments;
            int at = i * (segments + 1) + j;
            normals[at] = new Vector3(Mathf.Sin(theta) * Mathf.Cos(phi), Mathf.Cos(theta), Mathf.Sin(theta) * Mathf.Sin(phi));
            vertices[at] = normals[at] * Radius;
            uv[at] = new Vector2(j / (float)segments, 1 - i / (float)rings);
        }
        int k = 0;
        for (int i = 0; i < rings; i++) for (int j = 0; j < segments; j++)
        {
            int a = i * (segments + 1) + j, b = a + segments + 1;
            foreach (var idx in new[]{a, a+1, b, a+1, b+1, b}) indices[k++] = idx;
        }
        var mesh = new Mesh {name="ContinuousSphere", vertices=vertices, normals=normals, uv=uv, triangles=indices};
        mesh.RecalculateBounds(); SaveAsset(mesh, AssetsPath + "/ContinuousSphere.asset");
        return AssetDatabase.LoadAssetAtPath<Mesh>(AssetsPath + "/ContinuousSphere.asset");
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
        MeshObject("IllustrativeSphere", sun.transform, Sphere(), Material("SolarUnlit", AssetsPath + "/solar-illustration.png"));
        var corona = Quad("SubtleCorona", sun.transform, Material("CoronaUnlit", AssetsPath + "/corona-illustration.png", true), Radius * 2 / .70f, 0);
        var look = corona.AddComponent<Needle.Engine.Components.LookAt>();
        look.invertForward = true; look.keepUpDirection = false; look.copyTargetRotation = true;
        foreach (var name in new[]{"magnetogram", "bplus", "bminus"})
        {
            var layer = Quad("Layer_" + name, content.transform, Material("Data_" + name, AssetsPath + "/Data/" + name + ".png", true), .9f, 0);
            var face = layer.AddComponent<Needle.Engine.Components.LookAt>();
            face.invertForward = true; face.keepUpDirection = false; face.copyTargetRotation = true;
            layer.SetActive(false);
        }
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
            File.WriteAllBytes(Path.Combine(WebPath, "../evidence/visual-polish/unity-solar.png"), image.EncodeToPNG());
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
        try { Directory.CreateDirectory(Path.Combine(WebPath, "../evidence/visual-polish")); if (!File.Exists(ScenePath)) CreateScene(); else EditorSceneManager.OpenScene(ScenePath); Capture(); ExportScene(); EditorApplication.Exit(0); }
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
            if (!path.StartsWith("Assets/Phase5/Data/", StringComparison.Ordinal) && !path.EndsWith("solar-illustration.png")) return;
            texture.ExportSettings.alphaMode = GLTFSceneExporter.TextureExportSettings.AlphaMode.Always;
            Debug.Log("PHASE5_LOSSLESS_TEXTURE " + path);
        }
    }
}
