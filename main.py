import sys
from PyQt5.QtWidgets import QApplication
from ui import MainWindow
from license_validator import LicenseValidator  # Si nécessaire

if __name__ == "__main__":
    app = QApplication(sys.argv)
    LicenseValidator.verifier_licence()  # Si nécessaire
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
