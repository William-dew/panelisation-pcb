from math import floor, ceil
from typing import Optional, List

class RectanglePCB:
    """
    Classe représentant un PCB avec ses dimensions, sa position et son orientation.
    """
    def __init__(self, largeur: float, hauteur: float, x: float = 0, y: float = 0, rotation: int = 0):
        self.largeur = largeur
        self.hauteur = hauteur
        self.x = x
        self.y = y
        self.rotation = rotation

    def rotate(self):
        """
        Fait pivoter le PCB de 90 degrés.
        """
        self.largeur, self.hauteur = self.hauteur, self.largeur
        self.rotation = (self.rotation + 90) % 180

    def copy(self) -> 'RectanglePCB':
        """
        Crée une copie du PCB.
        """
        return RectanglePCB(self.largeur, self.hauteur, self.x, self.y, self.rotation)


class Panneau:
    """
    Classe représentant un panneau.
    """
    def __init__(self, largeur_totale: float, hauteur_totale: float, bordure: float = 15):
        self.largeur_totale = largeur_totale
        self.hauteur_totale = hauteur_totale
        self.bordure = bordure

        self.largeur = self.largeur_totale - 2 * self.bordure
        self.hauteur = self.hauteur_totale - 2 * self.bordure
        self.surface_utilisable = self.largeur * self.hauteur


