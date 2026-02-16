import subprocess
import time
import re
import socket
import requests
import os
import sys
from datetime import datetime

#Los colores principales
AZUL = "\033[94m"
VERDE = "\033[92m"
ROJO = "\033[91m"
AMARILLO = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RESET = "\033[0m"

ARCH_PERMIT = "permitidos.txt"
ARCH_HIST = "historial_ibice.csv"

PUERTOS_COMUNES = [
    21,22,23,53,80,139,443,445,554,
    8080,8443,8000,8001,8002,8883,9000,
    5000,5001,9100,515,631
]

def prepararArchivos():
    if not os.path.exists(ARCH_PERMIT):
        with open(ARCH_PERMIT, "w", encoding="utf-8") as f:
            f.write("")
    if not os.path.exists(ARCH_HIST):
        with open(ARCH_HIST, "w", encoding="utf-8") as f:
            f.write("fecha;ip;mac;fabricante;tipo;puertos;disp\n")

def limpiarPantalla():
    os.system("cls" if os.name == "nt" else "clear")

def buscarIPLocal():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    s.close()
    return ip

def buscarMACLocal():
    try:
        salida = subprocess.check_output("getmac", shell=True).decode(errors="ignore")
        m = re.search(r"([0-9A-F]{2}(-[0-9A-F]{2}){5})", salida, re.I)
        return m.group(1).lower() if m else "00-00-00-00-00-00"
    except:
        return "00-00-00-00-00-00"

def b_red(ip):
    p = ip.split(".")
    return f"{p[0]}.{p[1]}.{p[2]}."

def fabricanteMAC(mac):
    try:
        pref = mac.upper().replace("-", ":")
        pref = ":".join(pref.split(":")[:3])
        r = requests.get(f"https://api.macvendors.com/{pref}", timeout=2)
        if r.status_code == 200:
            t = r.text.strip()
            if t:
                return t[:18]
    except:
        pass
    return "Desconocido"

def macRara(mac):
    try:
        m = mac.replace("-", "").replace(":", "").lower()
        return m[1] in ["2","6","a","e"]
    except:
        return False

def puertoOK(ip, p):
    try:
        s = socket.socket()
        s.settimeout(0.15)
        if s.connect_ex((ip,p)) == 0:
            s.close()
            return True
        s.close()
    except:
        pass
    return False

def mirarPuertos(ip):
    abiertos = []
    inicio = time.time()
    for p in PUERTOS_COMUNES:
        if puertoOK(ip, p):
            abiertos.append(p)
        if time.time() - inicio > 5:
            break
    return abiertos

# Revisar o cambiar no funciona del todo
def tipoDisp(d):
    fab = (d.get("fabricante") or "").lower()
    pu = d.get("puertos", [])
    if any(x in pu for x in [5000,5001,8080,443]):
        return "NAS"
    if any(x in pu for x in [9100,515,631]):
        return "Impresora"
    if 554 in pu or any(x in pu for x in [8000,8001,8002,9000]):
        return "Camara"
    if any(x in pu for x in [139,445]):
        return "Windows"
    if any(x in fab for x in ["zte","router","huawei","tplink"]):
        return "Router"
    if any(x in fab for x in ["samsung","xiaomi","apple","huawei","oppo","realme","oneplus"]):
        return "Movil"
    if any(x in fab for x in ["lg","sony","philips","hisense","samsung"]) and 8000 in pu:
        return "TV"
    if any(x in fab for x in ["playstation","sony interactive","xbox","nintendo"]):
        return "Consola"
    if any(x in pu for x in [1883,8883,8000,8001,8002,9000]):
        return "IoT"
    return "Desconocido"

def es_dispositivos(base, ipLocal, macLocal):
    lista = []
    for i in range(1,255):
        ip = f"{base}{i}"
        subprocess.Popen(
            f"start /b ping -n 1 -w 1 {ip}",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    time.sleep(0.3)
    try:
        salida = subprocess.check_output("arp -a", shell=True).decode(errors="ignore")
    except:
        salida = ""
    for linea in salida.split("\n"):
        m = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-f\-]{17})", linea, re.I)
        if m:
            ip, mac = m.groups()
            mac = mac.lower()
            if ip.startswith(("224.","239.","255.")):
                continue
            pu = mirarPuertos(ip)
            lista.append({
                "ip": ip,
                "mac": mac,
                "fabricante": fabricanteMAC(mac),
                "puertos": pu
            })
    if not any(d["mac"] == macLocal for d in lista):
        pu2 = mirarPuertos(ipLocal)
        lista.append({
            "ip": ipLocal,
            "mac": macLocal,
            "fabricante": "Este equipo",
            "puertos": pu2
        })
    return lista

