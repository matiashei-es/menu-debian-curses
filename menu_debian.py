import curses
import glob
import json
import os
import subprocess


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


def ver_contenido_json(stdscr, ruta_json):
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

        stdscr.addstr(0, 2, f"Archivo: {os.path.basename(ruta_json)}"[: max_x - 4], curses.A_BOLD)
        stdscr.addstr(1, 2, "↑/↓ o j/k: desplazar | q o ESC: volver"[: max_x - 4], curses.A_DIM)

        for i in range(alto_util):
            idx = scroll + i
            if idx < len(lineas):
                stdscr.addstr(2 + i, 2, lineas[idx][: max_x - 4])

        stdscr.addstr(max_y - 1, 2, f"Líneas {min(scroll + 1, len(lineas))}-{min(scroll + alto_util, len(lineas))} de {len(lineas)}"[: max_x - 4], curses.A_REVERSE)
        stdscr.refresh()

        tecla = stdscr.getch()
        if tecla in (ord("q"), ord("Q"), 27):
            break
        elif tecla in (curses.KEY_UP, ord("k")) and scroll > 0:
            scroll -= 1
        elif tecla in (curses.KEY_DOWN, ord("j")) and scroll + alto_util < len(lineas):
            scroll += 1


def menu_jsons(stdscr):
    archivos = obtener_jsons()
    if not archivos:
        stdscr.erase()
        stdscr.addstr(2, 4, "No se encontraron archivos .json.", curses.A_BOLD)
        stdscr.addstr(4, 4, "Presioná cualquier tecla para volver...", curses.A_DIM)
        stdscr.refresh()
        stdscr.getch()
        return

    sel = 0
    while True:
        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()

        stdscr.addstr(1, 3, "FORMACIONES (.json) - Enter para abrir | q para volver", curses.A_BOLD | curses.A_UNDERLINE)

        for idx, ruta in enumerate(archivos):
            y = 3 + idx
            if y >= max_y - 2:
                break
            nombre = os.path.basename(ruta)
            if idx == sel:
                stdscr.attron(curses.A_REVERSE | curses.A_BOLD)
                stdscr.addstr(y, 5, f"> {nombre}"[: max_x - 8])
                stdscr.attroff(curses.A_REVERSE | curses.A_BOLD)
            else:
                stdscr.addstr(y, 5, f"  {nombre}"[: max_x - 8])

        stdscr.refresh()
        tecla = stdscr.getch()

        if tecla in (ord("q"), ord("Q"), 27):
            break
        elif tecla in (curses.KEY_UP, ord("k")):
            sel = (sel - 1) % len(archivos)
        elif tecla in (curses.KEY_DOWN, ord("j")):
            sel = (sel + 1) % len(archivos)
        elif tecla in (10, 13, curses.KEY_ENTER):
            ver_contenido_json(stdscr, archivos[sel])


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

    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_GREEN)
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)

    opciones = [
        "Abrir Kickoff",
        "Listar Formaciones (.json)",
        "Abrir Alineaciones (alineaciones.py)",
        "Salir",
    ]
    seleccion = 0

    while True:
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()

        if max_y < 14 or max_x < 55:
            stdscr.attron(curses.color_pair(5))
            stdscr.addstr(0, 0, "Terminal muy chica. Agrandá la ventana (mínimo 55x14).")
            stdscr.attroff(curses.color_pair(5))
            stdscr.refresh()
            stdscr.getch()
            break

        header_h = 3
        footer_h = 3
        body_h = max_y - header_h - footer_h

        header_win = stdscr.derwin(header_h, max_x, 0, 0)
        body_win = stdscr.derwin(body_h, max_x, header_h, 0)
        footer_win = stdscr.derwin(footer_h, max_x, max_y - footer_h, 0)

        header_win.bkgd(" ", curses.color_pair(1))
        header_win.box()
        titulo = "DEBIAN 13 - MENÚ FÚTBOL"
        header_win.addstr(1, max(2, (max_x // 2) - (len(titulo) // 2)), titulo, curses.A_BOLD)

        body_win.bkgd(" ", curses.color_pair(2))
        body_win.box()
        body_win.addstr(2, 4, "Movete con ↑ / ↓ (o j / k) y presioná Enter:", curses.A_UNDERLINE)

        for idx, opcion in enumerate(opciones):
            y_pos = 4 + idx
            if idx == seleccion:
                body_win.attron(curses.color_pair(3) | curses.A_BOLD)
                body_win.addstr(y_pos, 6, f"> {opcion} ")
                body_win.attroff(curses.color_pair(3) | curses.A_BOLD)
            else:
                body_win.addstr(y_pos, 6, f"  {opcion} ", curses.color_pair(2))

        footer_win.bkgd(" ", curses.color_pair(4))
        footer_win.box()
        footer_win.addstr(1, 2, f"Seleccionado: {opciones[seleccion]}"[: max_x - 4], curses.A_BOLD)

        stdscr.refresh()
        tecla = stdscr.getch()

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
                menu_jsons(stdscr)
            elif seleccion == 2:
                ruta_script = os.path.expanduser("~/Alineaciones-Fut/alineaciones.py")
                cmd = f"python3 {ruta_script}" if os.path.exists(ruta_script) else "python3 alineaciones.py"
                ejecutar_externo(stdscr, cmd)


if __name__ == "__main__":
    curses.wrapper(main)
