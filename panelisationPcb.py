import sys
from math import floor, ceil
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QWidget, QGroupBox, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QCheckBox, QProgressBar
)
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PyQt5.QtWidgets import QMessageBox
from license_validator import LicenseValidator


class RectanglePCB:
    """
    Classe représentant un PCB avec ses dimensions, sa position et son orientation.
    """
    def __init__(self, largeur, hauteur, x=0, y=0, rotation=0):
        self.largeur = largeur  # Largeur du PCB
        self.hauteur = hauteur  # Hauteur du PCB
        self.x = x              # Position en X sur le panneau
        self.y = y              # Position en Y sur le panneau
        self.rotation = rotation  # Orientation du PCB (0 ou 90 degrés)

    def rotate(self):
        """
        Fait pivoter le PCB de 90 degrés en échangeant largeur et hauteur.
        """
        self.largeur, self.hauteur = self.hauteur, self.largeur
        self.rotation = (self.rotation + 90) % 180  # Mise à jour de l'angle de rotation

    def copy(self):
        """
        Crée une copie du PCB pour éviter de modifier l'original.
        """
        return RectanglePCB(self.largeur, self.hauteur, self.x, self.y, self.rotation)

class Panneau:
    """
    Classe représentant le panneau sur lequel les PCB sont placés, en considérant les bordures.
    """
    def __init__(self, largeur_totale, hauteur_totale, bordure=15):
        self.largeur_totale = largeur_totale  # Largeur totale du panneau
        self.hauteur_totale = hauteur_totale  # Hauteur totale du panneau
        self.bordure = bordure                # Largeur de la bordure

        # Calcul de la surface utilisable en soustrayant les bordures des deux côtés
        self.largeur = self.largeur_totale - 2 * self.bordure
        self.hauteur = self.hauteur_totale - 2 * self.bordure
        self.surface_utilisable = self.largeur * self.hauteur  # Surface utilisable du panneau

