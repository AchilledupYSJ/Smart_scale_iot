import asyncio
import threading
import time
from bleak import BleakClient, BleakScanner
from smart_scale.config import BT_MAC_ADDRESS, BT_TIMEOUT
from smart_scale.utils.logger import log

class BluetoothClient:
    def __init__(self):
        self.mac = BT_MAC_ADDRESS
        self.connected = False
        self._latest_weight = None
        self._stop_event = asyncio.Event()
        self._thread = None
        self._loop = None

    def connect(self):
        """Starts the BLE connection loop in a background thread."""
        if self.connected:
            return True

        
        self._thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self._thread.start()
        
     
        time.sleep(2)
        return True 

    def _run_async_loop(self):
        asyncio.run(self._ble_main())

    async def _ble_main(self):
        log(f"[BLE] Connecting to {self.mac}...")
        
        def notification_handler(sender, data):
            try:
             
                text = data.decode('utf-8', errors='ignore').strip()
                if not text:
                    return
                
                
                clean_text = ''.join(c for c in text if c.isdigit() or c == '.')
                if clean_text:
                    self._latest_weight = float(clean_text)
                    self.connected = True
            except Exception as e:
                
                pass

        while not self._stop_event.is_set():
            try:
                device = await BleakScanner.find_device_by_address(self.mac, timeout=10.0)
                if not device:
                    log(f"[BLE] Device {self.mac} not found. Retrying...")
                    self.connected = False
                    await asyncio.sleep(5)
                    continue

                async with BleakClient(device, timeout=BT_TIMEOUT) as client:
                    log(f"[BLE] Connected: {client.is_connected}")
                    self.connected = True

                    
                    target_char = None
                    for service in client.services:
                        for char in service.characteristics:
                            if "notify" in char.properties:
                                target_char = char.uuid
                                break
                        if target_char:
                            break
                    
                    if not target_char:
                        log("[BLE] No Notify Characteristic found! Cannot read data.")
                        return

                    log(f"[BLE] Subscribing to {target_char}...")
                    await client.start_notify(target_char, notification_handler)
                    
                    
                    while client.is_connected and not self._stop_event.is_set():
                        await asyncio.sleep(1.0)
                        
                    self.connected = False
                    log("[BLE] Disconnected.")

            except Exception as e:
                log(f"[BLE] Connection Error: {e}")
                self.connected = False
                await asyncio.sleep(5) 

    def read_weight(self):
        """Returns the latest reading from the background thread."""
        return self._latest_weight

    def close(self):
        if self._loop:
            self._loop.call_soon_threadsafe(self._stop_event.set)
        self.connected = False
