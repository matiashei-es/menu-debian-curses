import curses
import glob
import json
import os
import subprocess

TITULO = "FULBO DEBI - MATI"


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
        stdscr.addstr(1, 2, "↑/↓ o j/k: bajar/subir | q: volver"[: max_x - 4], color_rojo)

        for i in range(alto_util):
            idx = scroll + i
            if idx < len(lineas):
                stdscr.addstr(2 + i, 2, lineas[idx][: max_x - 4], color_rojo)

        pie = f"Líneas {min(scroll + 1, len(lineas))}-{min(scroll + alto_util, len(lineas))} de {len(lineas)}"
        stdscr.addstr(max_y - 1, 2, pie[: max_x - 4], color_rojo | curses.A_REVERSE)
        stdscr.refresh()

        tecla = stdscr.getch()
        if tecla in (ord("q"), ord("Q"), 27):
            break
        elif tecla in (curses.KEY_UP, ord("k")) and scroll > 0:
            scroll -= 1
        elif tecla in (curses.KEY_DOWN, ord("j")) and scroll + alto_util < len(lineas):
            scroll += 1


def menu_jsons(stdscr, color_rojo):
    archivos = obtener_jsons()
    if not archivos:
        stdscr.erase()
        stdscr.addstr(2, 4, "No se encontraron archivos .json.", color_rojo | curses.A_BOLD)
        stdscr.addstr(4, 4, "Tecla para volver...", color_rojo)
        stdscr.refresh()
        stdscr.getch()
        return

    sel = 0
    while True:
        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()
        stdscr.addstr(1, 3, "JSON - Enter: abrir | q: volver", color_rojo | curses.A_BOLD | curses.A_UNDERLINE)

        for idx, ruta in enumerate(archivos):
            y = 3 + idx
            if y >= max_y - 2:
                break
            nombre = os.path.basename(ruta)
            if idx == sel:
                stdscr.addstr(y, 5, f"> {nombre}"[: max_x - 8], color_rojo | curses.A_REVERSE | curses.A_BOLD)
            else:
                stdscr.addstr(y, 5, f"  {nombre}"[: max_x - 8], color_rojo)

        stdscr.refresh()
        tecla = stdscr.getch()

        if tecla in (ord("q"), ord("Q"), 27):
            break
        elif tecla in (curses.KEY_UP, ord("k")):
            sel = (sel - 1) % len(archivos)
        elif tecla in (curses.KEY_DOWN, ord("j")):
            sel = (sel + 1) % len(archivos)
        elif tecla in (10, 13, curses.KEY_ENTER):
            ver_contenido_json(stdscr, archivos[sel], color_rojo)


def ejecutar_externo(stdscr, comando):
    curses.endwin()
    try:
        subprocess.run(comando, shell=True)
    except Exception as e:
        print(f"Error al ejecutar '{comando}': {e}")
    input("\nPresioná Enter para volver al menú...")
    stdscr.keypad(True)
    curses.curs_set(0)


def main(stdscr):
    curses.curs_set(0)
    stdscr.keypad(True)
    curses.start_color()
    curses.use_default_colors()

    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    rojo = curses.color_pair(1)

    opciones = [
        "Abrir Kickoff",
        "Formaciones .json",
        "Abrir alineaciones.py",
        "Salir",
    ]
    seleccion = 0

    while True:
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()

        alto_box = min(13, max_y - 2)
        ancho_box = min(46, max_x - 4)

        if alto_box < 9 or ancho_box < 28:
            stdscr.addstr(0, 0, "Ventana muy chica.", rojo | curses.A_BOLD)
            stdscr.refresh()
            stdscr.getch()
            break

        start_y = (max_y - alto_box) // 2
        start_x = (max_x - ancho_box) // 2

        box_win = curses.newwin(alto_box, ancho_box, start_y, start_x)
        box_win.keypad(True)

        box_win.attron(rojo)
        box_win.box()
        titulo_corto = TITULO[: ancho_box - 4]
        x_titulo = max(2, (ancho_box - len(titulo_corto)) // 2)
        box_win.addstr(1, x_titulo, titulo_corto, rojo | curses.A_BOLD)
        box_win.hline(2, 1, curses.ACS_HLINE, ancho_box - 2)

        for idx, opcion in enumerate(opciones):
            y_pos = 4 + idx
            if y_pos >= alto_box - 2:
                break
            texto_op = f"> {opcion}" if idx == seleccion else f"  {opcion}"
            texto_op = texto_op[: ancho_box - 6]
            if idx == seleccion:
                box_win.addstr(y_pos, 3, texto_op, rojo | curses.A_REVERSE | curses.A_BOLD)
            else:
                box_win.addstr(y_pos, 3, texto_op, rojo)

        ayuda = "↑/↓ + Enter"[: ancho_box - 4]
        box_win.addstr(alto_box - 2, max(2, (ancho_box - len(ayuda)) // 2), ayuda, rojo | curses.A_DIM)
        box_win.attroff(rojo)

        stdscr.refresh()
        box_win.refresh()

        tecla = box_win.getch()

        if tecla in (curses.KEY_UP, ord("k")):
            seleccion = (seleccion - 1) % len(opciones)
        elif tecla in (curses.KEY_DOWN, ord("j")):
            seleccion = (seleccion + 1) % len(opciones)
        elif tecla in (10, 13, curses.KEY_ENTER):
            if seleccion == len(opciones) - 1:
                break
            elif seleccion == 0:
                ejecutar_externo(stdscr, "kickoff || kickoff-cli")
            elif seleccion == 1:
                menu_jsons(stdscr, rojo)
            elif seleccion == 2:
                ruta_script = os.path.expanduser("~/Alineaciones-Fut/alineaciones.py")
                cmd = f"python3 {ruta_script}" if os.path.exists(ruta_script) else "python3 alineaciones.py"
                ejecutar_externo(stdscr, cmd)


if __name__ == "__main__":
    curses.wrapper(main)
