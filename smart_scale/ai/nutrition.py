from smart_scale.utils.logger import log

# Simple database of nutrition per 100g
# Format: "key": {"calories": kcal, "protein": g, "carbs": g, "fats": g}
NUTRITION_DB = {
    "apple": {"calories": 52, "protein": 0.3, "carbs": 14, "fats": 0.2},
    "banana": {"calories": 89, "protein": 1.1, "carbs": 23, "fats": 0.3},
    "orange": {"calories": 47, "protein": 0.9, "carbs": 12, "fats": 0.1},
    "lemon": {"calories": 29, "protein": 1.1, "carbs": 9, "fats": 0.3},
    "strawberry": {"calories": 32, "protein": 0.7, "carbs": 7.7, "fats": 0.3},
    "bell pepper": {"calories": 20, "protein": 0.9, "carbs": 4.6, "fats": 0.2},
    "granny smith": {"calories": 52, "protein": 0.3, "carbs": 14, "fats": 0.2}, # Map to Apple
    "banana": {"calories": 89, "protein": 1.1, "carbs": 23, "fats": 0.3},
}

# ImageNet labels might be specific (e.g., "Granny Smith"). 
# This map normalizes them to our DB keys.
LABEL_MAPPING = {
    "granny smith": "apple",
    "golden delicious": "apple",
    "fig": "fig",
    "banana": "banana",
    "orange": "orange",
    "lemon": "lemon",
    "strawberry": "strawberry",
    "bell pepper": "bell pepper",
    "sweet pepper": "bell pepper",
    "capsicum": "bell pepper",
    "pimiento": "bell pepper"
}

class NutritionCalculator:
    def get_nutrition(self, label, weight_g):
        """
        Calculates total calories/macros.
        Label: The string returned by VisionAI.
        Weight: Weight in grams.
        """
        if not label:
            return None
            
        clean_label = label.lower().strip()
        
        # 1. Normalize Label
        food_key = clean_label
        for specific, generic in LABEL_MAPPING.items():
            if specific in clean_label:
                food_key = generic
                break
        
        # 2. Lookup
        data = NUTRITION_DB.get(food_key)
        if not data:
            log(f"[NUTRITION] Food '{food_key}' not found in database.")
            # Fallback based on simple keyword search if exact match fails
            for key in NUTRITION_DB.keys():
                if key in clean_label:
                    data = NUTRITION_DB[key]
                    log(f"[NUTRITION] Fallback match: '{clean_label}' -> '{key}'")
                    break
        
        if not data:
            return None

        # 3. Calculate
        factor = weight_g / 100.0
        result = {
            "food": food_key.capitalize(),
            "weight": weight_g,
            "calories": round(data["calories"] * factor, 1),
            "protein": round(data["protein"] * factor, 1),
            "carbs": round(data["carbs"] * factor, 1),
            "fats": round(data["fats"] * factor, 1)
        }
        
        return result
