using UnityEngine;
using UnityEngine.Events;
using UnityEngine.XR.Interaction.Toolkit;

public class VRFollowButton : MonoBehaviour
{
    [Header("Button Settings")]
    [SerializeField] private Transform playerCamera;  // Reference to the VR camera
    [SerializeField] private float followDistance = 2f;  // Distance from player
    [SerializeField] private float smoothSpeed = 5f;  // Movement smoothing
    [SerializeField] private Vector3 offset = new Vector3(0.5f, -0.3f, 0f);  // Position offset from camera

    [Header("Button Interaction")]
    [SerializeField] private float pressDistance = 0.1f;  // How far button can be pressed
    private Vector3 initialPosition;
    private bool isPressed = false;

    public UnityEvent onButtonPress;  // Event to trigger when button is pressed

    private void Start()
    {
        if (playerCamera == null)
        {
            // Try to find the camera if not assigned
            playerCamera = Camera.main.transform;
        }
        initialPosition = transform.localPosition;
    }

    private void Update()
    {
        // Calculate target position relative to camera
        Vector3 targetPosition = playerCamera.position + 
                               (playerCamera.forward * followDistance) +
                               (playerCamera.right * offset.x) +
                               (playerCamera.up * offset.y);

        // Smoothly move button to target position
        transform.position = Vector3.Lerp(transform.position, targetPosition, smoothSpeed * Time.deltaTime);

        // Make button face the player
        transform.LookAt(playerCamera);
    }

    // Called by XR Interactor when button is pressed
    public void OnButtonPressed(SelectEnterEventArgs args)
    {
        if (!isPressed)
        {
            isPressed = true;
            // Move button inward
            transform.localPosition = initialPosition - (Vector3.forward * pressDistance);
            onButtonPress.Invoke();
        }
    }

    // Called by XR Interactor when button is released
    public void OnButtonReleased(SelectExitEventArgs args)
    {
        if (isPressed)
        {
            isPressed = false;
            // Return button to original position
            transform.localPosition = initialPosition;
        }
    }
}