class PlacementPCB:
    """
    Classe gérant le placement des PCB sur le panneau, y compris les rotations et les retraits.
    """
    def __init__(self, panneau, pcb_prototype, espacement=0, allow_rotation=True):
        self.panneau = panneau              # Instance du panneau
        self.pcb_prototype = pcb_prototype  # Prototype du PCB à placer
        self.espacement = espacement        # Espacement entre les PCB
        self.allow_rotation = allow_rotation  # Indique si les rotations sont autorisées
        self.rectangles = []                # Liste des PCB placés
        self.surface_occupee = 0            # Surface totale occupée par les PCB
        self.nombre_pcb = 0                 # Nombre de PCB placés

    def calculer_meilleur_placement(self):
        """
        Calcule le meilleur placement possible en testant toutes les configurations.
        """
        meilleures_rectangles = []
        max_pcb = 0
        max_surface_occupee = 0

        # Liste des configurations à tester
        if self.allow_rotation:
            configurations = [
                {'cas': 1, 'retrait': None},
                {'cas': 1, 'retrait': 'colonne'},
                {'cas': 1, 'retrait': 'rangée'},
                {'cas': 2, 'retrait': None},
                {'cas': 2, 'retrait': 'colonne'},
                {'cas': 2, 'retrait': 'rangée'},
            ]
        else:
            configurations = [
                {'cas': 1, 'retrait': None},
                {'cas': 1, 'retrait': 'colonne'},
                {'cas': 1, 'retrait': 'rangée'},
            ]

        # Tester chaque configuration
        for config in configurations:
            self.rectangles.clear()
            self.calculer_placement(cas=config['cas'], retrait=config['retrait'])

            nombre_pcb = len(self.rectangles)
            surface_occupee = sum(rect.largeur * rect.hauteur for rect in self.rectangles)

            if nombre_pcb > max_pcb or (nombre_pcb == max_pcb and surface_occupee > max_surface_occupee):
                max_pcb = nombre_pcb
                max_surface_occupee = surface_occupee
                meilleures_rectangles = self.rectangles.copy()

        # Utiliser le meilleur placement trouvé
        self.rectangles = meilleures_rectangles
        self.nombre_pcb = max_pcb  # Stocker le nombre de PCB placés
        self.surface_occupee = max_surface_occupee  # Stocker la surface occupée

    def calculer_placement(self, cas=1, retrait=None):
        """
        Calcule le placement des PCB sur le panneau selon le cas spécifié.
        """
        # Copier le prototype pour éviter de le modifier directement
        pcb = self.pcb_prototype.copy()

        # Déterminer l'orientation selon le cas
        if cas == 2:
            pcb.rotate()  # Rotation du PCB si la plus grande dimension doit être en hauteur

        # Calcul du nombre de PCB pouvant être placés en largeur et en hauteur
        N_largeur = floor((self.panneau.largeur + self.espacement) / (pcb.largeur + self.espacement))
        N_hauteur = floor((self.panneau.hauteur + self.espacement) / (pcb.hauteur + self.espacement))

        # Retrait d'une colonne ou d'une rangée si spécifié
        if retrait == 'colonne' and N_largeur > 0:
            N_largeur -= 1  # Retirer une colonne
        elif retrait == 'rangée' and N_hauteur > 0:
            N_hauteur -= 1  # Retirer une rangée

        # Calcul de l'espace occupé en largeur et en hauteur
        largeur_occupee = N_largeur * pcb.largeur + max(0, N_largeur - 1) * self.espacement
        hauteur_occupee = N_hauteur * pcb.hauteur + max(0, N_hauteur - 1) * self.espacement

        # Calcul de l'espace restant sur le panneau
        R_largeur = self.panneau.largeur - largeur_occupee
        R_hauteur = self.panneau.hauteur - hauteur_occupee

        # Offsets pour la bordure
        offset_x = self.panneau.bordure
        offset_y = self.panneau.bordure

        # Placement des PCB sans rotation
        for i in range(N_largeur):
            for j in range(N_hauteur):
                x = offset_x + i * (pcb.largeur + self.espacement)  # Position en X du PCB
                y = offset_y + j * (pcb.hauteur + self.espacement)  # Position en Y du PCB
                rect = RectanglePCB(pcb.largeur, pcb.hauteur, x, y, rotation=pcb.rotation)
                self.rectangles.append(rect)  # Ajout du PCB à la liste des PCB placés

        # Placement des PCB rotés si les rotations sont autorisées
        if self.allow_rotation:
            self._placer_pcb_rotes(pcb, retrait, N_largeur, N_hauteur, R_largeur, R_hauteur, offset_x, offset_y)

    def _placer_pcb_rotes(self, pcb, retrait, N_largeur, N_hauteur, R_largeur, R_hauteur, offset_x, offset_y):
        """
        Place des PCB rotés de 90 degrés dans l'espace restant ou libéré.
        """
        # Créer un PCB roté pour le placement
        pcb_rot = pcb.copy()
        pcb_rot.rotate()

        # Si une colonne a été retirée, il y a plus d'espace en largeur
        if retrait == 'colonne':
            # Calcul du nombre de PCB rotés pouvant être placés en largeur et en hauteur
            N_largeur_rot = floor((self.panneau.largeur - (N_largeur * (pcb.largeur + self.espacement)) + self.espacement) / (pcb_rot.largeur + self.espacement))
            N_hauteur_rot = floor((self.panneau.hauteur + self.espacement) / (pcb_rot.hauteur + self.espacement))

            # Placement des PCB rotés dans l'espace libéré en largeur
            for i in range(N_largeur_rot):
                for j in range(N_hauteur_rot):
                    x = offset_x + N_largeur * (pcb.largeur + self.espacement) + i * (pcb_rot.largeur + self.espacement)
                    y = offset_y + j * (pcb_rot.hauteur + self.espacement)
                    # Vérification que le PCB roté ne dépasse pas du panneau
                    if x + pcb_rot.largeur <= self.panneau.largeur_totale - self.panneau.bordure and y + pcb_rot.hauteur <= self.panneau.hauteur_totale - self.panneau.bordure:
                        rect = RectanglePCB(pcb_rot.largeur, pcb_rot.hauteur, x, y, rotation=pcb_rot.rotation)
                        self.rectangles.append(rect)
        elif retrait == 'rangée':
            # Calcul du nombre de PCB rotés pouvant être placés en largeur et en hauteur
            N_largeur_rot = floor((self.panneau.largeur + self.espacement) / (pcb_rot.largeur + self.espacement))
            N_hauteur_rot = floor((self.panneau.hauteur - (N_hauteur * (pcb.hauteur + self.espacement)) + self.espacement) / (pcb_rot.hauteur + self.espacement))

            # Placement des PCB rotés dans l'espace libéré en hauteur
            for i in range(N_largeur_rot):
                for j in range(N_hauteur_rot):
                    x = offset_x + i * (pcb_rot.largeur + self.espacement)
                    y = offset_y + N_hauteur * (pcb.hauteur + self.espacement) + j * (pcb_rot.hauteur + self.espacement)
                    # Vérification que le PCB roté ne dépasse pas du panneau
                    if x + pcb_rot.largeur <= self.panneau.largeur_totale - self.panneau.bordure and y + pcb_rot.hauteur <= self.panneau.hauteur_totale - self.panneau.bordure:
                        rect = RectanglePCB(pcb_rot.largeur, pcb_rot.hauteur, x, y, rotation=pcb_rot.rotation)
                        self.rectangles.append(rect)
        else:
            # Placement standard des PCB rotés dans l'espace restant en largeur et en hauteur
            self._placer_pcb_rotes_standard(pcb, pcb_rot, N_largeur, N_hauteur, R_largeur, R_hauteur, offset_x, offset_y)

    def _placer_pcb_rotes_standard(self, pcb, pcb_rot, N_largeur, N_hauteur, R_largeur, R_hauteur, offset_x, offset_y):
        """
        Place des PCB rotés dans l'espace restant en largeur et en hauteur sans retrait.
        """
        # Placement des PCB rotés dans l'espace restant en largeur
        if R_largeur >= pcb_rot.largeur:
            N_largeur_rot = floor((R_largeur + self.espacement) / (pcb_rot.largeur + self.espacement))
            N_hauteur_rot = floor((self.panneau.hauteur + self.espacement) / (pcb_rot.hauteur + self.espacement))

            for i in range(N_largeur_rot):
                for j in range(N_hauteur_rot):
                    x = offset_x + N_largeur * (pcb.largeur + self.espacement) + i * (pcb_rot.largeur + self.espacement)
                    y = offset_y + j * (pcb_rot.hauteur + self.espacement)
                    if x + pcb_rot.largeur <= self.panneau.largeur_totale - self.panneau.bordure and y + pcb_rot.hauteur <= self.panneau.hauteur_totale - self.panneau.bordure:
                        rect = RectanglePCB(pcb_rot.largeur, pcb_rot.hauteur, x, y, rotation=pcb_rot.rotation)
                        self.rectangles.append(rect)

        # Placement des PCB rotés dans l'espace restant en hauteur
        if R_hauteur >= pcb_rot.hauteur:
            N_largeur_rot = floor((self.panneau.largeur + self.espacement) / (pcb_rot.largeur + self.espacement))
            N_hauteur_rot = floor((R_hauteur + self.espacement) / (pcb_rot.hauteur + self.espacement))

            for i in range(N_largeur_rot):
                for j in range(N_hauteur_rot):
                    x = offset_x + i * (pcb_rot.largeur + self.espacement)
                    y = offset_y + N_hauteur * (pcb.hauteur + self.espacement) + j * (pcb_rot.hauteur + self.espacement)
                    if x + pcb_rot.largeur <= self.panneau.largeur_totale - self.panneau.bordure and y + pcb_rot.hauteur <= self.panneau.hauteur_totale - self.panneau.bordure:
                        rect = RectanglePCB(pcb_rot.largeur, pcb_rot.hauteur, x, y, rotation=pcb_rot.rotation)
                        self.rectangles.append(rect)

