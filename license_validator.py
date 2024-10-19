from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMessageBox
import sys

class LicenseValidator:
    """
    Classe pour vérifier la date d'expiration de la licence.
    """
    DATE_EXPIRATION = "2024-12-31"

    @staticmethod
    def verifier_licence():
        date_actuelle = datetime.now().date()
        date_limite = datetime.strptime(LicenseValidator.DATE_EXPIRATION, "%Y-%m-%d").date()

        if date_actuelle > date_limite:
          
            # Affiche une fenêtre d'alerte indiquant l'expiration de la licence
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("La licence de ce programme a expiré.")
            msg.setInformativeText("Veuillez contacter l'administrateur pour renouveler votre licence.")
            msg.setWindowTitle("Licence Expirée")
            msg.exec_()
            sys.exit()
