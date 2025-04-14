from PyQt6.QtCore import pyqtSignal, QObject

class Communicator(QObject):
    chat_msg = pyqtSignal(str, str)
    chat_img = pyqtSignal(int)

comm = Communicator()