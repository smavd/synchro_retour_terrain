"""
Module Principal du plugin synchro retour terrain
Todo : 
    Couches géopackage pour la target layer. 
    Si couches invalides ou mauvaise structure : Qmessage box et retour à la fenetre de base. 
    choix du IDU : faire une combobox
"""

from pathlib import Path
from collections import Counter
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QWidget, QDialog, QMessageBox, QComboBox, QVBoxLayout, QTableWidget, QTableWidgetItem, QHBoxLayout, QPushButton, QGroupBox
from qgis.PyQt.QtCore import QVariant
from qgis.gui import QgsDataSourceSelectDialog
from qgis.core import QgsMapLayerType, QgsMapLayer, QgsVectorLayer, QgsProject, QgsFeature,QgsWkbTypes
from qgis.utils import iface


class WindowRetourTerrain(QDialog):
    def __init__(self, parent: QWidget=None) -> None:
        # On initialise le parent
        super().__init__(parent)
        # On charge loe fichier d'UI
        uic.loadUi(Path(__file__).parent / "window_retour_terrain.ui", self)

    def populate_targetcombobox(self):
        #Récupérer les couches du projet
        self.map_layers = QgsProject.instance().mapLayers().values()
        # Créer une liste des couches autorisées (vectorielles)
        self.allow_list = [
            lyr for lyr in self.map_layers 
            if lyr.type() == QgsMapLayer.VectorLayer  # Vérifie si la couche est vectorielle
            ]
        print(self.allow_list)
        # Créer une liste des couches interdites
        self.except_list = [lyr for lyr in self.map_layers if lyr not in self.allow_list]
        print(self.except_list)
        # Définir les couches à exclure dans la ComboBox
        self.MapLayerComboBox_target.setExceptedLayerList(self.except_list)
        return self.MapLayerComboBox_target

    def check_source_format(self):
        ''' Méthode qui vérifie si la couche source donnée par l'utilisateur est bien au format shapefile ou gpkg.
            Si la couche entrée a un format différent, un message d'erreur apparait. 
        '''
        source_layer_path =  str(self.mQgsFileWidget_source.filePath())
        print(source_layer_path)
        if source_layer_path == '':
            print("pas de couche sélectionnée.")
            return False 
        #Vérifier que le fichier est bien un geopackage
        elif source_layer_path.endswith(('.shp', '.gpkg')):
            print("source layer est dans un format valide.")
            return True
        else :
            message_format =f"Format de fichier non pris en charge. les formats pris en charge sont : \n shapefile (.shp) \n geopackage (.gpkg)"
            # Afficher le message d'erreur dans un QMessageBox
            QMessageBox.critical(None, "Erreur de format de fichier", message_format)
            #Réinitialiser la valeur de mQgsFileWidget_source
            self.mQgsFileWidget_source.setFilePath(None)
            return False   



    def get_target_fields(self, target_layer: 'QgsVectorLayer', combo_box: 'QComboBox', default_field: str = "IDU"):
        """
        Récupère les attributs de type texte, int ou double d'une couche vectorielle et les ajoute à un QComboBox,
        en plaçant le champ spécifié par 'default_field' en premier s'il existe.

        :param target_layer: Une instance de QgsVectorLayer.
        :param combo_box: Une instance de QComboBox où les attributs seront ajoutés.
        :param default_field: Le nom du champ à placer en premier, par défaut 'IDU'.
        """
        if target_layer is None:
            print("Pas de couche sélectionnée")
            return

        # Vérifie si la couche est valide
        if not target_layer.isValid():
            print("La couche n'est pas valide")
            return

        # Effacer les éléments existants dans le combo_box
        combo_box.clear()

        if isinstance(target_layer, QgsVectorLayer):
            # Obtenir la liste des champs de la couche
            fields = target_layer.fields()

            # Initialiser une liste pour les champs à ajouter
            fields_to_add = []

            # Vérifier si le champ par défaut existe
            default_field_found = False
            for field in fields:
                if field.name() == default_field:
                    default_field_found = True
                elif field.type() in (QVariant.String, QVariant.Int, QVariant.Double):
                    # Ajouter les champs de type String, Int ou Double
                    fields_to_add.append(field.name())

            # Si le champ par défaut a été trouvé, l'ajouter en premier
            if default_field_found:
                combo_box.addItem(default_field)

            # Ajouter les autres champs
            combo_box.addItems(fields_to_add)
        else:
            print("La couche choisie n'est pas un vecteur")


    def display_report(self, report):
        """
        Affiche un rapport de synchronisation dans une boîte de dialogue (QMessageBox).

        Cette méthode prend en entrée un dictionnaire de rapport généré par la méthode `edit_target` et affiche un résumé
        des entités ajoutées, des entités mises à jour, ainsi que les détails des champs modifiés dans une boîte de dialogue.
        La boîte contient deux boutons : "Terminer" et "Synchroniser une autre couche".
        
        Args:
            report (dict): Le dictionnaire de rapport retourné par `edit_target`, contenant :
                - 'added_entities': Le nombre d'entités ajoutées à la couche cible.
                - 'updated_entities': Le nombre d'entités mises à jour dans la couche cible.
                - 'updated_fields': Un dictionnaire avec les champs modifiés et leurs anciennes/nouvelles valeurs pour chaque IDU.
                - supressed_entities : Le nombre d'entités supprimées de la couche cible.
        Returns:
            None: Cette méthode affiche uniquement la boîte de dialogue et ne retourne rien.
        """
        # Créer le message du rapport
        report_message = f"Synchronisation terminée.\n\n"
        report_message += f"Nombre d'entités ajoutées : {report['added_entities']}\n"
        report_message += f"Nombre d'entités supprimées : {report['supressed_entities']}\n"
        report_message += f"Nombre d'entités mises à jour : {report['updated_entities']}\n"
        

        # Ajouter les détails sur les champs mis à jour, si disponibles
        if report['updated_fields']:
            report_message += "\nDétails des champs mis à jour :\n"
            for idu, fields in report['updated_fields'].items():
                report_message += f"\n- IDU {idu} :\n"
                for field_name, values in fields.items():
                    old_value = values['old_value']
                    new_value = values['new_value']
                    report_message += f"    {field_name} : '{old_value}' -> '{new_value}'\n"
        else:
            report_message += "\nAucun champ mis à jour.\n"

        # Créer une boîte de dialogue QMessageBox
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Rapport de Synchronisation")
        msg_box.setText(report_message)
        msg_box.setIcon(QMessageBox.Information)

        # Ajouter des boutons "Terminer" et "Synchroniser une autre couche"
        msg_box.addButton("Terminer", QMessageBox.AcceptRole)
        msg_box.addButton("Synchroniser une autre couche", QMessageBox.ActionRole)

        # Afficher la boîte de dialogue et capturer la réponse de l'utilisateur
        response = msg_box.exec_()

        # Vérifier quelle action a été choisie
        if response == QMessageBox.AcceptRole:
            print("L'utilisateur a choisi de terminer.")
            # Vous pouvez mettre ici le code pour terminer ou quitter le processus
        else:
            print("L'utilisateur a choisi de synchroniser une autre couche.")
            self.show()

    
    def update_data(self):
        print("debut de update_data")

        #Création de l'objet target_layer
        target_layer = self.MapLayerComboBox_target.currentLayer()
        print('Target_layer chargé :', target_layer)
        
        # Chargement de la couche source
        print("chargement de source_layer...")
        source_layer_path =  self.mQgsFileWidget_source.filePath() # Chemin de la couche source 
        print('Chemin vers la donnee source : ', source_layer_path)
        source_layer = None  # Initialiser la variable source_vector_layer

        if self.check_source_format() is True: # On vérifie que l'utilisateur a bien renseigné une couche source au bon format
            if source_layer_path.endswith('.shp'): # cas ou le fichier layer_source est un shp
                source_layer = QgsVectorLayer(source_layer_path, "source_layer", "ogr")
                print('Source_layer chargé : ', source_layer)
            elif source_layer_path.endswith('.gpkg'): # cas ou le fichier layer_source est un gpkg
                source_layer = iface.addVectorLayer(source_layer_path, "temp_source_layer", "ogr")

        else:
            message =f"Veuillez sélectionner une couche source avec un format valide (geopackage ou shapefile)"
            # Afficher le message d'erreur dans un QMessageBox
            QMessageBox.critical(None, "Pas de couche source", message)
        
        # Vérification de l'existance et l'unicité d'un identifiant unique (IDU par défaut)
        idu = self.idu_comboBox.currentText()
        print(idu)

        # Création de l'objet TerrainSynchronizer
        synchronizer = TerrainSynchronizer(source_layer=source_layer, target_layer=target_layer, idu=idu)

        # Vérifier que l'IDU est unique
        idu_test = synchronizer.check_idu_exists_unique(target_layer, source_layer, idu)
        print(idu_test)
            
        # Rechercher les entités de la couche cible qui n'ont pas de correspondance dans la couche source
        idus_orphelins = synchronizer.check_attributs(target_layer, source_layer, idu)
        print("IDU orphelins : ", idus_orphelins)
        features_uniquement_target = [
            f for f in target_layer.getFeatures()
            if f[idu] in idus_orphelins
            ]
        idus_a_supprimer = None
        if features_uniquement_target:
            fen = FenetreEntitesOrphelines(features_uniquement_target, idu, self)
            if fen.exec_() == QDialog.Accepted:
                idus_a_supprimer = fen.get_selected_idus()
            else:
                idus_a_supprimer = None
         
        if idu_test: # Si le idu_test est True
            # Début de la mise à jour de la target_layer
            print('Vérification des structures des couches : ')
            if (target_layer, source_layer): # Tester si les deux couches ont la même structure
                test_layer_structure = synchronizer.compare_layer_structure(target_layer, source_layer)
                if test_layer_structure is True:
                    #Récupération du champ date_maj
                    date_maj = self.date_combobox.currentText()
                    print(f"Date de MAJ : {date_maj}")
                    # Edition des entités de target layer
                    print("début de l'édition des entités de couche cible")
                    report = synchronizer.edit_target(
                        target_layer=target_layer,
                        source_layer=source_layer,
                        idus_a_supprimer=idus_a_supprimer,
                        idu=idu,
                        date_groupBox=self.date_groupBox,
                        date_maj=date_maj
                    )
                    print(report)
                    self.display_report(report)
                else: 
                    message = f"""La couche de terrain (couche source) et la couche à mettre à jour (couche cible) ont des structure différentes. 
                                \n Mise à jour impossible.
                                \n Vérifiez les couches selectionnées."""
                    QMessageBox.critical(None, "Pas de couche source", message)
                    self.show()


        # Suppression de la couche temporaire source_layer
        if source_layer:
            QgsProject.instance().removeMapLayer(source_layer)

        
