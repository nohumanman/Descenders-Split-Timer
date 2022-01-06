﻿using UnityEngine;
using ModTool.Interface;

namespace RocketLeagueMod
{
    public class Loader : ModBehaviour
    {
        public static GameObject gameObject;

        public static void Load()
        {
            Debug.Log("MODLOADER START");
            Utilities _u = GameObject.FindObjectOfType<Utilities>();
            if (_u != null)
            {
                Debug.Log("Mod was already loaded, unloading...");
                MonoBehaviour.Destroy(_u.gameObject);
            }
            Debug.Log("Finished Mod Check");
            gameObject = new GameObject();
            gameObject.name = "loaderRockLeagu";
            Debug.Log("GameObject Instantiated");
            gameObject.AddComponent<Utilities>();
            Debug.Log("Utilities added");
            gameObject.AddComponent<BikeSwitcher>();
            Debug.Log("BikeSwitcher added");
        }
        public static void Unload()
        {
            MonoBehaviour.Destroy(gameObject);
        }

        public static void _unload()
        {
            MonoBehaviour.Destroy(gameObject);
        }
    }
}

