using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;
using ModTool.Interface;

public class ServerInfo : ModBehaviour {
	public string server = "https://split-timer.nohumanman.com/";
	[System.NonSerialized]
	public bool isOnline = true;
	private static ServerInfo _instance;
	public static ServerInfo Instance { get { return _instance; } }
	private void Awake()
	{
		// used to keep singleton
		if (_instance != null && _instance != this)
		{
			this.enabled = false;
		}
		else {
			_instance = this;
		}
	}
	void Start () {
		StartCoroutine(CoroCheckIfOnline());
	}
	
	IEnumerator CoroCheckIfOnline(){
		while (true){
			using (UnityWebRequest webRequest = UnityWebRequest.Get(server))
			{
				yield return webRequest.SendWebRequest();
				if (webRequest.responseCode != 200){
					if (isOnline != false){
						Debug.LogWarning("Server Disconnected!");
					}
					isOnline = false;
				}
				else{
					if (isOnline != true){
						Debug.LogWarning("Server Reconnected!");
					}
					isOnline = true;
				}
			}
			yield return new WaitForSeconds(5f);
		}
	}
}
