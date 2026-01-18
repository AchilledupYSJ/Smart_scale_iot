#include <SoftwareSerial.h>
#include "HX711.h"

SoftwareSerial miBluetooth(2, 3);

const int LOADCELL_DOUT_PIN = 4;
const int LOADCELL_SCK_PIN = 5;
HX711 balanza;
float calibration_factor = 953.5; 

const int PIN_TRIG = 6;
const int PIN_ECHO = 7;

const int DISTANCIA_UMBRAL = 15; 

bool objetoDetectado = false; 

void setup() {
  Serial.begin(9600);
  miBluetooth.begin(9600);
  
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);

  Serial.println("--- SISTEMA INTELIGENTE INICIADO ---");
  Serial.println("Tarando balanza...");
  
  balanza.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  balanza.set_scale();
  balanza.tare();
  
  Serial.println("¡Listo! Esperando objeto...");
}

void loop() {
  long duracion, distancia_cm;
  
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);
  
  duracion = pulseIn(PIN_ECHO, HIGH);
  distancia_cm = duracion * 0.034 / 2;
  

  if (distancia_cm < DISTANCIA_UMBRAL && distancia_cm > 0) {
    
    if (!objetoDetectado) {
      Serial.println("--> Objeto detectado. Esperando 3 segundos para estabilizar...");
      
      delay(3000); 
  
      balanza.set_scale(calibration_factor);
      float peso = balanza.get_units(10);
      if (peso < 0) peso = 0.00;
      
      Serial.print("Peso estable capturado: ");
      Serial.print(peso, 1);
      Serial.println(" g");
      
      miBluetooth.println(peso, 1);
      
      objetoDetectado = true; 
    }
    
  } else {
    if (objetoDetectado) {
      Serial.println("Objeto retirado. Listo para el siguiente.");
      objetoDetectado = false;
      
    }
  }
  
  delay(100);
}