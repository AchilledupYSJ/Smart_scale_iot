import requests
import threading
from smart_scale.config import THINGSPEAK_API_KEY, THINGSPEAK_URL
from smart_scale.utils.logger import log

def upload_data(food_name, weight, calories, protein, carbs, fats):
    """
    Uploads data to ThingSpeak in a background thread to avoid blocking the main UI.
    """
    if not THINGSPEAK_API_KEY or "YOUR_API_KEY" in THINGSPEAK_API_KEY:
        log("[CLOUD] API Key not configured. Skipping upload.")
        return

    def _send():
        try:
           
            payload = {
                "api_key": THINGSPEAK_API_KEY,
                "field1": weight,       
                "field2": calories,     
                "field3": protein,     
                "field4": carbs,        
                "field5": fats,         
                
                "status": f"Food: {food_name}" 
            }
            
            response = requests.get(THINGSPEAK_URL, params=payload, timeout=5)
            if response.status_code == 200:
                log(f"[CLOUD] Data uploaded to ThingSpeak! (Entry ID: {response.text})")
            else:
                log(f"[CLOUD] Upload failed: {response.status_code} - {response.text}")
        except Exception as e:
            log(f"[CLOUD] Connection error: {e}")


    t = threading.Thread(target=_send, daemon=True)
    t.start()
