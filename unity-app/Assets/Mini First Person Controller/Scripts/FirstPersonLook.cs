using UnityEngine;
using Unity.XR.CoreUtils;

public class FirstPersonLook : MonoBehaviour
{
    [SerializeField] Transform character;
    public float smoothing = 1.5f;

    private XROrigin xrOrigin;
    private Transform xrCamera;

    void Reset()
    {
        // Get the character from the FirstPersonMovement in parents.
        character = GetComponentInParent<FirstPersonMovement>().transform;
    }

    void Start()
    {
        if (character == null)
        {
            character = GetComponentInParent<FirstPersonMovement>()?.transform;
        }

        // Get XR components
        xrOrigin = FindFirstObjectByType<XROrigin>();
        if (xrOrigin != null)
        {
            xrCamera = xrOrigin.Camera.transform;
        }
    }

    void Update()
    {
        if (character == null || xrCamera == null) return;

        // Use headset rotation for both looking and character rotation
        transform.rotation = xrCamera.rotation;
        
        // Update character rotation to match horizontal view direction
        Vector3 flatForward = Vector3.ProjectOnPlane(xrCamera.forward, Vector3.up).normalized;
        if (flatForward.sqrMagnitude > 0.01f)
        {
            character.rotation = Quaternion.LookRotation(flatForward);
        }
    }
}