class PlacementPCB:
    """
    Classe gérant le placement des PCB sur un panneau.
    """
    def __init__(self, panneau: Panneau, pcb_prototype: RectanglePCB, espacement: float = 0, allow_rotation: bool = True):
        self.panneau = panneau
        self.pcb_prototype = pcb_prototype
        self.espacement = espacement
        self.allow_rotation = allow_rotation
        self.rectangles: List[RectanglePCB] = []
        self.surface_occupee: float = 0
        self.nombre_pcb: int = 0

    def calculer_meilleur_placement(self):
        """
        Calcule le meilleur placement possible.
        """
        meilleures_rectangles = []
        max_pcb = 0
        max_surface_occupee = 0

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

        for config in configurations:
            self.rectangles.clear()
            self.calculer_placement(cas=config['cas'], retrait=config['retrait'])

            nombre_pcb = len(self.rectangles)
            surface_occupee = sum(rect.largeur * rect.hauteur for rect in self.rectangles)

            if nombre_pcb > max_pcb or (nombre_pcb == max_pcb and surface_occupee > max_surface_occupee):
                max_pcb = nombre_pcb
                max_surface_occupee = surface_occupee
                meilleures_rectangles = self.rectangles.copy()

        self.rectangles = meilleures_rectangles
        self.nombre_pcb = max_pcb
        self.surface_occupee = max_surface_occupee

    def calculer_placement(self, cas: int = 1, retrait: Optional[str] = None):
        """
        Calcule le placement pour une configuration donnée.
        """
        pcb = self.pcb_prototype.copy()

        if cas == 2:
            pcb.rotate()

        N_largeur = floor((self.panneau.largeur + self.espacement) / (pcb.largeur + self.espacement))
        N_hauteur = floor((self.panneau.hauteur + self.espacement) / (pcb.hauteur + self.espacement))

        if retrait == 'colonne' and N_largeur > 0:
            N_largeur -= 1
        elif retrait == 'rangée' and N_hauteur > 0:
            N_hauteur -= 1

        largeur_occupee = N_largeur * pcb.largeur + max(0, N_largeur - 1) * self.espacement
        hauteur_occupee = N_hauteur * pcb.hauteur + max(0, N_hauteur - 1) * self.espacement

        R_largeur = self.panneau.largeur - largeur_occupee
        R_hauteur = self.panneau.hauteur - hauteur_occupee

        offset_x = self.panneau.bordure
        offset_y = self.panneau.bordure

        # Placement des PCB sans rotation
        for i in range(N_largeur):
            for j in range(N_hauteur):
                x = offset_x + i * (pcb.largeur + self.espacement)
                y = offset_y + j * (pcb.hauteur + self.espacement)
                rect = RectanglePCB(pcb.largeur, pcb.hauteur, x, y, rotation=pcb.rotation)
                self.rectangles.append(rect)

        # Placement rotés si autorisé
        if self.allow_rotation:
            self._placer_pcb_rotes(pcb, retrait, N_largeur, N_hauteur, R_largeur, R_hauteur, offset_x, offset_y)

    def _placer_pcb_rotes(self, pcb, retrait, N_largeur, N_hauteur, R_largeur, R_hauteur, offset_x, offset_y):
        pcb_rot = pcb.copy()
        pcb_rot.rotate()

        if retrait == 'colonne':
            N_largeur_rot = floor((self.panneau.largeur - (N_largeur * (pcb.largeur + self.espacement)) + self.espacement) / (pcb_rot.largeur + self.espacement))
            N_hauteur_rot = floor((self.panneau.hauteur + self.espacement) / (pcb_rot.hauteur + self.espacement))

            for i in range(N_largeur_rot):
                for j in range(N_hauteur_rot):
                    x = offset_x + N_largeur * (pcb.largeur + self.espacement) + i * (pcb_rot.largeur + self.espacement)
                    y = offset_y + j * (pcb_rot.hauteur + self.espacement)
                    if x + pcb_rot.largeur <= self.panneau.largeur_totale - self.panneau.bordure and y + pcb_rot.hauteur <= self.panneau.hauteur_totale - self.panneau.bordure:
                        self.rectangles.append(RectanglePCB(pcb_rot.largeur, pcb_rot.hauteur, x, y, rotation=pcb_rot.rotation))

        elif retrait == 'rangée':
            N_largeur_rot = floor((self.panneau.largeur + self.espacement) / (pcb_rot.largeur + self.espacement))
            N_hauteur_rot = floor((self.panneau.hauteur - (N_hauteur * (pcb.hauteur + self.espacement)) + self.espacement) / (pcb_rot.hauteur + self.espacement))

            for i in range(N_largeur_rot):
                for j in range(N_hauteur_rot):
                    x = offset_x + i * (pcb_rot.largeur + self.espacement)
                    y = offset_y + N_hauteur * (pcb.hauteur + self.espacement) + j * (pcb_rot.hauteur + self.espacement)
                    if x + pcb_rot.largeur <= self.panneau.largeur_totale - self.panneau.bordure and y + pcb_rot.hauteur <= self.panneau.hauteur_totale - self.panneau.bordure:
                        self.rectangles.append(RectanglePCB(pcb_rot.largeur, pcb_rot.hauteur, x, y, rotation=pcb_rot.rotation))
        else:
            self._placer_pcb_rotes_standard(pcb, pcb_rot, N_largeur, N_hauteur, R_largeur, R_hauteur, offset_x, offset_y)

    def _placer_pcb_rotes_standard(self, pcb, pcb_rot, N_largeur, N_hauteur, R_largeur, R_hauteur, offset_x, offset_y):
        if R_largeur >= pcb_rot.largeur:
            N_largeur_rot = floor((R_largeur + self.espacement) / (pcb_rot.largeur + self.espacement))
            N_hauteur_rot = floor((self.panneau.hauteur + self.espacement) / (pcb_rot.hauteur + self.espacement))

            for i in range(N_largeur_rot):
                for j in range(N_hauteur_rot):
                    x = offset_x + N_largeur * (pcb.largeur + self.espacement) + i * (pcb_rot.largeur + self.espacement)
                    y = offset_y + j * (pcb_rot.hauteur + self.espacement)
                    if x + pcb_rot.largeur <= self.panneau.largeur_totale - self.panneau.bordure and y + pcb_rot.hauteur <= self.panneau.hauteur_totale - self.panneau.bordure:
                        self.rectangles.append(RectanglePCB(pcb_rot.largeur, pcb_rot.hauteur, x, y, rotation=pcb_rot.rotation))

        if R_hauteur >= pcb_rot.hauteur:
            N_largeur_rot = floor((self.panneau.largeur + self.espacement) / (pcb_rot.largeur + self.espacement))
            N_hauteur_rot = floor((R_hauteur + self.espacement) / (pcb_rot.hauteur + self.espacement))

            for i in range(N_largeur_rot):
                for j in range(N_hauteur_rot):
                    x = offset_x + i * (pcb_rot.largeur + self.espacement)
                    y = offset_y + N_hauteur * (pcb.hauteur + self.espacement) + j * (pcb_rot.hauteur + self.espacement)
                    if x + pcb_rot.largeur <= self.panneau.largeur_totale - self.panneau.bordure and y + pcb_rot.hauteur <= self.panneau.hauteur_totale - self.panneau.bordure:
                        self.rectangles.append(RectanglePCB(pcb_rot.largeur, pcb_rot.hauteur, x, y, rotation=pcb_rot.rotation))


def calcul_pourcentage_remplissage(surface_occupee: float, surface_utilisable: float) -> float:
    """
    Calcule le pourcentage de remplissage.
    """
    if surface_utilisable > 0:
        return (surface_occupee / surface_utilisable) * 100
    return 0.0


def calcul_panneaux_necessaires(nombre_total_pcb: int, pcb_par_panneau: int) -> int:
    """
    Calcule le nombre de panneaux nécessaires.
    """
    if pcb_par_panneau > 0:
        return ceil(nombre_total_pcb / pcb_par_panneau)
    return 0
