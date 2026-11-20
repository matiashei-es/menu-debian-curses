import curses
from datetime import datetime
import glob
import json
import os
import subprocess
import urllib.error
import urllib.request

TITULO = "FURBO DT - MATI"
CIUDAD_CLIMA = "Manuel+Alberti,Argentina"


def obtener_clima(ciudad=CIUDAD_CLIMA):
    url = f"https://wttr.in/{ciudad}?format=%t+%C&lang=es"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "curl/7.88.1"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            texto = resp.read().decode("utf-8", errors="replace").strip()
            if texto and "Unknown location" not in texto:
                return " ".join(texto.split())
    except (urllib.error.URLError, TimeoutError, Exception):
        pass
    return "Clima no disponible"


def obtener_jsons():
    rutas = [
        "*.json",
        os.path.expanduser("~/*.json"),
        os.path.expanduser("~/Alineaciones-Fut/*.json"),
        os.path.expanduser("~/downloads/*.json"),
    ]
    encontrados = []
    for ruta in rutas:
        for archivo in glob.glob(ruta):
            ruta_abs = os.path.abspath(archivo)
            if ruta_abs not in encontrados:
                encontrados.append(ruta_abs)
    return sorted(encontrados)


def formatear_json_ordenado(data):
    if isinstance(data, dict):
        lineas = []
        equipo = data.get("equipo")
        formacion = data.get("formacion")
        jugadores = data.get("jugadores")

        cabecera = []
        if equipo is not None:
            cabecera.append(f"Equipo: {equipo}")
        if formacion is not None:
            cabecera.append(f"Formación: {formacion}")
        if cabecera:
            lineas.append(" | ".join(cabecera))
            lineas.append("")

        if isinstance(jugadores, list):
            lineas.extend(_dibujar_canchita(formacion, jugadores))
            return "\n".join(lineas)

        for clave, valor in data.items():
            if clave in ("equipo", "formacion", "jugadores"):
                continue
            if isinstance(valor, (dict, list)):
                lineas.append(f"{clave.capitalize()}:")
                for sub in json.dumps(valor, indent=2, ensure_ascii=False).splitlines():
                    lineas.append(f"  {sub}")
            else:
                lineas.append(f"{clave.capitalize()}: {valor}")

        if lineas:
            return "\n".join(lineas)

    return json.dumps(data, indent=2, ensure_ascii=False)


