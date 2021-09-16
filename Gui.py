from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout


class Gui:
    def __init__(self):
        self.app = QApplication([])
        window = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QPushButton('Top'))
        layout.addWidget(QPushButton('Bottom'))
        window.setLayout(layout)
        window.show()

    def exec(self):
        self.app.exec()
