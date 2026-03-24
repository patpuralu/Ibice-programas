# IBICE Watchdog

IBICE Watchdog es una herramienta en Python para **monitorizar tu red local en tiempo real**, detectar dispositivos conectados y analizar posibles intrusos.

---

## ¿Qué hace?

IBICE Watchdog escanea tu red local y:

* Detecta dispositivos conectados (IP + MAC)
* Identifica fabricante (Huawei, Apple, etc.)
* Escanea puertos comunes abiertos
* Intenta identificar el tipo de dispositivo:

  * Router
  * Móvil
  * TV
  * Cámara
  * Consola
  * IoT
* Detecta dispositivos:

  * Nuevos
  * Sospechosos
  * Permitidos
* Guarda historial en CSV
* Muestra un mapa de red

---

## Cómo funciona internamente

### 1. Descubrimiento de red

* Hace ping a toda la red (`192.168.x.1 - 254`)
* Usa `arp -a` para obtener:

  * IP
  * MAC

---

### 2. Identificación de fabricante

* Usa la API:

  ```
  https://api.macvendors.com/
  ```
* A partir de la MAC obtiene el fabricante

---

### 3. Escaneo de puertos

Comprueba puertos comunes como:

```
21, 22, 80, 443, 8080, 5000, 9100...
```

Para detectar servicios activos:

* Web
* NAS
* Impresoras
* Cámaras

---

### 4. Clasificación de dispositivos

Según MAC, puertos y fabricante:

| Tipo | Descripción      |
| ---- | ---------------- |
| (TD) | Tu dispositivo   |
| (R)  | Router           |
| (P)  | Permitido        |
| (N)  | Nuevo            |
| (NS) | Nuevo sospechoso |
| (S)  | Sospechoso       |
| •    | Normal           |

---

### 5. Detección de sospechosos

Un dispositivo es sospechoso si:

* Tiene MAC rara
* Fabricante desconocido
* No estaba antes en la red

---

### 6. Persistencia

Archivos generados:

* `permitidos.txt` → dispositivos confiables
* `historial_ibice.csv` → registro de actividad

---

## Modos de uso

### 1. Watchdog (tiempo real)

Monitorea continuamente la red:

* Escaneo cada X segundos
* Detecta cambios en tiempo real
* Muestra:

  * Nuevos dispositivos
  * Dispositivos desconectados

---

### 2. Escáner profundo

* Escanea todos los dispositivos
* Analiza puertos abiertos
* No es continuo

---

## Cómo usarlo

### Requisitos

* Python 3
* Librerías:

```bash
pip install requests
```

---

### Ejecutar

```bash
python Ibice.py
```

---
### Instalar el .exe 

En el .exe ya lo tienes todo, solo debes instalarlo y ejecutarlo (Windows)

---
### Menú

```
1) Watchdog
2) Escaner profundo
```

---

## Ejemplo de salida

```
Tipo IP              MAC                  Fabricante        Disp        Puertos
(N)  192.168.1.45    aa-bb-cc-dd-ee-ff    Xiaomi            Movil       80,443
(R)  192.168.1.1     xx-xx-xx-xx-xx-xx    TP-Link           Router      80
```

---

## Mapa de red

```
(R) 192.168.1.1 Router
   └─ (P) 192.168.1.10 PC
   └─ (N) 192.168.1.45 Movil
```

---

## Limitaciones

* Depende de `arp` → puede no detectar todo
* API de fabricante puede fallar
* Escaneo de puertos limitado (timeout corto)
* Optimizado más para Windows (`getmac`, `ping -n`)

---

## Uso ético

Este programa está diseñado para:

* Auditar tu propia red
* Detectar intrusos
* NO usar en redes ajenas sin permiso