def ver_contenido_json(stdscr, ruta_json, color_rojo):
    try:
        with open(ruta_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        texto = json.dumps(data, indent=2, ensure_ascii=False)
    except Exception as e:
        texto = f"Error al leer el archivo:\n{e}"

    lineas = texto.splitlines() or ["(Archivo vacío)"]
    scroll = 0

    while True:
        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()
        alto_util = max(3, max_y - 4)

        stdscr.addstr(0, 2, f"Archivo: {os.path.basename(ruta_json)}"[: max_x - 4], color_rojo | curses.A_BOLD)
        stdscr.addstr(1, 2, "↑/↓ o j/k: bajar/subir | [0]/q: volver"[: max_x - 4], color_rojo)

        for i in range(alto_util):
            idx = scroll + i
            if idx < len(lineas):
                stdscr.addstr(2 + i, 2, lineas[idx][: max_x - 4], color_rojo)

        pie = f"Líneas {min(scroll + 1, len(lineas))}-{min(scroll + alto_util, len(lineas))} de {len(lineas)}"
        stdscr.addstr(max_y - 1, 2, pie[: max_x - 4], color_rojo | curses.A_REVERSE)
        stdscr.refresh()

        tecla = stdscr.getch()
        if tecla in (ord("0"), ord("q"), ord("Q"), 27):
            break
        elif tecla in (curses.KEY_UP, ord("k")) and scroll > 0:
            scroll -= 1
        elif tecla in (curses.KEY_DOWN, ord("j")) and scroll + alto_util < len(lineas):
            scroll += 1

def _dibujar_canchita(formacion, jugadores):
    if not jugadores:
        return []

    # Intenta leer algo tipo "4-2-3-1" o "4-3-3"
    partes = []
    if isinstance(formacion, str):
        for trozo in formacion.replace(" ", "").split("-"):
            if trozo.isdigit():
                partes.append(int(trozo))

    lineas = []
    ancho = 42
    lineas.append("+" + "-" * (ancho - 2) + "+")

    # Arquero (si hay al menos 1)
    idx = 0
    if idx < len(jugadores):
        arq = str(jugadores[idx])[:14]
        lineas.append(f"|{'[ARQ] ' + arq:^{ancho - 2}}|")
        idx += 1

    # Líneas de campo según la formación (de atrás hacia adelante)
    if partes:
        for cant in partes:
            if idx >= len(jugadores):
                break
            grupo = [str(j)[:8] for j in jugadores[idx : idx + cant]]
            idx += cant
            espacio_hueco = max(1, (ancho - 2) // max(1, len(grupo)))
            fila = [" "] * (ancho - 2)
            for i, nombre in enumerate(grupo):
                centro = int((i + 0.5) * espacio_hueco)
                inicio = max(1, min(ancho - 2 - len(nombre), centro - len(nombre) // 2))
                for c_idx, ch in enumerate(nombre):
                    if inicio + c_idx < ancho - 2:
                        fila[inicio + c_idx] = ch
            lineas.append("|" + "".join(fila) + "|")
    else:
        # Si no hay formación válida, reparte el resto en filas de a 3
        while idx < len(jugadores):
            grupo = [str(j)[:10] for j in jugadores[idx : idx + 3]]
            idx += 3
            lineas.append(f"|{'  '.join(grupo):^{ancho - 2}}|")

    # Suplentes / restantes si sobran jugadores
    if idx < len(jugadores):
        lineas.append("+" + "-" * (ancho - 2) + "+")
        lineas.append(f"|{'Suplentes / Resto':^{ancho - 2}}|")
        while idx < len(jugadores):
            supl = str(jugadores[idx])[: ancho - 6]
            lineas.append(f"|  - {supl:<{ancho - 6}}|")
            idx += 1

    lineas.append("+" + "-" * (ancho - 2) + "+")
    return lineas




def menu_jsons(stdscr, color_rojo):
    archivos = obtener_jsons()
    if not archivos:
        stdscr.erase()
        stdscr.addstr(2, 4, "No se encontraron archivos .json.", color_rojo | curses.A_BOLD)
        stdscr.addstr(4, 4, "[0] o tecla para volver...", color_rojo)
        stdscr.refresh()
        stdscr.getch()
        return

    sel = 0
    while True:
        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()
        stdscr.addstr(1, 3, "JSON - Enter: abrir | [0] Volver al menú", color_rojo | curses.A_BOLD | curses.A_UNDERLINE)

        for idx, ruta in enumerate(archivos):
            y = 3 + idx
            if y >= max_y - 3:
                break
            nombre = os.path.basename(ruta)
            if idx == sel:
                stdscr.addstr(y, 5, f"> {nombre}"[: max_x - 8], color_rojo | curses.A_REVERSE | curses.A_BOLD)
            else:
                stdscr.addstr(y, 5, f"  {nombre}"[: max_x - 8], color_rojo)

        y_volver = min(max_y - 2, 3 + len(archivos) + 1)
        stdscr.addstr(y_volver, 5, "[0] Volver al menú"[: max_x - 8], color_rojo | curses.A_BOLD)

        stdscr.refresh()
        tecla = stdscr.getch()

        if tecla in (ord("0"), ord("q"), ord("Q"), 27):
            break
        elif tecla in (curses.KEY_UP, ord("k")):
            sel = (sel - 1) % len(archivos)
        elif tecla in (curses.KEY_DOWN, ord("j")):
            sel = (sel + 1) % len(archivos)
        elif tecla in (10, 13, curses.KEY_ENTER):
            ver_contenido_json(stdscr, archivos[sel], color_rojo)


def ejecutar_externo(stdscr, comando, pausar=True):
    curses.endwin()
    try:
        subprocess.run(comando, shell=True)
    except Exception as e:
        print(f"Error al ejecutar '{comando}': {e}")
    if pausar:
        input("\nPresioná Enter para volver al menú...")
    stdscr.keypad(True)
    curses.curs_set(0)


def activar_opcion(stdscr, idx, rojo, clima_ref):
    if idx == 0:
        ejecutar_externo(stdscr, "kickoff || kickoff-cli")
    elif idx == 1:
        menu_jsons(stdscr, rojo)
    elif idx == 2:
        ruta_script = os.path.expanduser("/home/mati/alineaciones.py")
        cmd = f"python3 {ruta_script}" if os.path.exists(ruta_script) else "python3 alineaciones.py"
        ejecutar_externo(stdscr, cmd)
    elif idx == 3:
        clima_ref[0] = obtener_clima()
    elif idx == 4:
        ejecutar_externo(stdscr, "sudo reboot", pausar=False)
    elif idx == 5:
        ejecutar_externo(stdscr, "sudo poweroff", pausar=False)


def main(stdscr):
    curses.curs_set(0)
    stdscr.keypad(True)
    curses.start_color()
    curses.use_default_colors()

    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    rojo = curses.color_pair(1)

    clima_ref = [obtener_clima()]

    opciones = [
        "Abrir Kickoff",
        "Formaciones .json",
        "Abrir alineaciones.py",
        "Actualizar clima",
        "Reiniciar VM",
        "Apagar VM",
        "Salir",
    ]
    seleccion = 0

    while True:
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()

        alto_box = min(17, max_y - 2)
        ancho_box = min(54, max_x - 4)

        if alto_box < 13 or ancho_box < 32:
            stdscr.addstr(0, 0, "Ventana muy chica.", rojo | curses.A_BOLD)
            stdscr.refresh()
            stdscr.getch()
            break

        start_y = (max_y - alto_box) // 2
        start_x = (max_x - ancho_box) // 2

        box_win = curses.newwin(alto_box, ancho_box, start_y, start_x)
        box_win.keypad(True)

        fecha_hora = datetime.now().strftime("%d/%m %H:%M:%S")

        box_win.attron(rojo)
        box_win.box()

        titulo_corto = TITULO[: ancho_box - 4]
        x_titulo = max(2, (ancho_box - len(titulo_corto)) // 2)
        box_win.addstr(1, x_titulo, titulo_corto, rojo | curses.A_BOLD)

        info_top = f"{fecha_hora} | {clima_ref[0]}"[: max(1, ancho_box - 6)]
        x_info = max(2, (ancho_box - len(info_top)) // 2)
        box_win.addstr(2, x_info, info_top, rojo)

        box_win.hline(3, 1, curses.ACS_HLINE, ancho_box - 2)

        for idx, opcion in enumerate(opciones):
            y_pos = 4 + idx
            if y_pos >= alto_box - 2:
                break
            etiqueta = f"[{idx + 1}] {opcion}" if idx < 6 else f"[q] {opcion}"
            texto_op = f"> {etiqueta}" if idx == seleccion else f"  {etiqueta}"
            texto_op = texto_op[: ancho_box - 6]
            if idx == seleccion:
                box_win.addstr(y_pos, 3, texto_op, rojo | curses.A_REVERSE | curses.A_BOLD)
            else:
                box_win.addstr(y_pos, 3, texto_op, rojo)

        ayuda = "1-6 / ↑↓+Enter / [0] volver / q"[: ancho_box - 4]
        box_win.addstr(alto_box - 2, max(2, (ancho_box - len(ayuda)) // 2), ayuda, rojo | curses.A_DIM)
        box_win.attroff(rojo)

        stdscr.refresh()
        box_win.refresh()

        tecla = box_win.getch()

        if tecla in (ord("q"), ord("Q")):
            break
        elif tecla in (curses.KEY_UP, ord("k")):
            seleccion = (seleccion - 1) % len(opciones)
        elif tecla in (curses.KEY_DOWN, ord("j")):
            seleccion = (seleccion + 1) % len(opciones)
        elif tecla in (10, 13, curses.KEY_ENTER):
            if seleccion == len(opciones) - 1:
                break
            activar_opcion(stdscr, seleccion, rojo, clima_ref)
        elif ord("1") <= tecla <= ord("6"):
            idx_atajo = tecla - ord("1")
            seleccion = idx_atajo
            activar_opcion(stdscr, idx_atajo, rojo, clima_ref)


if __name__ == "__main__":
    curses.wrapper(main)

