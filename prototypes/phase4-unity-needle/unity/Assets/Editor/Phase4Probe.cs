// Editor tooling only. Runtime interaction is implemented in web/src/main.ts.
// Editor assembly references are explicit; validated with the installed exporter.
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

public static class Phase4Probe
{
    const string ScenePath = "Assets/Scenes/Phase4Probe.unity";
    static string WebPath => Path.GetFullPath(Path.Combine(Application.dataPath, "../../web"));

    [MenuItem("Auralis/Phase 4/1 - Create minimal scene")]
    public static void CreateScene()
    {
        if (!Application.isBatchMode && !EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
        if (File.Exists(ScenePath)) throw new InvalidOperationException("Phase4Probe.unity already exists; open and edit it instead of overwriting it.");
        Directory.CreateDirectory("Assets/Scenes");
        Directory.CreateDirectory("Assets/Materials");
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var export = new GameObject("NeedleExport").AddComponent<ExportInfo>();
        export.DirectoryName = "../web";
        export.ExportOnSave = false;
        var root = new GameObject("PlacementRoot");
        root.AddComponent<Needle.Engine.Components.WebARSessionRoot>();
        var probe = new GameObject("ProbeObject");
        probe.transform.SetParent(root.transform, false);
        var cube = GameObject.CreatePrimitive(PrimitiveType.Cube);
        cube.name = "Cube20cm";
        cube.transform.SetParent(probe.transform, false);
        cube.transform.localPosition = new Vector3(0, .1f, 0);
        cube.transform.localScale = Vector3.one * .2f;
        UnityEngine.Object.DestroyImmediate(cube.GetComponent<Collider>());
        var material = new Material(Shader.Find("Standard"));
        material.color = new Color(.278f, .835f, .757f);
        material.SetFloat("_Metallic", .1f);
        material.SetFloat("_Glossiness", .6f);
        AssetDatabase.CreateAsset(material, "Assets/Materials/Probe.mat");
        cube.GetComponent<Renderer>().sharedMaterial = material;
        var camera = new GameObject("Main Camera").AddComponent<Camera>();
        camera.tag = "MainCamera";
        camera.transform.position = new Vector3(.5f, .4f, -.7f);
        camera.transform.LookAt(cube.transform.position);
        camera.fieldOfView = 45; camera.nearClipPlane = .01f; camera.farClipPlane = 30;
        camera.clearFlags = CameraClearFlags.SolidColor;
        camera.backgroundColor = new Color(.043f, .067f, .106f);
        var controls = camera.gameObject.AddComponent<Needle.Engine.Components.OrbitControls>();
        controls.autoTarget = false; controls.lookAtTarget = cube.transform;
        var light = new GameObject("Key Light").AddComponent<Light>();
        light.type = LightType.Directional; light.intensity = 1.5f;
        light.transform.rotation = Quaternion.Euler(45, -30, 0);
        RenderSettings.ambientLight = new Color(.45f, .5f, .6f);
        EditorSceneManager.SaveScene(scene, ScenePath);
        AssetDatabase.SaveAssets();
        Debug.Log("PHASE4_SCENE_CREATED " + Application.unityVersion);
    }

    [MenuItem("Auralis/Phase 4/2 - Export with Needle")]
    public static void ExportScene()
    {
        if (SceneManager.GetActiveScene().path != ScenePath) throw new InvalidOperationException("Open Assets/Scenes/Phase4Probe.unity first.");
        EditorSceneManager.SaveScene(SceneManager.GetActiveScene());
        var target = Path.Combine(WebPath, "public/unity/Phase4Probe.glb");
        Directory.CreateDirectory(Path.GetDirectoryName(target));
        var asset = AssetDatabase.LoadAssetAtPath<SceneAsset>(ScenePath);
        var context = new ObjectExportContext(BuildContext.LocalDevelopment, asset, WebPath, target);
        // Needle returns a relative URI, not an absolute filesystem path.
        if (!Export.AsGlb(context, asset, out var outputUri, force: true) || !File.Exists(target))
            throw new InvalidOperationException("Needle export failed. Preserve the Editor log.");
        var bytes = File.ReadAllBytes(target);
        if (bytes.Length < 20 || System.Text.Encoding.ASCII.GetString(bytes, 0, 4) != "glTF")
            throw new InvalidDataException("Needle did not produce a binary glTF.");
        using var sha = SHA256.Create();
        var evidence = new ExportEvidence { unityVersion=Application.unityVersion, exporterVersion="5.1.12", timestampUtc=DateTime.UtcNow.ToString("o"), scene=ScenePath, sha256=BitConverter.ToString(sha.ComputeHash(bytes)).Replace("-", "").ToLowerInvariant(), bytes=bytes.Length };
        File.WriteAllText(Path.Combine(WebPath,"public/unity/export-evidence.json"), JsonUtility.ToJson(evidence,true));
        Debug.Log("PHASE4_NEEDLE_EXPORT_SUCCEEDED " + target + " " + evidence.sha256 + " uri=" + outputUri);
    }

    static void CaptureReference()
    {
        var camera = Camera.main;
        var rt = new RenderTexture(640, 480, 24);
        var image = new Texture2D(640, 480, TextureFormat.RGB24, false);
        var previous = RenderTexture.active;
        var previousTarget = camera.targetTexture;
        try
        {
            camera.targetTexture = rt;
            camera.Render();
            RenderTexture.active = rt;
            image.ReadPixels(new Rect(0, 0, 640, 480), 0, 0);
            image.Apply();
            var dir = Path.GetFullPath(Path.Combine(WebPath, "../evidence/phase42"));
            Directory.CreateDirectory(dir);
            File.WriteAllBytes(Path.Combine(dir, "unity-camera.png"), image.EncodeToPNG());
            Debug.Log("PHASE42_UNITY_REFERENCE_RENDERED");
        }
        finally
        {
            camera.targetTexture = previousTarget;
            RenderTexture.active = previous;
            UnityEngine.Object.DestroyImmediate(image);
            UnityEngine.Object.DestroyImmediate(rt);
        }
    }

    // Unity batch mode: omit -quit; this method exits after the synchronous export.
    public static void BuildAndExport()
    {
        try { if (!File.Exists(ScenePath)) CreateScene(); else EditorSceneManager.OpenScene(ScenePath); CaptureReference(); ExportScene(); EditorApplication.Exit(0); }
        catch (Exception e) { Debug.LogException(e); EditorApplication.Exit(1); }
    }
    [Serializable] class ExportEvidence { public string unityVersion, exporterVersion, timestampUtc, scene, sha256; public int bytes; }
}