def cargarPermitidos():
    s = set()
    if os.path.exists(ARCH_PERMIT):
        with open(ARCH_PERMIT, "r", encoding="utf-8") as f:
            for l in f:
                l = l.strip().lower()
                if l:
                    s.add(l)
    return s

def guardarHistorial(disps):
    existe = os.path.exists(ARCH_HIST)
    with open(ARCH_HIST, "a", encoding="utf-8") as f:
        if not existe:
            f.write("fecha;ip;mac;fabricante;tipo;puertos;disp\n")
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for d in disps:
            f.write(
                f"{ahora};{d['ip']};{d['mac']};{d['fabricante']};"
                f"{d['tipo']};{','.join(map(str,d['puertos']))};{d.get('dispositivo','')}\n"
            )

def clasificarDisp(d, permitidos, antes, ipLocal, macLocal, ipRouter):
    mac = d["mac"]
    ip = d["ip"]
    fab = d["fabricante"]
    if mac == macLocal or fab == "Este equipo":
        t = "este_equipo"
    elif ip == ipRouter:
        t = "router"
    elif mac in permitidos:
        t = "permitido"
    elif mac not in antes:
        if fab == "Desconocido" or macRara(mac):
            t = "nuevo_sospechoso"
        else:
            t = "nuevo"
    else:
        if fab == "Desconocido" or macRara(mac):
            t = "sospechoso"
        else:
            t = "normal"
    iconos = {
        "este_equipo": "(TD)",
        "router": "(R)",
        "permitido": "(P)",
        "nuevo": "(N)",
        "nuevo_sospechoso": "(NS)",
        "sospechoso": "(S)",
        "normal": "•"
    }
    colores = {
        "este_equipo": CYAN,
        "router": MAGENTA,
        "permitido": VERDE,
        "nuevo": AMARILLO,
        "nuevo_sospechoso": ROJO,
        "sospechoso": ROJO,
        "normal": RESET
    }
    d["tipo"] = t
    d["icono"] = iconos[t]
    d["color"] = colores[t]
    d["dispositivo"] = tipoDisp(d)
    return d

# El inicio
def banner_ibice():
    print(AZUL + r"""
██╗██████╗ ██╗ ██████╗███████╗
██║██╔══██╗██║██╔════╝██╔════╝
██║██████╔╝██║██║     █████╗  
██║██╔══██╗██║██║     ██╔══╝  
██║██████╔╝██║╚██████╗███████╗
╚═╝╚═════╝ ╚═╝ ╚═════╝╚══════╝
        IBICE WATCHDOG
""" + RESET)

def mapaRed(disps, ipRouter):
    print(MAGENTA + "\n[ Mapa de red ]" + RESET)
    r = None
    otros = []
    for d in disps:
        if d["ip"] == ipRouter or d["tipo"] == "router":
            r = d
        else:
            otros.append(d)
    if r:
        print(f"{r['color']}{r['icono']} {r['ip']}  {r['mac']}  {r['fabricante']} [{r.get('dispositivo','')}]"+RESET)
    else:
        print("Router no detectado")
    for d in otros:
        print(f"   └─ {d['color']}{d['icono']} {d['ip']}  {d['mac']}  {d['fabricante']} [{d.get('dispositivo','')}]"+RESET)

