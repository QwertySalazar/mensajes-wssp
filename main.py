
import os
os.environ["QT_QPA_PLATFORM"] = "windows:dpiawareness=1"

import sys, time
import pywhatkit as kit
import pyautogui as ag
from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt

# =================== PARÁMETROS CLAVE (ajustables) ===================
OPEN_WAIT_SECONDS = 8      # 10–15 PC/Internet es normal-lenta
ENTER_DELAY_SECONDS = 7    # si queda como borrador, sube a 8–12
MIN_BETWEEN_SECONDS = 12   # no menos de 12 para estabilidad
# =====================================================================

def normaliza_numeros(cadena: str):
    bruto = cadena.replace("\n", ",").replace(" ", ",").split(",")
    nums = []
    for n in bruto:
        n = n.strip()
        if not n:
            continue
        if not n.startswith("+"):
            n = "+" + n
        nums.append(n)
    return nums

def enviar_mensajes(numeros, plantilla_a, plantilla_b, wait_between):
    ag.PAUSE = 0.5
    total = len(numeros)

    for i, numero in enumerate(numeros, start=101):
        try:
            plantilla = plantilla_a if (i % 2 == 1) else plantilla_b
            mensaje_final = f"{i}. {plantilla}"

            kit.sendwhatmsg_instantly(
                phone_no=numero,
                message=mensaje_final,
                wait_time=OPEN_WAIT_SECONDS,
                tab_close=False,
                close_time=2
            )

            time.sleep(ENTER_DELAY_SECONDS)
            ag.press("enter")  # asegurar envío
            time.sleep(max(wait_between, MIN_BETWEEN_SECONDS))
            ag.hotkey("ctrl", "w")  # cerrar pestaña
            time.sleep(1)

            print(f"[{i}/{total}] ✅ Enviado a {numero}")
        except Exception as e:
            print(f"[{i}/{total}] ⚠️ No se pudo enviar a {numero}: {e}")
            try:
                ag.hotkey("ctrl", "w")
            except Exception:
                pass
            time.sleep(3)

class MyApp(QtWidgets.QMainWindow):
    def __init__(self):
        super(MyApp, self).__init__()
        uic.loadUi("./design.ui", self)

        # Ventana sin bordes (si tu UI ya lo usa)
        self.setWindowOpacity(1)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.click_position = None

        # Crear el campo de "Mensaje B" si no existe en el .ui
        self._ensure_second_message_field()

        # Botones
        self.send.clicked.connect(self.enviar)
        self.send.clicked.connect(self.clearData)
        self.help.clicked.connect(self.abrirAyuda)
        self.btn_close.clicked.connect(lambda: self.close())

    # --- Inserta dinámicamente "mensaje2" debajo de "mensaje" ---
    def _ensure_second_message_field(self):
        if hasattr(self, "mensaje2") and self.mensaje2:
            return  # ya existe

        # Debe existir el primer campo 'mensaje' en tu .ui
        base = getattr(self, "mensaje", None)
        if base is None:
            return  # algo raro en el .ui; seguimos sin romper

        # Crear el QLineEdit clonando estilos del primero
        self.mensaje2 = QtWidgets.QLineEdit(self)
        self.mensaje2.setObjectName("mensaje2")
        self.mensaje2.setPlaceholderText("- Ingrese el mensaje B")
        try:
            self.mensaje2.setStyleSheet(base.styleSheet())
        except Exception:
            pass

        # Buscar el layout donde está 'mensaje' e insertarlo debajo
        container = base.parentWidget()
        layout = container.layout() if container else None

        if layout is None:
            # Si por algún motivo no hay layout, crea uno vertical y agrega ambos
            layout = QtWidgets.QVBoxLayout(container)
            container.setLayout(layout)
            layout.addWidget(base)
            layout.addWidget(self.mensaje2)
            return

        # Insertar justo después del 'mensaje'
        idx = None
        for i in range(layout.count()):
            w = layout.itemAt(i).widget()
            if w is base:
                idx = i
                break
        if idx is not None:
            layout.insertWidget(idx + 1, self.mensaje2)
        else:
            layout.addWidget(self.mensaje2)

        # placeholder del A 
        if not base.placeholderText():
            base.setPlaceholderText("- Ingrese el mensaje A")

    def abrirAyuda(self):
        try:
            self.ventana_ayuda = QtWidgets.QMainWindow()
            uic.loadUi("./help.ui", self.ventana_ayuda)
            self.ventana_ayuda.btn_close.clicked.connect(lambda: self.ventana_ayuda.close())
            self.ventana_ayuda.setWindowOpacity(1)
            self.ventana_ayuda.setWindowFlags(Qt.WindowType.FramelessWindowHint)
            self.ventana_ayuda.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            self.ventana_ayuda.show()
        except Exception:
            pass

    def _leer_texto(self, nombre_widget: str) -> str:
        w = getattr(self, nombre_widget, None)
        return w.text().strip() if w and hasattr(w, "text") else ""

    def enviar(self):
        mensaje_a = self._leer_texto("mensaje")
        mensaje_b = self._leer_texto("mensaje2") or mensaje_a
        wait_time_str = self._leer_texto("time")
        numeros_str   = self._leer_texto("telefonos")

        if not mensaje_a:
            self.mostrarError("Error", "Escribe el Mensaje A.")
            return

        try:
            wait_between = int(wait_time_str)
        except ValueError:
            self.mostrarError("Error", "El tiempo debe ser un número entero (segundos).")
            return

        numeros = normaliza_numeros(numeros_str)
        if not numeros:
            self.mostrarError("Error", "Ingresa al menos un número (separados por coma/espacio).")
            return

        enviar_mensajes(numeros, mensaje_a, mensaje_b, wait_between)

        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setText(f"Envío terminado a {len(numeros)} destinatarios ✅")
        msg_box.setWindowTitle("Éxito")
        msg_box.exec()

    def clearData(self):
        if hasattr(self, "telefonos"): self.telefonos.setText("")
        if hasattr(self, "mensaje"):   self.mensaje.setText("")
        if hasattr(self, "mensaje2"):  self.mensaje2.setText("")
        if hasattr(self, "time"):      self.time.setText("")

    def mostrarError(self, title, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setText(message)
        msg_box.setWindowTitle(title)
        msg_box.exec()

    # Arrastre de ventana
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.click_position = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.click_position is not None:
            self.move(self.pos() + event.globalPosition().toPoint() - self.click_position)
            self.click_position = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.click_position = None

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec())
