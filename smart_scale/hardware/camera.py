import time
import os
import subprocess
import shutil
from smart_scale.utils.logger import log

class CameraHandler:
    def __init__(self, resolution=(1024, 768)):
        self.resolution = resolution
        self.method = None
        
        if shutil.which("rpicam-still"):
            self.method = "rpicam"
            log("[CAM] detected 'rpicam-still'. Using CLI mode.")
        elif shutil.which("libcamera-still"):
            self.method = "libcamera"
            log("[CAM] detected 'libcamera-still'. Using CLI mode.")
        elif self._try_import_picamera():
            self.method = "legacy"
            log("[CAM] detected 'picamera' library. Using Legacy mode.")
        else:
            self.method = "mock"
            log("[CAM] No camera detected. Using Mock Camera.")

    def _try_import_picamera(self):
        try:
            import picamera
            self.camera = picamera.PiCamera()
            self.camera.resolution = self.resolution
            self.camera.close() 
            return True
        except:
            return False

    def capture_image(self, save_path="capture.jpg"):
        """Captures an image using the available method."""
        try:
            abs_path = os.path.abspath(save_path)
            
            if self.method in ["libcamera", "rpicam"]:
                cmd_exe = "rpicam-still" if self.method == "rpicam" else "libcamera-still"
                
                cmd = [
                    cmd_exe,
                    "-o", abs_path,
                    "-t", "500",
                    "--width", str(self.resolution[0]),
                    "--height", str(self.resolution[1]),
                    "-n" 
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                log(f"[CAM] Image saved to {save_path} ({self.method})")
                return save_path

            elif self.method == "legacy":
                import picamera
                with picamera.PiCamera() as cam:
                    cam.resolution = self.resolution
                    cam.start_preview()
                    time.sleep(1) 
                    cam.capture(abs_path)
                log(f"[CAM] Image saved to {save_path} (legacy)")
                return save_path

            else:
                return self._mock_capture(save_path)

        except Exception as e:
            log(f"[CAM] Capture failed ({self.method}): {e}")
            if self.method != "mock":
                log("[CAM] Falling back to mock...")
                return self._mock_capture(save_path)
            return None

    def _mock_capture(self, save_path):
        """Creates a dummy image for testing."""
        try:
            from PIL import Image, ImageDraw
            img = Image.new('RGB', self.resolution, color = 'red')
            d = ImageDraw.Draw(img)
            d.text((10,10), "Mock Image", fill=(255,255,0))
            img.save(save_path)
            log(f"[CAM] Mock image generated at {save_path}")
            return save_path
        except:
            return None

    def close(self):
        pass
