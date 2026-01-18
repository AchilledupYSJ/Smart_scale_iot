import time
import os
from smart_scale.config import (
    WEIGHT_THRESHOLD_START, 
    WEIGHT_STABLE_VARIANCE, 
    WEIGHT_THRESHOLD_RESET,
    DEBUG_MODE
)
from smart_scale.hardware.camera import CameraHandler
from smart_scale.hardware.bluetooth_client import BluetoothClient
from smart_scale.ai.vision import VisionAI
from smart_scale.ai.nutrition import NutritionCalculator, NUTRITION_DB, LABEL_MAPPING
from smart_scale.utils.logger import log

class SmartScaleApp:
    def __init__(self):
        log("[MAIN] Initializing Smart Scale V2...")
        self.camera = CameraHandler()
        self.bt_client = BluetoothClient()
        self.vision = VisionAI()
        self.calc = NutritionCalculator()
        
        self.state = "IDLE" 
        self.last_weight = 0.0
        self.stable_counter = 0

    def run(self):
        while not self.bt_client.connect():
            log("[MAIN] Retrying Bluetooth in 5s...")
            time.sleep(5)
            
        log("[MAIN] System Ready. Waiting for weight...")
        
        try:
            while True:
                weight = self.bt_client.read_weight()
                if weight is None:
                    if not self.bt_client.connected:
                        log("[MAIN] Bluetooth disconnected. Reconnecting...")
                        self.bt_client.connect()
                    continue
                    
                self._process_weight(weight)
                time.sleep(0.1) 

        except KeyboardInterrupt:
            log("[MAIN] Stopping...")
        finally:
            self.cleanup()

    def _process_weight(self, current_weight):
        
        if current_weight < WEIGHT_THRESHOLD_RESET and self.state != "IDLE":
            log("[MAIN] Weight removed. Resetting to IDLE.")
            print("\n--- READY FOR NEXT ITEM ---\n")
            self.state = "IDLE"
            self.stable_counter = 0
            return

        if self.state == "IDLE":
            if current_weight > WEIGHT_THRESHOLD_START:
                log(f"[MAIN] Weight detected ({current_weight}g). Stabilizing...")
                self.state = "STABILIZING"
                self.last_weight = current_weight
                self.stable_counter = 0

        elif self.state == "STABILIZING":
            diff = abs(current_weight - self.last_weight)
            if diff < WEIGHT_STABLE_VARIANCE:
                self.stable_counter += 1
            else:
                self.stable_counter = 0
                self.last_weight = current_weight
            
            if self.stable_counter >= 10:
                self.state = "PROCESSING"
                self._perform_analysis(current_weight)

    def _perform_analysis(self, weight):
        log(f"[MAIN] Weight Stable: {weight}g. Capturing...")
        
        img_path = self.camera.capture_image("current_food.jpg")
        
        known_words = list(NUTRITION_DB.keys()) + list(LABEL_MAPPING.keys())
        label, conf = self.vision.analyze_image(img_path, known_keywords=known_words)
        
        if label and label != "Unknown":
            info = self.calc.get_nutrition(label, weight)
            
            if info:
                self._display_result(info)
                from smart_scale.cloud.thingspeak import upload_data
                upload_data(
                    food_name=info['food'],
                    weight=info['weight'],
                    calories=info['calories'],
                    protein=info['protein'],
                    carbs=info['carbs'],
                    fats=info['fats']
                )
            else:
                log(f"[MAIN] Identified '{label}' but no nutrition info found.")
        else:
            log("[MAIN] Could not identify food.")
            
        self.state = "RESULT"

    def _display_result(self, info):
        print("\n" + "="*30)
        print(f" FOOD DETECTED: {info['food']}")
        print(f" WEIGHT: {info['weight']}g")
        print("-" * 30)
        print(f" CALORIES: {info['calories']} kcal")
        print(f" PROTEIN:  {info['protein']} g")
        print(f" CARBS:    {info['carbs']} g")
        print(f" FATS:     {info['fats']} g")
        print("="*30 + "\n")

    def cleanup(self):
        self.camera.close()
        self.bt_client.close()

if __name__ == "__main__":
    app = SmartScaleApp()
    app.run()
