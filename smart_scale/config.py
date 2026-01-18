# config.py

# config bluetooth
BT_MAC_ADDRESS = "FC:45:C3:E0:AF:46"
BT_PORT = 1  
BT_TIMEOUT = 10 

# configuracion peso
WEIGHT_THRESHOLD_START = 10.0  
WEIGHT_STABLE_VARIANCE = 2.0   


WEIGHT_THRESHOLD_RESET = 5.0

# configuracion vision
MODEL_FILENAME = "mobilenet_v1_1.0_224_quant.tflite"
LABELS_FILENAME = "labels_mobilenet_quant_v1_224.txt"
CONFIDENCE_THRESHOLD = 0.5
CONFIDENCE_THRESHOLD_KNOWN = 0.2  

# configuracion nube
THINGSPEAK_API_KEY = "LU5PCN2QJAMAXY2R"
THINGSPEAK_URL = "https://api.thingspeak.com/update"

DEBUG_MODE = True
