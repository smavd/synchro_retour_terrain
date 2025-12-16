"""
Module principal

Todo :
    Forcer le type des données d'entrée vecteur.

"""
#-----------------------------------------------------------
# Copyright (C) 2015 Martin Dobias
#-----------------------------------------------------------
# Licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#---------------------------------------------------------------------
from typing import Any
from pathlib import Path
from PyQt5.QtWidgets import QAction, QMessageBox, QComboBox
from PyQt5.QtCore import Qt
from qgis.utils import iface
from qgis.core import Qgis, QgsMapLayerType, QgsProject, QgsMapLayer
from PyQt5.QtGui import QIcon
from synchro_retour_terrain.window_retour_terrain import WindowRetourTerrain # Vs Code ne trouve pas le module situé dans le même dossier mais Qgis le trouvera bien. 



def classFactory(iface):

    # Choisir quelle version du plugin utiliser
    from .plugin_main import SyncRetourTerrainPlugin

    return SyncRetourTerrainPlugin(iface)

