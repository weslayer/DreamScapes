using Dummiesman;
using System.IO;
using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
using Meta.WitAi;
using Meta.WitAi.Json;

public class SpawnIn : MonoBehaviour 
{
    private Vector3 spawnPosition = new Vector3(0f, 0f, 0f);
    private float spawnDistance = 0.5f;
    private UnityEngine.XR.Interaction.Toolkit.Interactors.IXRInteractor interactor;
    private bool isSpawning = false; // Prevent multiple simultaneous spawns
    private float spawnCooldown = 2f; // Time between spawns
    private float lastSpawnTime = 0f;
    private string status = "Click the A button to spawn an object";
    private VoiceService voiceService;

    void Start()
    {
        voiceService = GetComponent<VoiceService>();
        if (voiceService == null)
        {
            Debug.LogError("Could not find VoiceService!");
        }
    }

    void Awake()
    {
        interactor = GetComponent<UnityEngine.XR.Interaction.Toolkit.Interactors.IXRInteractor>();
    }

    void Update()
    {
        if (OVRInput.GetDown(OVRInput.Button.One, OVRInput.Controller.RTouch) && 
            !isSpawning && 
            Time.time - lastSpawnTime >= spawnCooldown)
        {
            voiceService.Activate();
        }
    }

    void OnFullTranscriptionString(string transcription)
    {
        string BASE_URL = "https://ngrok/generate/";
        string url = $"{BASE_URL}/{UnityWebRequest.EscapeURL(transcription)}";
    
        // Start loading object
        StartCoroutine(LoadFromURL(url));
    }

    void OnDestroy()
    {
        // No longer needed
    }

    IEnumerator LoadFromURL(string url)
    {
        status = "Loading object...";
        if (isSpawning) yield break;
        isSpawning = true;
        lastSpawnTime = Time.time;

        var cameraRig = GetComponentInParent<OVRCameraRig>();
        if (cameraRig == null)
        {
            Debug.LogError("Could not find OVRCameraRig!");
            isSpawning = false;
            yield break;
        }

        var centerEye = cameraRig.centerEyeAnchor;
        spawnPosition = centerEye.position + (centerEye.forward * spawnDistance);
        Debug.Log("Started loading object...");
        
        UnityWebRequest www = UnityWebRequest.Get(url);
        var operation = www.SendWebRequest();
        
        yield return operation;

        try
        {
            if (www.result == UnityWebRequest.Result.Success)
            {
                using (var textStream = new MemoryStream(System.Text.Encoding.UTF8.GetBytes(www.downloadHandler.text)))
                {
                    GameObject loadedObj = new OBJLoader().Load(textStream);
                    if (loadedObj != null)
                    {
                        var grabInteractable = loadedObj.AddComponent<UnityEngine.XR.Interaction.Toolkit.Interactables.XRGrabInteractable>();
                        var rigidbody = loadedObj.AddComponent<Rigidbody>();
                        rigidbody.useGravity = true;
                        
                        loadedObj.transform.position = spawnPosition;
                        loadedObj.transform.localScale = new Vector3(0.1f, 0.1f, 0.1f); // Scale down the object
                        loadedObj.transform.rotation = Quaternion.identity;
                        loadedObj.SetActive(true);
                        Debug.Log($"Object spawned successfully at: {loadedObj.transform.position}");
                    }
                    else
                    {
                        Debug.LogError("Failed to create object from OBJ file");
                    }
                }
            }
            else
            {
                Debug.LogError("Failed to download file: " + www.error);
            }
        }
        catch (System.Exception e)
        {
            Debug.LogError($"Error in spawn process: {e.Message}");
        }
        finally
        {
            www.Dispose();
            isSpawning = false;
            status = "Click the A button to spawn an object";
        }

        yield return new WaitForSeconds(0.1f);
    }
}
