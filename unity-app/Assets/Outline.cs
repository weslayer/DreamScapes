using UnityEngine;

public class Outline : MonoBehaviour
{
    public Color OutlineColor = Color.yellow;
    public float OutlineWidth = 7.0f;
    
    private Material outlineMaterial;
    private Renderer[] renderers;
    private Material[] originalMaterials;
    private bool isInitialized = false;

    void Awake()
    {
        Initialize();
    }

    private void Initialize()
    {
        if (isInitialized) return;
        
        renderers = GetComponentsInChildren<Renderer>();
        if (renderers.Length > 0)
        {
            // Store original materials
            originalMaterials = new Material[renderers.Length];
            for (int i = 0; i < renderers.Length; i++)
            {
                originalMaterials[i] = renderers[i].material;
            }

            // Create outline material
            outlineMaterial = new Material(Shader.Find("Standard"));
            outlineMaterial.color = new Color(OutlineColor.r, OutlineColor.g, OutlineColor.b, 0.5f);
        }
        
        isInitialized = true;
    }

    public void OnEnable()
    {
        if (!isInitialized)
        {
            Initialize();
        }
        ApplyOutline();
    }

    public void OnDisable()
    {
        RestoreOriginalMaterials();
    }

    private void ApplyOutline()
    {
        if (!isInitialized || renderers == null) return;
        
        foreach (var renderer in renderers)
        {
            if (renderer != null)
            {
                renderer.material = outlineMaterial;
            }
        }
    }

    private void RestoreOriginalMaterials()
    {
        if (!isInitialized || renderers == null) return;
        
        for (int i = 0; i < renderers.Length; i++)
        {
            if (renderers[i] != null && originalMaterials[i] != null)
            {
                renderers[i].material = originalMaterials[i];
            }
        }
    }
}