﻿using System;
using System.Collections;
using System.Collections.Generic;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;
using ModLoaderSolution;

namespace SplitTimer{
	[RequireComponent(typeof(PlayerInfo))]
	[RequireComponent(typeof(MapInfo))]
	public class NetClient : MonoBehaviour {
		public static NetClient Instance { get; private set; }
		public RidersGate[] ridersGates;
		private TcpClient socketConnection;
		private Thread clientReceiveThread;
		bool PlayerCollision = false;
		List<string> messages = new List<string>();
		public int port = 65432;
		public string ip = "18.132.81.187";
		void Awake(){
			if (Instance != null && Instance != this) 
				Destroy(this); 
			else
				Instance = this;
			this.gameObject.AddComponent<Utilities>();
		}
		void Start () {
			Debug.Log("connecting to tcp server");
			ConnectToTcpServer();
			ridersGates = GameObject.FindObjectsOfType<RidersGate>();
		}
		void Update()
        {
			if (Input.GetKey(KeyCode.LeftShift) && Input.GetKeyDown(KeyCode.C))
            {
				Physics.IgnoreLayerCollision(8, 8, PlayerCollision);
				PlayerCollision = !PlayerCollision;
			}
			foreach(string message in messages)
            {
                try
                {
					MessageRecieved(message);
				}
				catch (Exception ex)
                {
					Debug.Log(ex);
                }
            }
			messages.Clear();
        }
		private void ConnectToTcpServer () {
			try {
				clientReceiveThread = new Thread (new ThreadStart(ListenForData));
				clientReceiveThread.IsBackground = true;
				clientReceiveThread.Start();
			}
			catch (Exception e) {
				Debug.Log("On client connect exception " + e); 		
			}
		}
		private void ListenForData() {
			try {
				socketConnection = new TcpClient(ip, port);
				Byte[] bytes = new Byte[1024];
				while (true) {
					using (NetworkStream stream = socketConnection.GetStream()) { 					
						int length; 								
						while ((length = stream.Read(bytes, 0, bytes.Length)) != 0) { 						
							var incommingData = new byte[length]; 						
							Array.Copy(bytes, 0, incommingData, 0, length); 						
							string serverMessage = Encoding.ASCII.GetString(incommingData);
							string[] serverMessages = serverMessage.Split('\n');
							foreach(string message in serverMessages)
							{
								messages.Add(message);
							}
						}
					}
				}
			}
			catch (SocketException socketException) {             
				Debug.Log("Socket exception: " + socketException);         
			}
		}
		private void MessageRecieved(string message) {
			Debug.Log(message);
			if (message == "")
				return;
			if (message == "SUCCESS") {
				PlayerInfo.Instance.NetStart();
			}
			if (message.StartsWith("BANNED")) {
				string[] ban = message.Split('|');
				// string reason = ban[1];
				string method = ban[2];
				if (method == "CRASH")
					while (true) { }
				if (method == "CLOSE")
					Application.Quit();
			}
			if (message.StartsWith("RIDERSGATE")) {
				Debug.Log("Riderz Gate");
				string[] gate = message.Split('|');
				float randomTime = float.Parse(gate[1]);
				foreach (RidersGate ridersGate in ridersGates) {
					Debug.Log("GATE");
					ridersGate.TriggerGate(randomTime);
				}
			}
			if (message.StartsWith("TOGGLE_SPECTATOR"))
            {
				GetComponent<Utilities>().ToggleSpectator();
			}
			if (message.StartsWith("SPECTATE"))
            {
				string name = message.Split('|')[1];
				gameObject.GetComponent<Utilities>().SpectatePlayer(name);
            }
			if (message.StartsWith("SET_BIKE"))
            {
				int num = int.Parse(message.Split('|')[1]);
				gameObject.GetComponent<Utilities>().SetBike(num);
			}
			if (message.StartsWith("FREEZE_PLAYER"))
            {
				gameObject.GetComponent<Utilities>().FreezePlayer();
			}
			if (message.StartsWith("UNFREEZE_PLAYER"))
            {
				gameObject.GetComponent<Utilities>().UnfreezePlayer();
			}
			if (message.StartsWith("TOGGLE_CONTROL"))
            {
				string shouldStr = message.Split('|')[1];
				bool should = shouldStr == "true";
				gameObject.GetComponent<Utilities>().ToggleControl(should);
			}
			if (message.StartsWith("CLEAR_SESSION_MARKER"))
            {
				gameObject.GetComponent<Utilities>().ClearSessionMarker();
			}
			if (message.StartsWith("RESET_PLAYER"))
            {
				gameObject.GetComponent<Utilities>().ResetPlayer();
			}
			if (message.StartsWith("ADD_MODIFIER"))
            {
				string modifier = message.Split('|')[1];
				gameObject.GetComponent<Utilities>().AddGameModifier(modifier);
			}
			if (message.StartsWith("RESPAWN_ON_TRACK"))
            {
				gameObject.GetComponent<Utilities>().RespawnOnTrack();
			}
			if (message.StartsWith("RESPAWN_AT_START"))
            {
				gameObject.GetComponent<Utilities>().RespawnAtStartline();
			}
			if (message.StartsWith("INVALIDATE_TIME"))
            {
				string[] gate = message.Split('|');
				string reason = gate[1];
				TimerText.Instance.count = false;
				TimerText.Instance.text.text = reason;
				TimerText.Instance.text.color = Color.red;
			}
			if (message.StartsWith("TOGGLE_COLLISION"))
            {
				Physics.IgnoreLayerCollision(8, 8, PlayerCollision);
				PlayerCollision = !PlayerCollision;
			}
			if (message.StartsWith("TOGGLE_BOOST"))
            {
				if (gameObject.GetComponent<SpeedBoost>() == null)
					gameObject.AddComponent<SpeedBoost>();
				SpeedBoost speedBoost = gameObject.GetComponent<SpeedBoost>();
				speedBoost.speedEnabled = !speedBoost.speedEnabled;
				speedBoost.speedMultiplier = float.Parse(message.Split('|')[1]);
			}
			if (message.StartsWith("MODIFY_SPEED"))
            {
				if (gameObject.GetComponent<TimeModifier>() == null)
					gameObject.AddComponent<TimeModifier>();
				TimeModifier timeModifier = gameObject.GetComponent<TimeModifier>();
				timeModifier.speed = float.Parse(message.Split('|')[1]);
			}
			if (message.StartsWith("TOGGLE_GOD"))
            {
				Debug.Log("Toggling God.");
				gameObject.GetComponent<Utilities>().ToggleGod();
			}
			SendData("pong");
			Debug.Log("Message recieved: " + message);
		}
		public void SendData(string clientMessage) {
			clientMessage = clientMessage + "\n";
			Debug.Log("Client sending message: " + clientMessage);
			if (socketConnection == null) {  
				Debug.Log("Socket not connected!");           
				return;         
			}
			try { 					
				NetworkStream stream = socketConnection.GetStream(); 			
				if (stream.CanWrite) {
					byte[] clientMessageAsByteArray = Encoding.ASCII.GetBytes(clientMessage);
					stream.Write(clientMessageAsByteArray, 0, clientMessageAsByteArray.Length);
				}
			}
			catch (SocketException socketException) {             
				Debug.Log("Socket exception: " + socketException);         
			}     
		}
		public void OnDestroy()
		{
			SendData("MAP_EXIT");
			if (socketConnection != null)
			{
				socketConnection.Close();
			}
		}
	}
}