class TerrainSynchronizer:
    """
    Classe contenant la logique métier : vérifications, comparaison de structure,
    édition/synchronisation de la couche cible à partir de la couche source.
    """
    def __init__(self, source_layer, target_layer, idu: str):
        self.source_layer = source_layer
        self.target_layer = target_layer
        self.idu = idu

    @staticmethod
    def afficher_message_erreur(message):
        """Affiche une QMessageBox avec un message d'erreur."""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Erreur")
        msg.setText(message)
        msg.exec_()

    @staticmethod
    def verifier_existence_attribut(layer, idu):
        """Vérifie si l'attribut existe dans la couche."""
        if layer is None:
            return False
        return idu in [field.name() for field in layer.fields()]
        
    @staticmethod
    def verifier_unicite_attribut(layer, idu):
        """Vérifie si les valeurs de l'attribut sont uniques dans la couche.
        Retourne (bool, set) : bool indique unicité, set contient les valeurs dupliquées.
        """
        if layer is None:
            return False, set()
        valeurs = [feature[idu] for feature in layer.getFeatures()]
        valeurs_dupliquees = set()
        vus = set()
        for v in valeurs:
            if v in vus:
                valeurs_dupliquees.add(v)
            else:
                vus.add(v)
        return len(valeurs_dupliquees) == 0, valeurs_dupliquees

    def check_idu_exists_unique(self, target_layer, source_layer, idu):
        """
        Vérifie l'existence et l'unicité d'un attribut dans deux couches.
        """
        # Vérification de l'existence de l'attribut dans chaque couche
        attribut_existe_source = self.verifier_existence_attribut(source_layer, idu)
        attribut_existe_target = self.verifier_existence_attribut(target_layer, idu)

        if not attribut_existe_source:
            self.afficher_message_erreur(f"L'attribut '{idu}' n'existe pas dans la couche source.")
            return None
        
        if not attribut_existe_target:
            self.afficher_message_erreur(f"L'attribut '{idu}' n'existe pas dans la couche cible.")
            return None

        # Vérification de l'unicité
        attribut_unique_source, valeurs_dupliquees_source = self.verifier_unicite_attribut(source_layer, idu)
        attribut_unique_target, valeurs_dupliquees_target = self.verifier_unicite_attribut(target_layer, idu)

        if not attribut_unique_source:
            self.afficher_message_erreur(f"Les valeurs de l'identifiant '{idu}' ne sont pas uniques dans la couche source.\nValeurs dupliquées : {valeurs_dupliquees_source}")
            return None

        if not attribut_unique_target:
            self.afficher_message_erreur(f"Les valeurs de l'identifiant '{idu}' ne sont pas uniques dans la couche cible.\nValeurs dupliquées : {valeurs_dupliquees_target}")
            return None

        return {
            'attribut_existe_source': True,
            'attribut_existe_target': True,
            'attribut_unique_source': True,
            'attribut_unique_target': True
        }

    def compare_layer_structure(self, target_layer, source_layer):
        ''' Compare la structure des tables attributaires de deux objets QgsVectorLayer
            Renvoie True si les structures sont identiques, sinon False.
        '''
        
        # Vérifier si les deux couches sont valides
        if not target_layer.isValid() or not source_layer.isValid():
            print("Une ou les deux couches ne sont pas valides.")
            return False

        # Vérifier le nombre de champs
        if target_layer.fields().count() != source_layer.fields().count():
            print("Le nombre de champs est différent.")
            return False

        # Comparer les noms et types des champs
        for target_field, source_field in zip(target_layer.fields(), source_layer.fields()):
            if target_field.name() != source_field.name():
                print(f"Les noms des champs sont différents : {target_field.name()} vs {source_field.name()}")
                return False
            if target_field.typeName() != source_field.typeName():
                print(f"Les types des champs sont différents : {target_field.typeName()} vs {source_field.typeName()}")
                return False

        print("Les structures des couches sont identiques.")
        return True

    def edit_target(self,target_layer,source_layer,idus_a_supprimer=None,idu='IDU',date_groupBox=None,date_maj="date_maj"):
        """
        Synchronise les entités de la couche source avec celles de la couche cible, en fonction d'un identifiant unique (IDU).

        Cette méthode compare les entités de deux couches (source et cible) sur la base d'un champ d'identifiant unique (IDU).
        Si une entité de la source existe déjà dans la cible (même IDU), ses attributs et sa géométrie sont mis à jour si nécessaire.
        Si l'entité n'existe pas dans la couche cible, elle est ajoutée. La méthode retourne un dictionnaire contenant :
        - le nombre d'entités ajoutées,
        - le nombre d'entités mises à jour,
        - les champs mis à jour pour chaque entité et leurs valeurs respectives.

        Args:
            target_layer (QgsVectorLayer): La couche cible où les entités seront ajoutées ou mises à jour.
            source_layer (QgsVectorLayer): La couche source qui contient les entités à synchroniser avec la cible.
            idu (str, optional): Le champ de la clé unique utilisé pour identifier les entités à synchroniser (par défaut 'IDU').
            date_groupBox (QGroupBox, optional): Un objet QGroupBox qui indique si la vérification de la date doit être appliquée.
            date_maj(str, optional): Nom de l'attribut date_maj, récupéré dans la date_combobox.

        Returns:
            dict: Un dictionnaire contenant :
                - 'added_entities': Le nombre d'entités ajoutées à la couche cible.
                - 'updated_entities': Le nombre d'entités mises à jour dans la couche cible.
                - 'updated_fields': Un dictionnaire contenant pour chaque IDU les champs modifiés et leurs anciennes/nouvelles valeurs.
        """

        # récupérer l'expression de filtre de la couche cible
        target_filter = target_layer.subsetString()
        print(target_filter)
        # Suppression du filtre sur la couche cible (il est remis à la fin de l'édition)
        target_layer.setSubsetString(None)
        
        # Initialisation des compteurs et du dictionnaire de suivi des mises à jour
        report = {
            'added_entities': 0,
            'supred_entities': 0,
            'updated_entities': 0,
            'updated_fields': {}
        }

        report['supressed_entities'] = 0
        if idus_a_supprimer:
            target_layer.startEditing()
            for f in target_layer.getFeatures():
                if f[idu] in idus_a_supprimer:
                    target_layer.deleteFeature(f.id())
                    report['supressed_entities'] += 1
                    print(f"Entité avec IDU {f[idu]} supprimée de la couche cible.")

        # Créer un index pour rechercher les entités par IDU
        target_idu_index = {}
        for target_feature in target_layer.getFeatures():
            target_idu_index[target_feature[idu]] = target_feature

        # boucle sur toutes les entités de source_layer
        for source_feature in source_layer.getFeatures():
            source_idu_value = source_feature[idu]

            # Vérifier si l'entité existe déjà dans la couche cible
            if source_idu_value in target_idu_index:
                target_feature = target_idu_index[source_idu_value]
                update_required = False
                updated_fields = {}

                # Comparer les attributs avec la vérification de la date si date_groupBox est activé

                if date_groupBox and date_groupBox.isChecked():
                    source_date_maj = source_feature['date_maj']
                    target_date_maj = target_feature['date_maj']
                    print("source date : " + str(source_date_maj) + "target date : " + str(target_date_maj) )
                    print(str(source_date_maj > target_date_maj))
                    # Comparer la date source avec la valeur de date_maj passée en paramètre
                    if date_maj and source_date_maj > target_date_maj:
                        
                        for field in source_layer.fields():
                            if field.name() != 'fid' and source_feature[field.name()] != target_feature[field.name()]:
                                update_required = True
                                updated_fields[field.name()] = {
                                    'old_value': target_feature[field.name()],
                                    'new_value': source_feature[field.name()]
                                }
                else:
                    # Comparer sans tenir compte de la date
                    for field in source_layer.fields():
                        if field.name() != 'fid' and source_feature[field.name()] != target_feature[field.name()]:
                            update_required = True
                            updated_fields[field.name()] = {
                                'old_value': target_feature[field.name()],
                                'new_value': source_feature[field.name()]
                            }

                # Mettre à jour l'entité cible si nécessaire
                if update_required:
                    for field in source_layer.fields():
                        if field.name() != 'fid':  # Inclure IDU
                            target_feature.setAttribute(field.name(), source_feature[field.name()])

                    # Mettre à jour la géométrie
                    if source_layer.geometryType() != QgsWkbTypes.NullGeometry:
                        target_feature.setGeometry(source_feature.geometry())

                    target_layer.updateFeature(target_feature)

                    # Incrémenter le nombre d'entités mises à jour
                    report['updated_entities'] += 1

                    # Enregistrer les champs mis à jour pour cette entité
                    report['updated_fields'][source_idu_value] = updated_fields
            else:
                # Ajouter une nouvelle entité à la couche cible
                new_feature = QgsFeature(target_layer.fields())

                # Copier tous les attributs de la source vers la nouvelle entité
                for field in source_layer.fields():
                    if field.name() != 'fid':  # Inclure IDU
                        new_feature.setAttribute(field.name(), source_feature[field.name()])

                # Copier la géométrie de la source vers la nouvelle entité
                if source_layer.geometryType() != QgsWkbTypes.NullGeometry:
                    new_feature.setGeometry(source_feature.geometry())

                # Ajouter la nouvelle entité à la couche cible
                if target_layer.addFeature(new_feature):
                    report['added_entities'] += 1  # Incrémenter le nombre d'entités ajoutées
                else:
                    print(f"Impossible d'ajouter une nouvelle entité avec IDU {source_idu_value} à la couche cible.")

        # Valider et sauvegarder les modifications dans la couche cible
        if not target_layer.commitChanges():
            print("Erreur lors de la validation des modifications dans la couche cible.")
        
        # Remettre le filtre sur la couche cible
        target_layer.setSubsetString(target_filter)
        
        return report
    
    def check_attributs(self, source_layer, target_layer, idu):
        ''' Vérifier les entités de la couche target_layer qui n'ont pas de correspondance dans la couche source_layer'''
        idu_source = {f[idu] for f in source_layer.getFeatures()}
        idu_target = {f[idu] for f in target_layer.getFeatures()}
        print("Nombre d'attribut dans source_layer : ", len(idu_source))
        print("Nombre d'attribut dans target : ", len(idu_target))
        idu_checked = idu_source - idu_target
        return idu_checked

