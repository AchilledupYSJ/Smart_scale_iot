import os
import time
import numpy as np
from smart_scale.config import MODEL_FILENAME, LABELS_FILENAME, CONFIDENCE_THRESHOLD, CONFIDENCE_THRESHOLD_KNOWN
from smart_scale.utils.logger import log

try:
    from PIL import Image
    import tflite_runtime.interpreter as tflite
except ImportError:
    try:
        from PIL import Image
        import tensorflow.lite as tflite
    except ImportError:
        log("[AI] WARNING: Neither tflite_runtime nor tensorflow installed. Vision will fail.")
        tflite = None

class VisionAI:
    def __init__(self, models_dir=None):
        if models_dir is None:
            
            base_dir = os.path.dirname(os.path.abspath(__file__))
            models_dir = os.path.join(base_dir, "models")
            
        self.model_path = os.path.join(models_dir, MODEL_FILENAME)
        self.labels_path = os.path.join(models_dir, LABELS_FILENAME)
        self.interpreter = None
        self.input_details = None
        self.output_details = None
        self.labels = []
        
        self.warmup()

    def warmup(self):
        """Loads model into memory."""
        if tflite is None:
            return

        log(f"[AI] Loading model from {self.model_path}...")
        try:
           
            if os.path.exists(self.labels_path):
                with open(self.labels_path, 'r') as f:
                    self.labels = [line.strip() for line in f.readlines()]
            else:
                log(f"[AI] Labels file not found: {self.labels_path}")

            self.interpreter = tflite.Interpreter(model_path=self.model_path)
            self.interpreter.allocate_tensors()

            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            
            log(f"[AI] Model loaded. Labels: {len(self.labels)}")

        except Exception as e:
            log(f"[AI] Error loading model: {e}")
            self.interpreter = None

    def analyze_image(self, image_path, known_keywords=None):
        """
        Infers the class of the image.
        If known_keywords is provided (list of strings), it will search the Top 5
        predictions for a match and prioritize it over the Top 1.
        
        Returns: (label, confidence) or (None, 0.0)
        """
        if self.interpreter is None:
            return None, 0.0

        if not os.path.exists(image_path):
            log(f"[AI] Image not found: {image_path}")
            return None, 0.0

        try:
            start_time = time.time()
            
           
            input_shape = self.input_details[0]['shape']
            height, width = input_shape[1], input_shape[2]
            
            img = Image.open(image_path).convert('RGB')
            img = img.resize((width, height))
            
    
            input_type = self.input_details[0]['dtype']
            img_data = np.array(img, dtype=input_type)
            img_data = np.expand_dims(img_data, axis=0) 
            
         
            self.interpreter.set_tensor(self.input_details[0]['index'], img_data)
            self.interpreter.invoke()
            
          
            output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
            predictions = np.squeeze(output_data) 

          
            top_k_indices = predictions.argsort()[-5:][::-1]
            
            final_label = None
            final_score = 0.0
            found_promoted = False

            log("[AI] Top 5 Predictions (Raw):")
            for i, idx in enumerate(top_k_indices):
                score = predictions[idx]
                if input_type == np.uint8:
                    score = score / 255.0
                else:
                    score = float(score)
                
                lbl = self.labels[idx] if idx < len(self.labels) else "Unknown"
                log(f"   {i+1}. {lbl}: {score:.3f}")
                
              
                if i == 0:
                    final_label = lbl
                    final_score = score
                
            
                if known_keywords and not found_promoted:
                    clean_lbl = lbl.lower()
                    for kw in known_keywords:
                        if kw.lower() in clean_lbl:
                            log(f"[AI] *** SMART FILTER MATCH: '{lbl}' (Rank {i+1}) matches keyword '{kw}' -> PROMOTED ***")
                            final_label = lbl
                            final_score = score
                            found_promoted = True
                            break
            
            duration = time.time() - start_time
            log(f"[AI] Final Decision: {final_label} ({final_score:.2f}) in {duration:.3f}s")
            
            
            threshold = CONFIDENCE_THRESHOLD
            if found_promoted:
                threshold = CONFIDENCE_THRESHOLD_KNOWN
                log(f"[AI] Using lowered threshold ({threshold}) for known item.")

            if final_score < threshold:
                log(f"[AI] Low confidence ({final_score:.2f} < {threshold}). Ignoring.")
                return None, final_score

            return final_label, final_score

        except Exception as e:
            log(f"[AI] Inference error: {e}")
            return None, 0.0