class MplCanvas(FigureCanvasQTAgg):
    """
    Classe pour intégrer une figure Matplotlib dans PyQt5.
    """
    def __init__(self, parent=None, width=15, height=85, dpi=100):
        fig, self.axes = plt.subplots(2, 2, figsize=(width, height), dpi=dpi)
        super().__init__(fig)
        self.setParent(parent)
        plt.close(fig)  # Évite l'affichage de la figure dans une fenêtre séparée

class MainWindow(QMainWindow):
    """
    Classe principale de l'application PyQt5.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Panélisation PCB | William-Dew")
        self.setGeometry(100, 100, 1600, 900)

        # Variables pour les entrées utilisateur
        self.largeur_pcb = 0
        self.hauteur_pcb = 0
        self.espacement = 5      # Espacement par défaut 5 mm
        self.bordure = 15        # Bordure par défaut de 15 mm
        self.nombre_pcb_a_fabriquer = 1  # Valeur par défaut 1
        self.pourcentage_surlancement = 5  # Valeur par défaut 5%
        self.allow_rotation = True  # Mode mixte activé par défaut

        # Listes pour les dimensions des panneaux avec les valeurs pré-remplies
        self.panneaux_largeurs = [600, 580, 570, 457]
        self.panneaux_hauteurs = [500, 510, 480, 300]

        # Stockage des résultats pour le récapitulatif
        self.resultats = []

        # Initialiser l'interface utilisateur
        self.init_ui()

    def init_ui(self):
        """
        Initialise l'interface utilisateur.
        """
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal avec proportions 15% pour les entrées et 85% pour la visualisation
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # Layout pour les entrées utilisateur (15%)
        input_layout = QVBoxLayout()
        main_layout.addLayout(input_layout, 15)

        # Layout pour la visualisation et le récapitulatif (85%)
        right_layout = QVBoxLayout()
        main_layout.addLayout(right_layout, 85)

        # Cadre pour les dimensions du PCB
        pcb_group = QGroupBox("Dimensions du PCB")
        input_layout.addWidget(pcb_group)
        pcb_layout = QVBoxLayout()
        pcb_group.setLayout(pcb_layout)

        # Création du layout pour 'Dimension: [input] x [input] mm'
        pcb_dimensions_layout = QHBoxLayout()
        pcb_layout.addLayout(pcb_dimensions_layout)

        self.largeur_pcb_input = QLineEdit(str(self.largeur_pcb))
        self.hauteur_pcb_input = QLineEdit(str(self.hauteur_pcb))

        # Réduire la largeur des champs de saisie
        self.largeur_pcb_input.setMaximumWidth(60)
        self.hauteur_pcb_input.setMaximumWidth(60)

        # Ajouter le label 'Dimension:' et les inputs avec 'x' entre les deux
        pcb_dimensions_layout.addWidget(QLabel("Dimension :"))
        pcb_dimensions_layout.addWidget(self.largeur_pcb_input)
        pcb_dimensions_layout.addWidget(QLabel("x"))
        pcb_dimensions_layout.addWidget(self.hauteur_pcb_input)
        pcb_dimensions_layout.addWidget(QLabel("mm"))

        # Déplacer 'Entraxe' dans un autre groupe
        espacement_group = QGroupBox("Entraxe")
        input_layout.addWidget(espacement_group)
        espacement_layout = QHBoxLayout()
        espacement_group.setLayout(espacement_layout)

        self.espacement_input = QLineEdit(str(self.espacement))
        self.espacement_input.setMaximumWidth(60)

        espacement_layout.addWidget(QLabel("Entraxe (mm) :"))
        espacement_layout.addWidget(self.espacement_input)

        # Cadre pour les paramètres de production
        production_group = QGroupBox("Production")
        input_layout.addWidget(production_group)
        production_layout = QHBoxLayout()
        production_group.setLayout(production_layout)

        self.nombre_pcb_input = QLineEdit(str(self.nombre_pcb_a_fabriquer))
        self.pourcentage_surlancement_input = QLineEdit(str(self.pourcentage_surlancement))

        # Réduire la largeur des champs de saisie
        self.nombre_pcb_input.setMaximumWidth(60)
        self.pourcentage_surlancement_input.setMaximumWidth(60)

        # Création d'un layout horizontal pour les champs
        production_dimensions_layout = QHBoxLayout()
        production_layout.addLayout(production_dimensions_layout)

        production_dimensions_layout.addWidget(QLabel("Qté Pcb :"))
        production_dimensions_layout.addWidget(self.nombre_pcb_input)
        production_dimensions_layout.addWidget(QLabel("Casse (%) :"))
        production_dimensions_layout.addWidget(self.pourcentage_surlancement_input)

        # Checkbox pour le mode mixte
        self.mode_mix_checkbox = QCheckBox("Mode Mixte")
        self.mode_mix_checkbox.setChecked(True)
        input_layout.addWidget(self.mode_mix_checkbox)

        # Cadre pour la bordure du panneau
        bordure_group = QGroupBox("Bordure du Panneau")
        input_layout.addWidget(bordure_group)
        bordure_layout = QHBoxLayout()
        bordure_group.setLayout(bordure_layout)

        self.bordure_input = QLineEdit(str(self.bordure))
        self.bordure_input.setMaximumWidth(60)

        bordure_layout.addWidget(QLabel("Bordure (mm) :"))
        bordure_layout.addWidget(self.bordure_input)

        # Cadres pour les dimensions des panneaux
        self.panneaux_largeurs_inputs = []
        self.panneaux_hauteurs_inputs = []

        for i in range(4):
            panneau_group = QGroupBox(f"Dimensions du Panneau {i+1}")
            input_layout.addWidget(panneau_group)
            panneau_layout = QVBoxLayout()
            panneau_group.setLayout(panneau_layout)

            # Création du layout pour 'Dimension: [input] x [input] mm'
            panneau_dimensions_layout = QHBoxLayout()
            panneau_layout.addLayout(panneau_dimensions_layout)

            largeur_input = QLineEdit(str(self.panneaux_largeurs[i]))
            hauteur_input = QLineEdit(str(self.panneaux_hauteurs[i]))

            # Réduire la largeur des champs de saisie
            largeur_input.setMaximumWidth(60)
            hauteur_input.setMaximumWidth(60)

            self.panneaux_largeurs_inputs.append(largeur_input)
            self.panneaux_hauteurs_inputs.append(hauteur_input)

            panneau_dimensions_layout.addWidget(QLabel("Dimension :"))
            panneau_dimensions_layout.addWidget(largeur_input)
            panneau_dimensions_layout.addWidget(QLabel("x"))
            panneau_dimensions_layout.addWidget(hauteur_input)
            panneau_dimensions_layout.addWidget(QLabel("mm"))

        # Bouton pour lancer le calcul
        calculer_button = QPushButton("Calculer")
        calculer_button.clicked.connect(self.calculer_et_visualiser)
        input_layout.addWidget(calculer_button)

        # Bouton pour réinitialiser la configuration
        reset_button = QPushButton("Nouvelle Configuration")
        reset_button.clicked.connect(self.nouvelle_configuration)
        input_layout.addWidget(reset_button)

        # Widget pour le canvas Matplotlib
        self.canvas = MplCanvas(width=15, height=85, dpi=100)  # Dimensions ajustées
        right_layout.addWidget(self.canvas)

        # Tableau pour afficher le récapitulatif
        self.table_widget = QTableWidget()
        right_layout.addWidget(self.table_widget)

        # Ajustements esthétiques
        font = QFont()
        font.setPointSize(10)
        self.setFont(font)

    def calculer_et_visualiser(self):
        """
        Récupère les entrées utilisateur, effectue les calculs et met à jour l'interface.
        """
        try:
            # Récupérer les valeurs saisies
            self.largeur_pcb = float(self.largeur_pcb_input.text())
            self.hauteur_pcb = float(self.hauteur_pcb_input.text())
            self.espacement = float(self.espacement_input.text())
            self.bordure = float(self.bordure_input.text())

            self.nombre_pcb_a_fabriquer = int(self.nombre_pcb_input.text())
            self.pourcentage_surlancement = float(self.pourcentage_surlancement_input.text())

            self.allow_rotation = self.mode_mix_checkbox.isChecked()

            self.panneaux_largeurs = [float(input.text()) for input in self.panneaux_largeurs_inputs]
            self.panneaux_hauteurs = [float(input.text()) for input in self.panneaux_hauteurs_inputs]

            # Vérifier que les valeurs sont positives
            if any(v <= 0 for v in [self.largeur_pcb, self.hauteur_pcb, self.espacement, self.bordure, self.nombre_pcb_a_fabriquer] + self.panneaux_largeurs + self.panneaux_hauteurs):
                QMessageBox.critical(self, "Erreur", "Toutes les valeurs doivent être positives.")
                return

            # Créer le prototype de PCB
            pcb_prototype = RectanglePCB(self.largeur_pcb, self.hauteur_pcb)

            # Calculer le nombre total de PCB à produire en incluant le surlancement
            nombre_total_pcb = ceil(self.nombre_pcb_a_fabriquer * (1 + self.pourcentage_surlancement / 100))

            # Listes pour stocker les panneaux et les placements
            panneaux = []
            placements = []
            self.resultats.clear()

            # Créer les panneaux et calculer les placements
            for i in range(4):
                panneau = Panneau(self.panneaux_largeurs[i], self.panneaux_hauteurs[i], self.bordure)
                panneaux.append(panneau)

                placement = PlacementPCB(panneau, pcb_prototype, self.espacement, allow_rotation=self.allow_rotation)
                placement.calculer_meilleur_placement()
                placements.append(placement)

                # Calculer le pourcentage de remplissage
                pourcentage_remplissage = (placement.surface_occupee / panneau.surface_utilisable) * 100 if panneau.surface_utilisable > 0 else 0

                # Calculer le nombre de panneaux nécessaires pour produire le nombre total de PCB
                if placement.nombre_pcb > 0:
                    nombre_panneaux_necessaires = ceil(nombre_total_pcb / placement.nombre_pcb)
                else:
                    nombre_panneaux_necessaires = 0  # Impossible de placer des PCB sur ce panneau

                # Calculer la quantité produite
                quantite_produite = placement.nombre_pcb * nombre_panneaux_necessaires

                self.resultats.append({
                    'panneau': i + 1,
                    'dimensions_totales': f"{panneau.largeur_totale} x {panneau.hauteur_totale}",
                    'dimensions_utilisables': f"{panneau.largeur} x {panneau.hauteur}",
                    'nombre_pcb': placement.nombre_pcb,
                    'pourcentage_remplissage': pourcentage_remplissage,
                    'nombre_panneaux_necessaires': nombre_panneaux_necessaires,
                    'quantite_produite': quantite_produite  # Nouvelle clé ajoutée
                })

            # Visualiser les placements
            self.visualiser_placements(panneaux, placements)
            # Afficher le récapitulatif
            self.afficher_recapitulatif()

        except ValueError:
            QMessageBox.critical(self, "Erreur", "Veuillez saisir des valeurs numériques valides.")
            return

    def visualiser_placements(self, panneaux, placements):
        """
        Met à jour le graphique pour visualiser les placements des PCB sur les panneaux.
        """
        # Effacer les axes
        for ax_row in self.canvas.axes:
            for ax in ax_row:
                ax.clear()

        # Liste des placements
        for idx, (panneau, placement) in enumerate(zip(panneaux, placements)):
            ax = self.canvas.axes[idx // 2][idx % 2]
            rectangles = placement.rectangles

            # Dessiner le panneau complet
            panneau_patch = patches.Rectangle((0, 0), panneau.largeur_totale, panneau.hauteur_totale,
                                              linewidth=1, edgecolor='black', facecolor='lightgray', alpha=0.3)
            ax.add_patch(panneau_patch)

            # Dessiner la surface utilisable (sans la bordure)
            surface_utilisable_patch = patches.Rectangle((panneau.bordure, panneau.bordure), panneau.largeur, panneau.hauteur,
                                                         linewidth=1, edgecolor='black', facecolor='none')
            ax.add_patch(surface_utilisable_patch)

            # Dessiner les PCB placés
            for rect in rectangles:
                # Choisir la couleur en fonction de l'orientation du PCB
                couleur = 'blue' if rect.rotation == 0 else 'green'
                rectangle_patch = patches.Rectangle((rect.x, rect.y), rect.largeur, rect.hauteur,
                                                    linewidth=1, edgecolor='black', facecolor=couleur, alpha=0.6)
                ax.add_patch(rectangle_patch)

            # Configurations supplémentaires du graphique
            ax.set_xlim(0, panneau.largeur_totale)
            ax.set_ylim(0, panneau.hauteur_totale)
            ax.set_aspect('equal', adjustable='box')
            ax.set_title(f"Format {idx +1} : {panneau.largeur_totale} x {panneau.hauteur_totale} : x{placement.nombre_pcb} PCB")
            ax.axis('off')

        # Rafraîchir le canvas
        self.canvas.draw()

    from PyQt5.QtWidgets import QProgressBar

    def afficher_recapitulatif(self):
        """
        Affiche les résultats dans un tableau avec des barres de progression.
        """
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
            
            # Ajouter une barre de progression pour le remplissage
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

        

        # Ajuster la taille des lignes
        row_height = 25  # Hauteur par défaut pour chaque ligne, ajustez si nécessaire
        self.table_widget.verticalHeader().setDefaultSectionSize(row_height)
        self.table_widget.resizeRowsToContents()

        
        total_height = 200

        # Définir la hauteur fixe du tableau
        self.table_widget.setFixedHeight(total_height)


    def nouvelle_configuration(self):
        """
        Réinitialise les champs pour une nouvelle configuration.
        """
        self.largeur_pcb_input.clear()
        self.hauteur_pcb_input.clear()
        self.espacement_input.setText(str(5))
        self.bordure_input.setText(str(15))
        self.nombre_pcb_input.setText(str(1))  # Valeur par défaut 1
        self.pourcentage_surlancement_input.setText(str(5))  # Valeur par défaut 5%
        self.mode_mix_checkbox.setChecked(True)

        valeurs_largeurs = [600, 580, 570, 457]
        valeurs_hauteurs = [500, 510, 480, 300]

        for i in range(4):
            self.panneaux_largeurs_inputs[i].setText(str(valeurs_largeurs[i]))
            self.panneaux_hauteurs_inputs[i].setText(str(valeurs_hauteurs[i]))

        # Effacer le canvas
        for ax_row in self.canvas.axes:
            for ax in ax_row:
                ax.clear()
        self.canvas.draw()

        # Effacer le tableau
        self.table_widget.clearContents()
        self.table_widget.setRowCount(0)

# Exécution de l'application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    LicenseValidator.verifier_licence()    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