class FenetreEntitesOrphelines(QDialog):
    def __init__(self,features_uniquement_target, idu_field_name, parent=None):
        super().__init__(parent)
        self.idu_field_name = idu_field_name
        self.setWindowTitle("Entités uniquement dans la cible")
        self.resize(600, 400)

        for i, field in enumerate(features_uniquement_target[0].fields()):
            if field.name() == self.idu_field_name:
                self.idu_col_index = i
                break

        if self.idu_col_index is None:
            raise ValueError(f"Champ IDU '{self.idu_field_name}' introuvable")
        
        layout = QVBoxLayout(self)

        # Tableau pour afficher les entités
        self.table = QTableWidget(self)
        self.table.setRowCount(len(features_uniquement_target))
        self.table.setColumnCount(len(features_uniquement_target[0].fields()))
        self.table.setHorizontalHeaderLabels([f.name() for f in features_uniquement_target[0].fields()])
        # Remplir le tableau avec les données des entités
        for row, f in enumerate(features_uniquement_target):
            for col, field in enumerate(f.fields()):
                valeur = f[field.name()]

                # Gestion des dates
                if field.type() == QVariant.Date and valeur:
                    valeur_str = valeur.toString("dd/MM/yyyy")
                elif field.type() == QVariant.DateTime and valeur:
                    valeur_str = valeur.toString("dd/MM/yyyy HH:mm:ss")
                else:
                    valeur_str = str(valeur) if valeur is not None else ""

                self.table.setItem(row, col, QTableWidgetItem(valeur_str))

                layout.addWidget(self.table)

        # Boutons
        boutons_layout = QHBoxLayout()
        self.btn_supprimer = QPushButton("Supprimer les entités")
        self.btn_annuler = QPushButton("Annuler")
        boutons_layout.addWidget(self.btn_supprimer)
        boutons_layout.addWidget(self.btn_annuler)

        layout.addLayout(boutons_layout)

        # Signaux
        self.btn_supprimer.clicked.connect(self.accept)
        self.btn_annuler.clicked.connect(self.reject)
        self.show()

    def get_selected_idus(self):
        selected_idus = []

        for item in self.table.selectionModel().selectedRows():
            row = item.row()
            idu_item = self.table.item(row, self.idu_col_index)

            if idu_item is not None:
                idu_value = idu_item.text()
                selected_idus.append(idu_value)
                
        print("IDU sélectionné pour suppression :", selected_idus)
        return selected_idus




