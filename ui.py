# ui.py

import sys
from math import ceil
from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QWidget, QGroupBox, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QCheckBox, QProgressBar, QFileDialog
)
from PyQt5.QtGui import QFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import matplotlib.patches as patches
from matplotlib.backends.backend_pdf import PdfPages

from reportlab.pdfgen import canvas as rcanvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

import textwrap

# Import de la logique
from logic import Panneau, RectanglePCB, PlacementPCB, calcul_pourcentage_remplissage, calcul_panneaux_necessaires

class MplCanvas(FigureCanvasQTAgg):
    """
    Classe pour intégrer une figure Matplotlib dans PyQt5.
    """
    def __init__(self, parent=None, width=15, height=85, dpi=100):
        fig, self.axes = plt.subplots(2, 2, figsize=(width, height), dpi=dpi)
        super().__init__(fig)
        self.setParent(parent)
        plt.close(fig)

class MainWindow(QMainWindow):
    """
    Classe principale de l'application.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Panélisation PCB | William-Dew")
        self.setGeometry(100, 100, 1600, 900)

        # Variables par défaut
        self.largeur_pcb = 0
        self.hauteur_pcb = 0
        self.espacement = 5
        self.bordure = 15
        self.nombre_pcb_a_fabriquer = 1
        self.pourcentage_surlancement = 5
        self.allow_rotation = True
        self.panneaux_largeurs = [600, 580, 570, 457]
        self.panneaux_hauteurs = [500, 510, 480, 300]
        self.resultats = []

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        input_layout = QVBoxLayout()
        main_layout.addLayout(input_layout, 15)

        right_layout = QVBoxLayout()
        main_layout.addLayout(right_layout, 85)

        # Groupe PCB
        pcb_group = QGroupBox("Dimensions du PCB")
        input_layout.addWidget(pcb_group)
        pcb_layout = QVBoxLayout()
        pcb_group.setLayout(pcb_layout)
        pcb_dimensions_layout = QHBoxLayout()
        pcb_layout.addLayout(pcb_dimensions_layout)
        self.largeur_pcb_input = QLineEdit(str(self.largeur_pcb))
        self.hauteur_pcb_input = QLineEdit(str(self.hauteur_pcb))
        self.largeur_pcb_input.setMaximumWidth(60)
        self.hauteur_pcb_input.setMaximumWidth(60)
        pcb_dimensions_layout.addWidget(QLabel("Dimension :"))
        pcb_dimensions_layout.addWidget(self.largeur_pcb_input)
        pcb_dimensions_layout.addWidget(QLabel("x"))
        pcb_dimensions_layout.addWidget(self.hauteur_pcb_input)
        pcb_dimensions_layout.addWidget(QLabel("mm"))

        # Groupe espacement
        espacement_group = QGroupBox("Entraxe")
        input_layout.addWidget(espacement_group)
        espacement_layout = QHBoxLayout()
        espacement_group.setLayout(espacement_layout)
        self.espacement_input = QLineEdit(str(self.espacement))
        self.espacement_input.setMaximumWidth(60)
        espacement_layout.addWidget(QLabel("Entraxe (mm) :"))
        espacement_layout.addWidget(self.espacement_input)

        # Groupe production
        production_group = QGroupBox("Production")
        input_layout.addWidget(production_group)
        production_layout = QHBoxLayout()
        production_group.setLayout(production_layout)
        self.nombre_pcb_input = QLineEdit(str(self.nombre_pcb_a_fabriquer))
        self.pourcentage_surlancement_input = QLineEdit(str(self.pourcentage_surlancement))
        self.nombre_pcb_input.setMaximumWidth(60)
        self.pourcentage_surlancement_input.setMaximumWidth(60)
        production_dimensions_layout = QHBoxLayout()
        production_layout.addLayout(production_dimensions_layout)
        production_dimensions_layout.addWidget(QLabel("Qté Pcb :"))
        production_dimensions_layout.addWidget(self.nombre_pcb_input)
        production_dimensions_layout.addWidget(QLabel("Casse (%) :"))
        production_dimensions_layout.addWidget(self.pourcentage_surlancement_input)

        # Checkbox rotation
        self.mode_mix_checkbox = QCheckBox("Mode Mixte")
        self.mode_mix_checkbox.setChecked(True)
        input_layout.addWidget(self.mode_mix_checkbox)

        # Groupe bordure
        bordure_group = QGroupBox("Bordure du Panneau")
        input_layout.addWidget(bordure_group)
        bordure_layout = QHBoxLayout()
        bordure_group.setLayout(bordure_layout)
        self.bordure_input = QLineEdit(str(self.bordure))
        self.bordure_input.setMaximumWidth(60)
        bordure_layout.addWidget(QLabel("Bordure (mm) :"))
        bordure_layout.addWidget(self.bordure_input)

        # Panneaux
        self.panneaux_largeurs_inputs = []
        self.panneaux_hauteurs_inputs = []
        for i in range(4):
            panneau_group = QGroupBox(f"Dimensions du Panneau {i+1}")
            input_layout.addWidget(panneau_group)
            panneau_layout = QVBoxLayout()
            panneau_group.setLayout(panneau_layout)
            panneau_dimensions_layout = QHBoxLayout()
            panneau_layout.addLayout(panneau_dimensions_layout)
            largeur_input = QLineEdit(str(self.panneaux_largeurs[i]))
            hauteur_input = QLineEdit(str(self.panneaux_hauteurs[i]))
            largeur_input.setMaximumWidth(60)
            hauteur_input.setMaximumWidth(60)
            self.panneaux_largeurs_inputs.append(largeur_input)
            self.panneaux_hauteurs_inputs.append(hauteur_input)
            panneau_dimensions_layout.addWidget(QLabel("Dimension :"))
            panneau_dimensions_layout.addWidget(largeur_input)
            panneau_dimensions_layout.addWidget(QLabel("x"))
            panneau_dimensions_layout.addWidget(hauteur_input)
            panneau_dimensions_layout.addWidget(QLabel("mm"))

        # Canvas
        self.canvas = MplCanvas(width=15, height=85, dpi=100)
        right_layout.addWidget(self.canvas)

        # Tableau résultats
        self.table_widget = QTableWidget()
        right_layout.addWidget(self.table_widget)

        font = QFont()
        font.setPointSize(10)
        self.setFont(font)

        # Bouton calculer
        calculer_button = QPushButton("Calculer")
        calculer_button.clicked.connect(self.calculer_et_visualiser)
        calculer_button.setDefault(True)
        input_layout.addWidget(calculer_button)

        # Bouton export PDF
        export_pdf_button = QPushButton("Exporter en PDF")
        export_pdf_button.clicked.connect(self.exporter_pdf)
        input_layout.addWidget(export_pdf_button)

        # Bouton reset
        reset_button = QPushButton("Nouvelle Configuration")
        reset_button.clicked.connect(self.nouvelle_configuration)
        input_layout.addWidget(reset_button)

        # Return pressed
        self.largeur_pcb_input.returnPressed.connect(calculer_button.click)
        self.hauteur_pcb_input.returnPressed.connect(calculer_button.click)
        self.espacement_input.returnPressed.connect(calculer_button.click)
        self.nombre_pcb_input.returnPressed.connect(calculer_button.click)
        self.pourcentage_surlancement_input.returnPressed.connect(calculer_button.click)
        self.bordure_input.returnPressed.connect(calculer_button.click)
        for largeur_input, hauteur_input in zip(self.panneaux_largeurs_inputs, self.panneaux_hauteurs_inputs):
            largeur_input.returnPressed.connect(calculer_button.click)
            hauteur_input.returnPressed.connect(calculer_button.click)

    def valider_entrees(self):
        valeurs = {}
        valeurs['largeur_pcb'] = float(self.largeur_pcb_input.text())
        valeurs['hauteur_pcb'] = float(self.hauteur_pcb_input.text())
        valeurs['espacement'] = float(self.espacement_input.text())
        valeurs['bordure'] = float(self.bordure_input.text())
        valeurs['nombre_pcb_a_fabriquer'] = int(self.nombre_pcb_input.text())
        valeurs['pourcentage_surlancement'] = float(self.pourcentage_surlancement_input.text())
        valeurs['allow_rotation'] = self.mode_mix_checkbox.isChecked()

        valeurs['panneaux_largeurs'] = [float(input.text()) for input in self.panneaux_largeurs_inputs]
        valeurs['panneaux_hauteurs'] = [float(input.text()) for input in self.panneaux_hauteurs_inputs]

        # Vérifications
        if any(v <= 0 for v in [valeurs['largeur_pcb'], valeurs['hauteur_pcb'], valeurs['espacement'], valeurs['bordure'], valeurs['nombre_pcb_a_fabriquer']]):
            raise ValueError("Les valeurs doivent être positives et non nulles.")
        if any(l <= 0 for l in valeurs['panneaux_largeurs']):
            raise ValueError("La largeur des panneaux doit être positive.")
        if any(h <= 0 for h in valeurs['panneaux_hauteurs']):
            raise ValueError("La hauteur des panneaux doit être positive.")

        return valeurs

    def calculer_et_visualiser(self):
        try:
            val = self.valider_entrees()
            self.largeur_pcb = val['largeur_pcb']
            self.hauteur_pcb = val['hauteur_pcb']
            self.espacement = val['espacement']
            self.bordure = val['bordure']
            self.nombre_pcb_a_fabriquer = val['nombre_pcb_a_fabriquer']
            self.pourcentage_surlancement = val['pourcentage_surlancement']
            self.allow_rotation = val['allow_rotation']
            self.panneaux_largeurs = val['panneaux_largeurs']
            self.panneaux_hauteurs = val['panneaux_hauteurs']

            pcb_prototype = RectanglePCB(self.largeur_pcb, self.hauteur_pcb)

            nombre_total_pcb = ceil(self.nombre_pcb_a_fabriquer * (1 + self.pourcentage_surlancement / 100))

            panneaux = []
            placements = []
            self.resultats.clear()

            for i in range(4):
                panneau = Panneau(self.panneaux_largeurs[i], self.panneaux_hauteurs[i], self.bordure)
                panneaux.append(panneau)

                placement = PlacementPCB(panneau, pcb_prototype, self.espacement, allow_rotation=self.allow_rotation)
                placement.calculer_meilleur_placement()
                placements.append(placement)

                pourcentage_remplissage = calcul_pourcentage_remplissage(placement.surface_occupee, panneau.surface_utilisable)
                nombre_panneaux_necessaires = calcul_panneaux_necessaires(nombre_total_pcb, placement.nombre_pcb)
                quantite_produite = placement.nombre_pcb * nombre_panneaux_necessaires

                self.resultats.append({
                    'panneau': i + 1,
                    'dimensions_totales': f"{panneau.largeur_totale} x {panneau.hauteur_totale}",
                    'dimensions_utilisables': f"{panneau.largeur} x {panneau.hauteur}",
                    'nombre_pcb': placement.nombre_pcb,
                    'pourcentage_remplissage': pourcentage_remplissage,
                    'nombre_panneaux_necessaires': nombre_panneaux_necessaires,
                    'quantite_produite': quantite_produite
                })

            self.visualiser_placements(panneaux, placements)
            self.afficher_recapitulatif()

        except ValueError as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def visualiser_placements(self, panneaux, placements):
        for ax_row in self.canvas.axes:
            for ax in ax_row:
                ax.clear()

        for idx, (panneau, placement) in enumerate(zip(panneaux, placements)):
            ax = self.canvas.axes[idx // 2][idx % 2]
            rectangles = placement.rectangles

            panneau_patch = patches.Rectangle((0, 0), panneau.largeur_totale, panneau.hauteur_totale,
                                              linewidth=1, edgecolor='black', facecolor='lightgray', alpha=0.3)
            ax.add_patch(panneau_patch)

            surface_utilisable_patch = patches.Rectangle((panneau.bordure, panneau.bordure), panneau.largeur, panneau.hauteur,
                                                         linewidth=1, edgecolor='black', facecolor='none')
            ax.add_patch(surface_utilisable_patch)

            for rect in rectangles:
                couleur = 'blue' if rect.rotation == 0 else 'green'
                rectangle_patch = patches.Rectangle((rect.x, rect.y), rect.largeur, rect.hauteur,
                                                    linewidth=1, edgecolor='black', facecolor=couleur, alpha=0.6)
                ax.add_patch(rectangle_patch)

            ax.set_xlim(0, panneau.largeur_totale)
            ax.set_ylim(0, panneau.hauteur_totale)
            ax.set_aspect('equal', adjustable='box')
            ax.set_title(f"Format {idx +1} : {panneau.largeur_totale} x {panneau.hauteur_totale} : x{placement.nombre_pcb} PCB")
            ax.axis('off')

        self.canvas.draw()

    def afficher_recapitulatif(self):
        columns = [
            'Panneau',
            'Dimensions Totales',
            'Dimensions Utilisables',
            'PCB par Panneau',
            'Remplissage (%)',
            'Panneaux Nécessaires',
            'Quantité Produite'
        ]
        self.table_widget.setRowCount(len(self.resultats))
        self.table_widget.setColumnCount(len(columns))
        self.table_widget.setHorizontalHeaderLabels(columns)
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for row, result in enumerate(self.resultats):
            self.table_widget.setItem(row, 0, QTableWidgetItem(str(result['panneau'])))
            self.table_widget.setItem(row, 1, QTableWidgetItem(result['dimensions_totales']))
            self.table_widget.setItem(row, 2, QTableWidgetItem(result['dimensions_utilisables']))
            self.table_widget.setItem(row, 3, QTableWidgetItem(str(result['nombre_pcb'])))

            remplissage = result['pourcentage_remplissage']
            progress_bar = QProgressBar()
            progress_bar.setValue(int(remplissage))
            progress_bar.setAlignment(QtCore.Qt.AlignCenter)
            if remplissage >= 75:
                progress_bar.setStyleSheet("QProgressBar::chunk { background-color: green; }")
            elif 60 <= remplissage < 75:
                progress_bar.setStyleSheet("QProgressBar::chunk { background-color: yellow; }")
            else:
                progress_bar.setStyleSheet("QProgressBar::chunk { background-color: red; }")
            self.table_widget.setCellWidget(row, 4, progress_bar)

            self.table_widget.setItem(row, 5, QTableWidgetItem(str(result['nombre_panneaux_necessaires'])))
            self.table_widget.setItem(row, 6, QTableWidgetItem(str(result['quantite_produite'])))

        row_height = 25
        self.table_widget.verticalHeader().setDefaultSectionSize(row_height)
        self.table_widget.resizeRowsToContents()

        total_height = 200
        self.table_widget.setFixedHeight(total_height)

    def nouvelle_configuration(self):
        self.largeur_pcb_input.clear()
        self.hauteur_pcb_input.clear()
        self.espacement_input.setText(str(5))
        self.bordure_input.setText(str(15))
        self.nombre_pcb_input.setText(str(1))
        self.pourcentage_surlancement_input.setText(str(5))
        self.mode_mix_checkbox.setChecked(True)

        valeurs_largeurs = [600, 580, 570, 457]
        valeurs_hauteurs = [500, 510, 480, 300]
        for i in range(4):
            self.panneaux_largeurs_inputs[i].setText(str(valeurs_largeurs[i]))
            self.panneaux_hauteurs_inputs[i].setText(str(valeurs_hauteurs[i]))

        for ax_row in self.canvas.axes:
            for ax in ax_row:
                ax.clear()
        self.canvas.draw()

        self.table_widget.clearContents()
        self.table_widget.setRowCount(0)

    

    def exporter_pdf(self):
        """
        Exporte la figure et le récapitulatif en PDF.
        """
        if not self.resultats:
            QMessageBox.warning(self, "Avertissement", "Aucun résultat à exporter. Veuillez d'abord calculer.")
            return

        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(self, "Exporter en PDF", "", "PDF Files (*.pdf)", options=options)
        if not filename:
            return

        with PdfPages(filename) as pdf:
            # Page 1 : la figure des panneaux
            pdf.savefig(self.canvas.figure)

            # Page 2 : Récapitulatif détaillé en plusieurs lignes
            fig2 = plt.figure(figsize=(8.27, 11.7))  # Format A4 approximatif
            plt.axis('off')
            y = 1
            plt.text(0.1, y, "Récapitulatif de la panélisation", fontsize=14, fontweight='bold')
            y -= 0.05

            # Pour chaque résultat, on affiche plusieurs lignes
            for res in self.resultats:
                lines = [
                    f"Panneau {res['panneau']}:",
                    f"    Dimensions Totales: {res['dimensions_totales']}",
                    f"    Dimensions Utilisables: {res['dimensions_utilisables']}",
                    f"    PCB par Panneau: {res['nombre_pcb']}",
                    f"    Remplissage: {res['pourcentage_remplissage']:.2f}%",
                    f"    Panneaux Nécessaires: {res['nombre_panneaux_necessaires']}",
                    f"    Quantité Produite: {res['quantite_produite']}"
                ]

                for line in lines:
                    plt.text(0.1, y, line, fontsize=10)
                    y -= 0.02
                y -= 0.03  # espace supplémentaire entre les différents panneaux

            pdf.savefig(fig2)
            plt.close(fig2)

        QMessageBox.information(self, "Information", f"Fichier PDF exporté : {filename}")

