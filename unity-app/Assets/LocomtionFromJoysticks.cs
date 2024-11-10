using UnityEngine;

public class JoystickLocomotion : MonoBehaviour
{
    public float speed = 2.0f;
    private Transform cameraRig;
    private Transform centerEyeAnchor;

    void Start()
    {
        // Find the OVRCameraRig in parent hierarchy
        cameraRig = transform.parent.parent;
        if (cameraRig == null)
        {
            Debug.LogError("Cannot find OVRCameraRig!");
            return;
        }

        // Get the center eye anchor for direction reference
        centerEyeAnchor = cameraRig.Find("TrackingSpace/CenterEyeAnchor");
        if (centerEyeAnchor == null)
        {
            Debug.LogError("Cannot find CenterEyeAnchor!");
            return;
        }
    }

    void Update()
    {
        if (cameraRig == null || centerEyeAnchor == null) return;

        // Read input from left thumbstick
        Vector2 input = OVRInput.Get(OVRInput.Axis2D.PrimaryThumbstick);

        // Get the camera's forward and right vectors
        Vector3 forward = centerEyeAnchor.forward;
        Vector3 right = centerEyeAnchor.right;

        // Project to horizontal plane
        forward.y = 0;
        right.y = 0;
        forward.Normalize();
        right.Normalize();

        // Calculate and apply movement
        Vector3 movement = (forward * input.y + right * input.x) * speed * Time.deltaTime;
        cameraRig.position += movement;
    }
}
