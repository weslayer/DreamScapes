using UnityEngine;
using UnityEngine.XR;
using UnityEngine.XR.Interaction.Toolkit;
using Unity.XR.CoreUtils;

public class VRMovementController : MonoBehaviour
{
    private XROrigin xrOrigin;
    private CharacterController character;
    public float speed = 1.0f;
    public XRNode inputSource;
    public float gravity = -9.81f;
    private float fallingSpeed;
    
    private void Start()
    {
        character = GetComponent<CharacterController>();
        xrOrigin = GetComponent<XROrigin>();
    }

    private void Update()
    {
        Vector2 inputAxis = InputDevices.GetDeviceAtXRNode(inputSource).TryGetFeatureValue(
            CommonUsages.primary2DAxis, out Vector2 value) ? value : Vector2.zero;

        Vector3 direction = new Vector3(inputAxis.x, 0, inputAxis.y);
        
        // Get head rotation for direction
        Vector3 headYaw = Quaternion.Euler(0, xrOrigin.Camera.transform.eulerAngles.y, 0) * direction;
        
        // Apply movement
        character.Move(headYaw * Time.deltaTime * speed);
        
        // Apply gravity
        if (character.isGrounded)
            fallingSpeed = 0;
        else
            fallingSpeed += gravity * Time.deltaTime;
            
        character.Move(Vector3.up * fallingSpeed * Time.deltaTime);
    }
}