# Funciones Principales no borrar
def modoWatch(ipLocal):
    limpiarPantalla()
    banner_ibice()
    print(CYAN + "Selecciona modo de escaneo:" + RESET)
    print("1) Normal (10s)")
    print("2) Rapido (2s)")
    m = input("> ").strip()
    espera = 10 if m != "2" else 2
    macLocal = buscarMACLocal()
    base = b_red(ipLocal)
    ipRouter = base + "1"
    print(CYAN + f"\nIP local: {ipLocal}" + RESET)
    print(CYAN + f"MAC local: {macLocal}" + RESET)
    print(CYAN + f"Rango: {base}1 - {base}254" + RESET)
    print(CYAN + f"Gateway: {ipRouter}" + RESET)
    permit = cargarPermitidos()
    if len(permit) == 0:
        print(AMARILLO + "\nAprendiendo dispositivos actuales..." + RESET)
        ini = es_dispositivos(base, ipLocal, macLocal)
        with open(ARCH_PERMIT, "w", encoding="utf-8") as f:
            for d in ini:
                f.write(d["mac"] + "\n")
                permit.add(d["mac"])
        print(VERDE + "Guardados como permitidos." + RESET)
    antes = {}
    try:
        while True:
            print(AMARILLO + "\nEscaneando red..." + RESET)
            lista = es_dispositivos(base, ipLocal, macLocal)
            ahora = {}
            for d in lista:
                d = clasificarDisp(d, permit, antes, ipLocal, macLocal, ipRouter)
                ahora[d["mac"]] = d
            guardarHistorial(list(ahora.values()))
            total = len(ahora)
            print()
            print("Tipo".ljust(4), "IP".ljust(16), "MAC".ljust(20), "Fabricante".ljust(18), "Disp".ljust(12), "Puertos")
            print("-"*110)
            for d in ahora.values():
                pu = ",".join(map(str,d["puertos"])) if d["puertos"] else "-"
                disp = d.get("dispositivo","")[:12]
                print(
                    d["color"] +
                    d["icono"].ljust(4),
                    d["ip"].ljust(16),
                    d["mac"].ljust(20),
                    d["fabricante"][:18].ljust(18),
                    disp.ljust(12),
                    pu +
                    RESET
                )
            print(CYAN + f"\nDispositivos conectados: {total}" + RESET)
            mapaRed(list(ahora.values()), ipRouter)
            nuevos = [d for mac,d in ahora.items() if mac not in antes]
            if nuevos:
                print(AMARILLO + "\nNuevos dispositivos" + RESET)
                for d in nuevos:
                    print(
                        d["color"] +
                        f"{d['icono']} {d['ip']}  {d['mac']}  {d['fabricante']} ({d['tipo']}) [{d.get('dispositivo','')}]" +
                        RESET
                    )
            fuera = [d for mac,d in antes.items() if mac not in ahora]
            if fuera:
                print(ROJO + "\nDispositivos desconectados" + RESET)
                for d in fuera:
                    print(
                        ROJO +
                        f"{d['ip']}  {d['mac']}  {d['fabricante']} [{d.get('dispositivo','')}]" +
                        RESET
                    )
            antes = ahora
            print(CYAN + f"\nEsperando {espera} segundos..." + RESET)
            time.sleep(espera)
    except KeyboardInterrupt:
        print(ROJO + "\nIBICE Watchdog detenido." + RESET)
        sys.exit(0)

def portscanProfundo(ipLocal):
    base = b_red(ipLocal)
    print(CYAN + f"\nEscaner profundo" + RESET)
    print(CYAN + f"Rango: {base}1 - {base}254" + RESET)
    print(AMARILLO + "\nBuscando dispositivos..." + RESET)
    lista = es_dispositivos(base, ipLocal, buscarMACLocal())
    ips = sorted(set(d["ip"] for d in lista))
    print(CYAN + f"\nDetectados: {len(ips)}" + RESET)
    for ip in ips:
        print(AMARILLO + f"\nEscaneando {ip}..." + RESET)
        ab = mirarPuertos(ip)
        if ab:
            print(VERDE + f"Puertos abiertos: {', '.join(map(str,ab))}" + RESET)
        else:
            print(ROJO + "Sin puertos comunes abiertos" + RESET)
    print(CYAN + "\nFinalizado" + RESET)

#Seleccion del modo
def menuPrincipal():
    prepararArchivos()
    limpiarPantalla()
    banner_ibice()
    print(CYAN + "Selecciona modo:" + RESET)
    print("1) Watchdog")
    print("2) Escaner profundo")
    m = input("> ").strip()
    ipLocal = buscarIPLocal()
    if m == "2":
        portscanProfundo(ipLocal)
    else:
        modoWatch(ipLocal)

if __name__ == "__main__":
    menuPrincipal()
