using UnityEngine;

public class CanvasFollowVR : MonoBehaviour 
{
    private Canvas canvas;
    private RectTransform canvasRect;
    [SerializeField] private float offsetX = 0f;  // Adjust to position from left/right
    [SerializeField] private float offsetY = 0f;  // Adjust to position from bottom
    [SerializeField] private Camera vrCamera;     // Reference to your VR camera

    void Start()
    {
        canvas = GetComponent<Canvas>();
        canvasRect = GetComponent<RectTransform>();
        
        // Make sure the canvas is in screen space - camera mode
        canvas.renderMode = RenderMode.ScreenSpaceCamera;
        canvas.worldCamera = vrCamera;
        
        // Set the canvas to overlay mode if you want it to always be visible
        canvas.sortingOrder = 100; // Ensures it renders on top of other UI elements
    }

    void Update()
    {
        // Position the canvas in the bottom corner
        if (canvasRect != null)
        {
            // Get the canvas size
            Vector2 canvasSize = canvasRect.sizeDelta;
            
            // Calculate the position (bottom corner)
            float posX = -Screen.width/2 + canvasSize.x/2 + offsetX;  // Left corner
            float posY = -Screen.height/2 + canvasSize.y/2 + offsetY; // Bottom corner
            
            canvasRect.anchoredPosition = new Vector2(posX, posY);
        }
    }
}