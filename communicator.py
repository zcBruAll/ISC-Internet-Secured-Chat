from PyQt6.QtCore import pyqtSignal, QObject

# Define a new class called 'Communicator' that inherits from QObject,
# which means it will be able to use Qt's signal and slot mechanism.
class Communicator(QObject):
    chat_msg = pyqtSignal(str, str)
    
    chat_img = pyqtSignal(int)

# Create an instance of the Communicator class.
comm = Communicator()
