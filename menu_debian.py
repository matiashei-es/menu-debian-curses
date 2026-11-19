import curses
import glob
import os
import subprocess


def obtener_jsons():
    rutas = ["*.json", os.path.expanduser("~/Alineaciones-Fut/*.json")]
    archivos = []
    for ruta in rutas:
        archivos.extend(glob.glob(ruta))
    return sorted(list(set(os.path.basename(f) for f in archivos)))


def mostrar_pantalla(body_win, titulo, lineas):
    body_win.erase()
    body_win.box()
    body_win.addstr(2, 4, titulo, curses.A_BOLD | curses.A_UNDERLINE)
    for idx, linea in enumerate(lineas):
        body_win.addstr(4 + idx, 4, linea[:60])
    body_win.addstr(12, 4, "Presioná cualquier tecla para volver al menú...", curses.A_DIM)
    body_win.refresh()
    body_win.getch()


def main(stdscr):
    curses.curs_set(0)
    stdscr.keypad(True)
    curses.start_color()

    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)    # Header
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)   # Body
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_GREEN)   # Opción activa
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_WHITE)   # Footer
    curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)     # Alerta tamaño

    opciones = [
        "Ver Banner y Estado",
        "Listar Formaciones (.json)",
        "Abrir Alineaciones (alineaciones.py)",
        "Salir",
    ]
    seleccion = 0

    while True:
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()

        if max_y < 16 or max_x < 65:
            stdscr.attron(curses.color_pair(5))
            stdscr.addstr(0, 0, "Terminal muy chica. Agrandá la ventana (mínimo 65x16).")
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

        # Header
        header_win.bkgd(" ", curses.color_pair(1))
        header_win.box()
        titulo_hdr = "DEBIAN 13 - MENÚ FÚTBOL"
        pos_x = max(2, (max_x // 2) - (len(titulo_hdr) // 2))
        header_win.addstr(1, pos_x, titulo_hdr, curses.A_BOLD)

        # Body
        body_win.bkgd(" ", curses.color_pair(2))
        body_win.box()
        body_win.addstr(2, 4, "Movete con ↑ / ↓ (o j / k) y presioná Enter:", curses.A_UNDERLINE)

        inicio_y = 4
        for idx, opcion in enumerate(opciones):
            y_pos = inicio_y + idx
            x_pos = 6
            if idx == seleccion:
                body_win.attron(curses.color_pair(3) | curses.A_BOLD)
                body_win.addstr(y_pos, x_pos, f"> {opcion} ")
                body_win.attroff(curses.color_pair(3) | curses.A_BOLD)
            else:
                body_win.addstr(y_pos, x_pos, f"  {opcion} ", curses.color_pair(2))

        # Footer
        footer_win.bkgd(" ", curses.color_pair(4))
        footer_win.box()
        footer_win.addstr(1, 2, f"Seleccionado: {opciones[seleccion]}", curses.A_BOLD)
        if max_x > 30:
            footer_win.addstr(1, max_x - 26, "Controles: ↑, ↓, Enter", curses.A_DIM)

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
                jsons = obtener_jsons()
                mostrar_pantalla(
                    body_win,
                    "ESTADO DEL SISTEMA",
                    [
                        "Sistema: Debian 13 (Python 3.13)",
                        f"Archivos .json detectados: {len(jsons)}",
                        "Alias activos: alineaciones / abrir",
                    ],
                )
            elif seleccion == 1:
                jsons = obtener_jsons()
                lineas = jsons if jsons else ["No se encontraron archivos .json todavía."]
                mostrar_pantalla(body_win, "FORMACIONES GUARDADAS", lineas)
            elif seleccion == 2:
                # Salimos temporalmente de curses para ejecutar alineaciones.py con input() normal
                curses.endwin()
                ruta_script = os.path.expanduser("~/Alineaciones-Fut/alineaciones.py")
                if os.path.exists(ruta_script):
                    subprocess.run(["python3", ruta_script])
                else:
                    subprocess.run(["python3", "alineaciones.py"])
                stdscr.keypad(True)
                curses.curs_set(0)


if __name__ == "__main__":
    curses.wrapper(main)
