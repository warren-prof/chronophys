# ChronoPhys est un logiciel gratuit pour réaliser des chronophotographies en Sciences-Physiques
# License Créative Commons : Attribution - Pas d'Utilisation Commerciale - Partage dans les Mêmes Conditions (BY-NC-SA)
# Auteur : Thibault Giauffret, ensciences.fr (2022)
# Version : dev-beta v0.4.1 (09 mai 2022)


# --------------------------------------------------   
# Importation des librairies
# -------------------------------------------------- 
import sys, os, csv, time, subprocess

# Gestion de l'interface
from PyQt5.QtCore import (
    QObject,
    pyqtSignal,
    pyqtSlot,
    QLocale,
    QRect,
    QPoint,
    QThread,
    Qt,
    QTimer
)
from PyQt5.QtGui import (
    QIcon,
    QDoubleValidator,
    QIntValidator,
    QPixmap,
    QPainter,
    QPen,
    QBrush,
    QImage,
    QColor,
    QPalette,
    QTransform
)
from PyQt5.QtWidgets import (
    QMainWindow,
    QSizePolicy,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QFileDialog,
    QDialogButtonBox,
    QLabel,
    QApplication,
    QDialog, 
    QLabel,
    QWidget, 
    QTableWidgetItem,
    QSpacerItem
)
from PyQt5.uic import loadUi
from waitingspinnerwidget import QtWaitingSpinner

# Gestion des délais (pour la lecture)
from time import sleep

# Gestion de la copie dans le presse-papier
from pyperclip import copy as pccopy

# Gestion des tableaux et des listes
from numpy import (linspace, array)

# Gestion des graphiques et du canvas
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

# Gestion de l'importation avec OpenCV
from extract import (extract_images, extract_infos, webcam_init, webcam_get_image, webcam_init_capture, webcam_write_image, webcam_end_capture, list_webcam_ports, release_cap)
from webserver import (get_address, start_server)

# Gestion des qrcodes
import qrcode

# Récupération du chemin absolu vers l'application
from pathlib import Path

if getattr(sys, 'frozen', False):
    application_path = str(Path(os.path.dirname(os.path.realpath(sys.executable))))
elif __file__:
    application_path = str(Path(os.path.dirname(os.path.realpath(__file__))))

import logging
# create logger 
logger = logging.getLogger('debug')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('debug.log',mode='w')
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)

# --------------------------------------------------   
# Classe principale gérant l'application
# -------------------------------------------------- 
class Window(QMainWindow):

    # --------------------------------------------------   
    # Initialisation de la fenêtre
    # --------------------------------------------------  
    def __init__(self):
        super().__init__()
        logger.info("Affichage de la fenêtre principale")

        # Importation de l'interface de base
        loadUi(resource_path('assets/ui/main.ui'), self)
        self.setWindowIcon(QIcon(resource_path('assets/icons/icon.png')))
        logger.info("Chargement de l'interface main.ui réalisée avec succès")
       
        # Initialisation des variables
        self.mesures = False
        self.t = array([])
        self.x = array([])
        self.y = array([])
        self.images = []
        self.loupe = False
        self.newopen = False
        self.webserver_running = False
        self.version = "<b>ChronoPhys</b> est un logiciel gratuit pour réaliser des chronophotographies en Sciences-Physiques<br><br><b>License Créative Commons</b> : Attribution - Pas d'Utilisation Commerciale - Partage dans les Mêmes Conditions (BY-NC-SA)<br><b>Auteur</b> : Thibault Giauffret, <a href=\"https://ensciences.fr\">ensciences.fr</a>(2022)<hr><b>Version</b> : dev-beta v0.4.1 (09 mai 2022)<br><b>Bugs</b> : <a href=\"mailto:contact@ensciences.fr\">contact@ensciences.fr</a>"

        # Ajout du plot au canvas
        self.figure = Figure()
        self.sc = FigureCanvasQTAgg(self.figure)
        self.figure.patch.set_facecolor("None")
        self.figure.tight_layout(pad=0)
        self.sc.axes = self.figure.add_subplot(111)

        # Gestion de la taille du plot
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.sc.setSizePolicy(sizePolicy)

        # Affichage de l'image initiale
        self.sc.setStyleSheet("background-color:transparent;")
        img = matplotlib.image.imread(resource_path('assets/icons/stopwatch.png'))
        self.sc.axes.imshow(img, extent=[-img.shape[1]/2., img.shape[1]/2., -img.shape[0]/2., img.shape[0]/2. ])
        self.sc.axes.set_axis_off()
        self.sc.axes.margins(0)
        self.clickEvent = self.sc.mpl_connect('button_press_event',self.measure_event)
        self.moveEvent = self.sc.mpl_connect('motion_notify_event',self.loupe_update)

        layout = QVBoxLayout()
        layout.addWidget(self.sc)

        # Creation d'un widget contenant le canvas
        self.mainWidget= QWidget(self.mainGroup)
        self.sc.updateGeometry()
        self.sc.setContentsMargins(0, 0, 0, 0)
        self.mainWidget.setLayout(layout)
        
        # Mise en arrière plan du canvas
        self.sc.lower()
 
        # Préparation des autres éléments de l'interface (activation, remplacement des libellés, utilisation d'icônes...)
        self.tabWidget.setTabEnabled(1, False);
        self.openButton.clicked.connect(self.video_open);
        self.phoneButton.clicked.connect(self.smartphone_video_open);
        self.webcamButton.clicked.connect(self.webcam_video_open);
        self.actionOuvrir_un_fichier_vid_o.triggered.connect(self.video_open)
        self.actionEnregistrer_une_vid_o_avec_un_smartphone.triggered.connect(self.smartphone_video_open)
        self.actionEnregistrer_une_vid_o_avec_la_webcam.triggered.connect(self.webcam_video_open)
        self.loupeBox.hide()


        self.playButton.setText('')
        self.playButton.setIcon(self.icon_from_svg(resource_path("assets/icons/play.svg")))
        self.pauseButton.setText('')
        self.pauseButton.setIcon(self.icon_from_svg(resource_path("assets/icons/pause.svg")))
        self.nextButton.setText('')
        self.nextButton.setIcon(self.icon_from_svg(resource_path("assets/icons/forward.svg")))
        self.prevButton.setText('')
        self.prevButton.setIcon(self.icon_from_svg(resource_path("assets/icons/backward.svg")))
        
        img = QPixmap(resource_path("assets/icons/video.svg"))
        qp = QPainter(img)
        qp.setCompositionMode(QPainter.CompositionMode_SourceIn)
        qp.fillRect( img.rect(), QColor(255,255,255))
        qp.end()
        self.openButton.setIcon(QIcon(img))
        #self.openButton.setIcon(self.icon_from_svg(resource_path("assets/icons/video.svg")))

        img = QPixmap(resource_path("assets/icons/camera-security.svg"))
        qp = QPainter(img)
        qp.setCompositionMode(QPainter.CompositionMode_SourceIn)
        qp.fillRect( img.rect(), QColor(255,255,255))
        qp.end()
        self.webcamButton.setIcon(QIcon(img))
        #self.webcamButton.setIcon(self.icon_from_svg(resource_path("assets/icons/camera-security.svg")))
        
        img = QPixmap(resource_path("assets/icons/mobile-signal-out.svg"))
        qp = QPainter(img)
        qp.setCompositionMode(QPainter.CompositionMode_SourceIn)
        qp.fillRect( img.rect(), QColor(255,255,255))
        qp.end()
        self.phoneButton.setIcon(QIcon(img))
        #self.phoneButton.setIcon(self.icon_from_svg(resource_path("assets/icons/mobile-signal-out.svg")))

        self.saveButton.setText('')
        self.saveButton.setStyleSheet("font-weight: bold;background-color:'#1b7a46';")
        img = QPixmap(resource_path("assets/icons/floppy-disk.svg"))
        qp = QPainter(img)
        qp.setCompositionMode(QPainter.CompositionMode_SourceIn)
        qp.fillRect( img.rect(), QColor(255,255,255))
        qp.end()
        self.saveButton.setIcon(QIcon(img))
        #self.saveButton.setIcon(self.icon_from_svg(resource_path("assets/icons/floppy-disk.svg")))
        self.loupeButton.setText('')
        self.loupeButton.setIcon(self.icon_from_svg(resource_path("assets/icons/magnifying-glass.svg")))
        
        self.validateButton.setIcon(self.icon_from_svg(resource_path("assets/icons/circle-check.svg")))
        self.rulerButton.setIcon(self.icon_from_svg(resource_path("assets/icons/ruler-triangle.svg")))
        self.repereButton.setIcon(self.icon_from_svg(resource_path("assets/icons/bullseye-arrow.svg")))
        self.formeButton.setIcon(self.icon_from_svg(resource_path("assets/icons/paintbrush.svg")))
        self.imageLabel.setText('')

        self.axeButton_1.setIcon(self.icon_from_svg(resource_path("assets/icons/axis1.svg")))
        self.axeButton_3.setIcon(self.icon_from_svg(resource_path("assets/icons/axis4.svg")))
        self.axeButton_4.setIcon(self.icon_from_svg(resource_path("assets/icons/axis2.svg")))
        self.axeButton_5.setIcon(self.icon_from_svg(resource_path("assets/icons/axis3.svg")))

        self.etalonBox.setEnabled(False)
        self.repereBox.setEnabled(False)
        self.styleBox.setEnabled(False)
        self.validateButton.setEnabled(False)
        self.tabWidget.setTabEnabled(2, False);


        self.onlyDouble = QDoubleValidator()
        self.onlyDouble.setLocale(QLocale("en_US"))
        self.valeurEtalon.setValidator(self.onlyDouble)

        self.action_propos.triggered.connect(self.infos_clicked)
        self.playButton.clicked.connect(self.play)

        # Affichage de la fenêtre
        self.show()

        self.loupeButton.clicked.connect(self.loupe_clicked)
        self.canvas_resize()

        logger.info("Fin de l'initialisation de l'interface")

    # --------------------------------------------------   
    # Complétion de l'interface une fois la video ouverte
    # --------------------------------------------------  

    def ui_update(self):

        logger.info("Mise à jour de l'interface")

        self.canvas_resize()

        try:
            self.sc.mpl_disconnect(self.clickEvent)
        except:
            logger.warning("Impossible de déconnecter l'évènement de clic sur canvas. Déjà déconnecté ?!") 

        self.label_nombre.setText(str(self.videoConfig["nb_images"]))
        self.label_ips.setText(str(self.videoConfig["fps"]))
        self.label_duree.setText(str(self.videoConfig["duration"]))
        self.label_largeur.setText(str(self.videoConfig["width"]))
        self.label_hauteur.setText(str(self.videoConfig["height"]))
        self.tabWidget.setTabEnabled(2, True)

        self.pixmap = QPixmap(resource_path("assets/icons/ensciences.svg")).scaled(78, 78, Qt.KeepAspectRatio)
        self.label_ensciences.setPixmap(self.pixmap) 
        self.label_ensciences.resize(80,80) 

        self.pixmap = QPixmap(resource_path("assets/icons/icon.svg")).scaled(78, 78, Qt.KeepAspectRatio)
        self.label_chrono.setPixmap(self.pixmap) 
        self.label_chrono.resize(80,80) 

        self.label_infos.setText(self.version)
        self.label_infos.setTextFormat(Qt.RichText)

        self.openButton.setStyleSheet("font-weight: bold;")
        self.phoneButton.setStyleSheet("font-weight: bold;")
        self.webcamButton.setStyleSheet("font-weight: bold;")
        self.openButton.setIcon(self.icon_from_svg(resource_path("assets/icons/video.svg")))
        self.phoneButton.setIcon(self.icon_from_svg(resource_path("assets/icons/mobile-signal-out.svg")))
        self.webcamButton.setIcon(self.icon_from_svg(resource_path("assets/icons/camera-security.svg")))
        

        self.repereBox.setStyleSheet("QGroupBox {\n    border: 2px solid gray;\n    border-color: #155e36;\n    margin-top: 27px;\n    font-size: 14px;\n    border-bottom-left-radius: 0px;\n    border-bottom-right-radius: 0px;\n}\n\nQGroupBox::title {\n    subcontrol-origin: margin;\n    subcontrol-position: top center;\n    border-top-left-radius: 0px;\n    border-top-right-radius: 0px;\n    padding: 5px 150px;\n    background-color: #155e36;\n    color: rgb(255, 255, 255);\n}")
        self.repereBox.setEnabled(True)

        self.etalonBox.setStyleSheet("QGroupBox {\n    border: 2px solid gray;\n    border-color: #FF17365D;\n    margin-top: 27px;\n    font-size: 14px;\n    border-bottom-left-radius: 0px;\n    border-bottom-right-radius: 0px;\n}\n\nQGroupBox::title {\n    subcontrol-origin: margin;\n    subcontrol-position: top center;\n    border-top-left-radius: 0px;\n    border-top-right-radius: 0px;\n    padding: 5px 150px;\n    background-color: #FF17365D;\n    color: rgb(255, 255, 255);\n}")
        self.buttonGroup.setExclusive(False)
        self.firstPoint.setChecked(False)
        self.secondPoint.setChecked(False)
        self.buttonGroup.setExclusive(True)
        self.etalonBox.setEnabled(False)

        self.styleBox.setEnabled(False)

        # Chargement dans le canvas de la première image de la vidéo
        self.sc.axes.cla()  # clear the axes content
        self.figure.subplots_adjust(bottom=0, right=1, top=1, left=0)
        self.mywidth = self.images[self.current_image].shape[0]
        self.myheight = self.images[self.current_image].shape[1]
        self.Vaxis_orient = 1
        self.Haxis_orient = 1
        self.Vaxis_ratio = 0.5
        self.Haxis_ratio = 0.5
        self.old_axisParam = (1,1)
        self.ratio = [-self.Vaxis_ratio*self.mywidth,self.Vaxis_ratio*self.mywidth,-self.Haxis_ratio*self.myheight,self.Haxis_ratio*self.myheight]

        self.playStatus = False
        self.axis_set = False
        self.etalonnage = {"status":"stage1", "done":False, "x1":0, "y1":0,"x2":0,"y2":0,"valeurMetres":0,"valeurPixels":0}
        self.axisType = 1
        self.showEtalon = False
        self.applyOrient = False
        self.settings = {"color":"b","line":"","point":".","grid":False,"ticks":True}

        bottom = -self.mywidth*self.Haxis_ratio
        top = self.mywidth-abs(bottom)
        left = -self.myheight*self.Vaxis_ratio
        right = self.myheight-abs(left)
        # print(self.Haxis_orient*left,self.Haxis_orient*right,self.Vaxis_orient*bottom,self.Vaxis_orient*top)
        self.myextent=[self.Haxis_orient*left, self.Haxis_orient*right,self.Vaxis_orient*bottom, self.Vaxis_orient*top]
        self.ratio = [left,right,bottom,top]

        self.sc.axes.imshow(self.images[0], extent=[ -self.myheight*self.Vaxis_ratio, self.myheight*(1-self.Vaxis_ratio),-self.mywidth*self.Haxis_ratio, self.mywidth*(1-self.Haxis_ratio)])
        self.sc.axes.margins(0)
        self.sc.setContentsMargins(0, 0, 0, 0)

        self.sc.draw_idle()

        self.horizontalSlider.setRange(1, self.nb_images)

        self.axis_update()
        
        # Configuration des boutons 
        if self.newopen == False:
            self.pauseButton.clicked.connect(self.pause)
            self.nextButton.clicked.connect(self.next_clicked)
            self.prevButton.clicked.connect(self.prev_clicked)
            self.validateButton.clicked.connect(self.start_measures)
            self.axeButton_1.clicked.connect(lambda: self.axe_clicked(1))
            self.axeButton_3.clicked.connect(lambda: self.axe_clicked(2))
            self.axeButton_4.clicked.connect(lambda: self.axe_clicked(3))
            self.axeButton_5.clicked.connect(lambda: self.axe_clicked(4))
            self.repereButton.clicked.connect(self.repere_clicked)
            self.firstPoint.toggled.connect(lambda: self.etalonnage_clicked(1))
            self.secondPoint.toggled.connect(lambda: self.etalonnage_clicked(2))
            self.rulerButton.clicked.connect(self.ruler_clicked)
            self.horizontalSlider.valueChanged.connect(self.slider_update)
            self.saveButton.clicked.connect(lambda: self.save_clicked(self.comboBox.currentIndex()))
            self.tableWidget.clicked.connect(self.row_changed)
            self.tabWidget.tabBarClicked.connect(self.tabbar_clicked)
            self.tableWidget.itemDoubleClicked.connect(self.table_clicked)
            self.formeButton.clicked.connect(self.settings_update)

            # Triggers dans le menubar
            self.actionCopier_dans_le_presse_papier.triggered.connect(lambda: self.save_clicked(0))
            self.actionSauvergarder_au_format_csv.triggered.connect(lambda: self.save_clicked(1))
            self.actionEnregistrer_le_code_Python_py.triggered.connect(lambda: self.save_clicked(2))
            self.actionExporter_le_graphique.triggered.connect(lambda: self.save_clicked(3))

        # Modification du widget tableau pour les valeurs
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setRowCount(self.nb_images) 
        self.tableWidget.setHorizontalHeaderLabels(["Temps (s)", "x (m)", "y (m)" ]) 

        logger.info("Mise à jour de l'interface réussie")

    # --------------------------------------------------   
    # Gestion du redimensionnement de la fenêtre
    # -------------------------------------------------- 

    def canvas_resize(self):
        self.mainWidget.setGeometry(QRect(0, 0, self.mainGroup.width(), self.mainGroup.height()))
        self.sc.setGeometry(QRect(0, 0, self.mainGroup.width(), self.mainGroup.height()))

    def resizeEvent(self, event):
        self.canvas_resize()
    
    # --------------------------------------------------   
    # Gestion de l'ouverture de la vidéo
    # --------------------------------------------------  

    def video_open(self):
        logger.info("Clic openButton")
        dialog = QFileDialog(self)
        dialog.setNameFilter(str("Video (*.mp4 *.avi *.wmv *mov);;All Files (*.*)"))
        dialog.setDirectory(os.getenv('HOME'))
        if dialog.exec_():
            filename = dialog.selectedFiles()[0]
            logger.info("Vidéo sélectionnée : "+filename)
            self.import_video(filename)

    def get_import_data(self, images, videoConfig, error, video_timestamp):
        logger.info("Importation des données de la vidéo")
        self.dlg_wait.stop()
        if error == False:
            self.images = images
            self.videoConfig = videoConfig
            self.video_timestamp = video_timestamp
            self.nb_images = self.videoConfig["nb_images"]
            self.duration = self.videoConfig["duration"]
            self.current_image = 0
            #print(self.images[self.current_image])
            self.imageLabel.setText('Image : '+str(self.current_image+1)+'/'+str(self.nb_images))
            self.horizontalSlider.setValue(self.current_image+1)
            self.t = array([None for i in range(self.nb_images)])
            self.x = array([None for i in range(self.nb_images)])
            self.y = array([None for i in range(self.nb_images)])
            self.ui_update()
            self.newopen = True
        else:
            dlg = CustomDialog("Une erreur est survenue lors de l'ouverture de la vidéo. Assurez-vous qu'elle contienne moins de 150 images.")
            logger.warning("La vidéo contient trop d'images...")
            if dlg.exec():
                print("Success!")
            else:
                print("Cancel!")

            
    # --------------------------------------------------   
    # Gestion du serveur web (envie video depuis smartphone)
    # --------------------------------------------------  

    def smartphone_video_open(self):

        logger.info("Importation d'une vidéo depuis un smartphone")
        if self.webserver_running == False:
            logger.info("Lancement du thread avec WebWorker")
            try :
                # On crée le QThread object
                self.web_thread = QThread()
                self.web_thread.setTerminationEnabled(True)

                # On crée l'objet "Worker"
                self.web_worker = WebWorker()

                # On déplace le worker dans le thread
                self.web_worker.moveToThread(self.web_thread)

                # On connecte les signaux et les slots
                self.web_thread.started.connect(self.web_worker.run)
                self.web_worker.finished.connect(self.stop_webserver)
                self.web_worker.finished.connect(self.web_thread.quit)
                self.web_worker.finished.connect(self.web_worker.deleteLater)
                self.web_thread.finished.connect(self.web_thread.deleteLater)

                self.web_worker.video.connect(self.video_received)

                # On démarre le thread
                self.web_thread.start()

                self.webserver_running = True
            except Exception as ex:
                logger.exception("Une erreur est survenue : " + str(ex))

        self.server_dlg = WebDialog()
        if self.server_dlg.exec():
            print("Success!")
        else:
            print("Cancel!")

    def stop_webserver(self):
        self.webserver_running = False

    def video_received(self,filename):
        logger.info("Réception d'une vidéo depuis le serveur web")
        filename = "./videos/"+filename
        dlg = CustomDialog("Une vidéo a été reçue, voulez-vous l'ouvrir ?")
        if dlg.exec():
            self.server_dlg.stop()
            self.import_video(filename)
        else:
            logger.info("Importation refusée")

    def import_video(self, filename):
        logger.info("Importation de la vidéo")
        try :
            logger.info("Extraction des informations de la vidéo")
            frame, camera_Width,camera_Height ,fps,frame_count,duration = extract_infos(str(filename))
            dlg2 = ImportDialog(frame,camera_Width,camera_Height ,fps,frame_count,duration )
        except Exception as ex :
            logger.exception("Une erreur est survenue : " + str(ex))

        if dlg2.exec_() == QDialog.Accepted:
            self.dlg_wait = WaitDialog()
            
            if self.dlg_wait.start():
                value = dlg2.GetValue()
                
                try :
                    # On crée le QThread object
                    self.import_thread = QThread()
                    self.import_thread.setTerminationEnabled(True)

                    # On crée l'objet "Worker"
                    self.import_worker = ImportWorker(filename, value)

                    # On déplace le worker dans le thread
                    self.import_worker.moveToThread(self.import_thread)

                    # On connecte les signaux et les slots
                    self.import_thread.started.connect(self.import_worker.run)
                    self.import_worker.finished.connect(self.stop)
                    self.import_worker.finished.connect(self.import_thread.quit)
                    self.import_worker.finished.connect(self.import_worker.deleteLater)
                    self.import_thread.finished.connect(self.import_thread.deleteLater)

                    self.import_worker.data.connect(self.get_import_data)

                    # On démarre le thread
                    self.import_thread.start()
                except Exception as ex:
                    logger.exception("Une erreur est survenue : " + str(ex))
                
        else:
            logger.info("Importation refusée")


    # --------------------------------------------------   
    # Gestion de la webcam
    # --------------------------------------------------  
    def webcam_video_open(self):
        self.webcam_dlg = WebcamDialog()
        if self.webcam_dlg.exec():
            logger.info("Enregistrement webcam confirmé")
            print("Success!")
            self.webcam_dlg.release()
            if self.webcam_dlg.recordDone == True:
                self.import_video(self.webcam_dlg.video_path)
        else:
            logger.info("Enregistrement webcam annulé")
            self.webcam_dlg.release()


    # --------------------------------------------------   
    # Gestion des contrôles
    # --------------------------------------------------  

    def play(self):
        logger.info("Clic playButton, lecture de la vidéo")
        if self.images != []:
            self.playButton.setEnabled(False);
            self.scrollArea.setEnabled(False);
            self.playStatus = True

            try :
                # On crée le QThread object
                self.mythread = QThread()
                self.mythread.setTerminationEnabled(True)


                # On crée l'objet "Worker"
                self.worker = Worker(images= self.images, x=self.x, y=self.y, axes=self.sc.axes,myextent = self.myextent,etalonnage=self.etalonnage,showEtalon=self.showEtalon,ratio=self.ratio,settings=self.settings, current_image=self.current_image, nb_images=self.nb_images)

                # On déplace le worker dans le thread
                self.worker.moveToThread(self.mythread)

                # On connecte les signaux et les slots
                self.mythread.started.connect(self.worker.run)
                self.worker.finished.connect(self.stop)
                self.worker.finished.connect(self.mythread.quit)
                self.worker.finished.connect(self.worker.deleteLater)
                self.mythread.finished.connect(self.mythread.deleteLater)

                self.worker.data.connect(self.play_update)

                # On démarre le thread
                self.mythread.start()
            except Exception as ex:
                logger.exception("Une erreur est survenue : " + str(ex))

    def stop(self):
        logger.info("Arrêt de la lecture")
        self.playStatus = False
        self.playButton.setEnabled(True);
        self.scrollArea.setEnabled(True);

    def pause(self):
        try:
            self.worker.stop()
        except:
            logger.warning("Tentative d'arrêt de la lecture. Déjà arrêté ?")
        

    def next_clicked(self):
        logger.info("Clic nextButton")
        if self.current_image < self.nb_images-1 and self.playStatus == False:
            self.current_image+=1
            self.horizontalSlider.setValue(self.current_image+1)
            self.canvas_update()

    def prev_clicked(self):
        logger.info("Clic prevButton")
        if self.current_image > 0 and self.playStatus == False:
            self.current_image-=1
            self.horizontalSlider.setValue(self.current_image+1)
            self.canvas_update()

    # --------------------------------------------------   
    # Gestion de la loupe
    # --------------------------------------------------  

    def loupe_clicked(self):
        logger.info("Clic loupeButton")
        if self.loupe == False :
            self.loupeBox.show()
            self.loupe = True
        else:
            self.loupeBox.hide()
            self.loupe = False

    def loupe_update(self,event):
        if self.loupe == True and self.images !=[]:
            bottom = self.mywidth*(1-self.Haxis_ratio)
            left = self.myheight*(self.Vaxis_ratio)

            if event.xdata!=None and event.ydata!=None :
                posx = (abs(left)+(self.Haxis_orient*event.xdata))+1
                posy = (abs(bottom)-(self.Vaxis_orient*event.ydata))+1
                if int(posy-0.05*self.mywidth) > 0 and  int(posx-0.05*self.mywidth)>0 and int(posy+0.05*self.mywidth) <= self.mywidth and  int(posx+0.05*self.mywidth) <= self.myheight:

                    axe = QPixmap(135, 135)
                    axe.fill(Qt.transparent)            
                    p = QPainter(axe)
                    pen = QPen(QBrush(QColor(10,10,10,230)), 2)
                    p.setPen(pen)
                    p.drawLine(135, int(135/2), 0, int(135/2))
                    p.drawLine(int(135/2),135, int(135/2),0)
                    p.end()
                    axe.scaled(135, 135,Qt.KeepAspectRatio, Qt.FastTransformation)

                    image = (self.images[self.current_image][int(posy-0.05*self.mywidth):int(posy+0.05*self.mywidth),int(posx-0.05*self.mywidth):int(posx+0.05*self.mywidth)]).copy()
                    #print(image)
                    #print(image.shape[1],image.shape[0])
                    img = QImage(image, image.shape[1], image.shape[0], image.shape[1] * 3,QImage.Format_RGB888)
                    pixmap = QPixmap(img).scaled(135, 135,Qt.KeepAspectRatio, Qt.FastTransformation)


                    s = pixmap.size()
                    result =  QPixmap(s)
                    result.fill(Qt.transparent)
                    painter = QPainter(result)
                    painter.setRenderHint(QPainter.Antialiasing)
                    painter.drawPixmap(QPoint(), pixmap)
                    painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                    painter.drawPixmap(result.rect(), axe, axe.rect())
                    painter.end()

                    # size = self.pixmap.size()
                    # self.pixmap.scaled(1 * size)
                    self.loupeBox.setPixmap(result)
            

    # --------------------------------------------------   
    # Gestion des évènements sur le canvas mpl et
    # mises à jours correpondantes
    # --------------------------------------------------  

    def axe_clicked(self,value):
        logger.info("Clic axeButton")
        self.axis_set = True
        self.applyOrient = True

        self.old_axisParam = self.orient_update(self.axisType)

        self.axisType = value

        try:
            self.sc.mpl_disconnect(self.clickEvent)
        except:
            logger.warning("Impossible de déconnecter l'évènement de clic sur canvas. Déjà déconnecté ?!")
        logger.info("Connexion de l'évènement clic sur canvas avec la fonction axis_event")
        self.clickEvent = self.sc.mpl_connect('button_press_event',self.axis_event)

    def orient_update(self,value):
        logger.info("Mise à jour des paramètres pour l'orientation des axes")
        if value == 1:
            return (1,1)
            self.Vaxis_orient = 1
            self.Haxis_orient = 1
        elif value == 2:
            return (-1, 1)
            self.Vaxis_orient = -1
            self.Haxis_orient = 1
        elif value == 3:
            return (1,-1)
            self.Vaxis_orient = 1
            self.Haxis_orient = -1
        elif value == 4:
            return (-1,-1)
            self.Vaxis_orient = -1
            self.Haxis_orient = -1

    def axis_update(self):
        logger.info("Mise à jour des axes")
        self.sc.axes.spines["left"].set_position(("data", 0))
        self.sc.axes.spines["bottom"].set_position(("data", 0))
        # Hide the top and right spines.
        self.sc.axes.spines["top"].set_visible(False)
        self.sc.axes.spines["right"].set_visible(False)

        if self.axisType == 1:
            self.sc.axes.plot(1, 0, ">k", transform=self.sc.axes.get_yaxis_transform(), clip_on=False)
            self.sc.axes.plot(0, 1, "^k", transform=self.sc.axes.get_xaxis_transform(), clip_on=False)
        elif self.axisType == 2:
            self.sc.axes.plot(1, 0, ">k", transform=self.sc.axes.get_yaxis_transform(), clip_on=False)
            self.sc.axes.plot(0, 0, "vk", transform=self.sc.axes.get_xaxis_transform(), clip_on=False)
        elif self.axisType == 3:
            self.sc.axes.plot(0, 0, "<k", transform=self.sc.axes.get_yaxis_transform(), clip_on=False)
            self.sc.axes.plot(0, 1, "^k", transform=self.sc.axes.get_xaxis_transform(), clip_on=False)
        elif self.axisType == 4:
            self.sc.axes.plot(0, 0, "<k", transform=self.sc.axes.get_yaxis_transform(), clip_on=False)
            self.sc.axes.plot(0, 0, "vk", transform=self.sc.axes.get_xaxis_transform(), clip_on=False)
    
    def repere_clicked(self):
        logger.info("Clic repereButton")
        self.etalonBox.setEnabled(True)
        try:
            self.sc.mpl_disconnect(self.clickEvent)
        except:
            logger.warning("Impossible de déconnecter l'évènement de clic sur canvas. Déjà déconnecté ?!")
        logger.info("Connexion de l'évènement clic sur canvas avec la fonction measure_event")
        self.clickEvent = self.sc.mpl_connect('button_press_event',self.measure_event)
        self.axis_set = False

        self.repereBox.setStyleSheet("QGroupBox {\n    border: 2px solid gray;\n    border-color: #FF17365D;\n    margin-top: 27px;\n    font-size: 14px;\n    border-bottom-left-radius: 0px;\n    border-bottom-right-radius: 0px;\n}\n\nQGroupBox::title {\n    subcontrol-origin: margin;\n    subcontrol-position: top center;\n    border-top-left-radius: 0px;\n    border-top-right-radius: 0px;\n    padding: 5px 150px;\n    background-color: #FF17365D;\n    color: rgb(255, 255, 255);\n}")

        self.etalonBox.setStyleSheet("QGroupBox {\n    border: 2px solid gray;\n    border-color: #155e36;\n    margin-top: 27px;\n    font-size: 14px;\n    border-bottom-left-radius: 0px;\n    border-bottom-right-radius: 0px;\n}\n\nQGroupBox::title {\n    subcontrol-origin: margin;\n    subcontrol-position: top center;\n    border-top-left-radius: 0px;\n    border-top-right-radius: 0px;\n    padding: 5px 150px;\n    background-color: #155e36;\n    color: rgb(255, 255, 255);\n}")

    def axis_event(self, event):
        if self.axis_set == True and event.xdata!=None and event.ydata!=None:
    
            # print('Old ratio was :',self.Haxis_ratio,self.Vaxis_ratio)
            # print('Center set to :',event.xdata,event.ydata)

            self.Haxis_ratio = (self.Haxis_ratio*self.mywidth+self.Vaxis_orient*event.ydata)/self.mywidth

            self.Vaxis_ratio = (self.Vaxis_ratio*self.myheight+self.Haxis_orient*event.xdata)/self.myheight

            # print('New ratio is :',self.Haxis_ratio,self.Vaxis_ratio)

            # On met à jour les différents plots...
            for i in range(len(self.x)):
                if self.x[i] != None and self.y[i] != None:
                    self.x[i]=(self.x[i]-event.xdata)
                    self.y[i]=(self.y[i]-event.ydata)
                    self.table_update(i,self.x[i],self.y[i])
            self.etalonnage["x1"]-=event.xdata
            self.etalonnage["x2"]-=event.xdata
            self.etalonnage["y1"]-=event.ydata
            self.etalonnage["y2"]-=event.ydata
            self.canvas_update()
            
    def etalonnage_clicked(self, value):
        try:
            self.sc.mpl_disconnect(self.clickEvent)
        except:
            logger.warning("Impossible de déconnecter l'évènement de clic sur canvas. Déjà déconnecté ?!")
        logger.info("Connexion de l'évènement clic sur canvas avec la fonction etalon_event")
        self.clickEvent = self.sc.mpl_connect('button_press_event',self.etalon_event)
        #self.validateButton.setStyleSheet("font-weight: bold;color:'#fff'")
        if value == 1:
            self.etalonnage["status"] = "stage1"
            #print("Prise du premier point pour l'étalonnage")
        elif value == 2:
            self.etalonnage["status"] = "stage2"
            #print("Prise du second point pour l'étalonnage")

    def ruler_clicked(self):
        logger.info("Clic rulerButton")
        if self.valeurEtalon.text() != "":
            self.buttonGroup.setExclusive(False)
            self.firstPoint.setChecked(False)
            self.secondPoint.setChecked(False)
            self.buttonGroup.setExclusive(True)

            self.validateButton.setEnabled(True)

            self.styleBox.setEnabled(True)
            self.valeurEtalon.setStyleSheet("")
            if self.etalonnage["done"] == True:
                self.etalonnage["old_valeurMetres"] = self.etalonnage["valeurMetres"]
                self.etalonnage["old_valeurPixels"] = self.etalonnage["valeurPixels"]
            self.etalonnage["valeurMetres"] = float(self.valeurEtalon.text().replace(',','.'))
            self.etalonnage["valeurPixels"] = ((self.etalonnage["x1"]-self.etalonnage["x2"])**2+(self.etalonnage["y1"]-self.etalonnage["y2"])**2)**(1/2)
            self.etalonnage["done"] = True
            self.labelEtalon.setText(str(round(self.etalonnage["valeurPixels"],2))+" pixels équivalent à "+str(self.etalonnage["valeurMetres"])+" mètres")
            # print(self.etalonnage)
            self.firstPoint.setChecked(False)
            self.secondPoint.setChecked(False)
            try:
                self.sc.mpl_disconnect(self.clickEvent)
            except:
                logger.warning("Impossible de déconnecter l'évènement de clic sur canvas. Déjà déconnecté ?!")
            logger.info("Connexion de l'évènement clic sur canvas avec la fonction measure_event")
            self.clickEvent = self.sc.mpl_connect('button_press_event',self.measure_event)

            self.etalonBox.setStyleSheet("QGroupBox {\n    border: 2px solid gray;\n    border-color: #FF17365D;\n    margin-top: 27px;\n    font-size: 14px;\n    border-bottom-left-radius: 0px;\n    border-bottom-right-radius: 0px;\n}\n\nQGroupBox::title {\n    subcontrol-origin: margin;\n    subcontrol-position: top center;\n    border-top-left-radius: 0px;\n    border-top-right-radius: 0px;\n    padding: 5px 150px;\n    background-color: #FF17365D;\n    color: rgb(255, 255, 255);\n}")
            self.validateButton.setStyleSheet("font-weight: bold;background-color:'#1b7a46';color:'#fff'")
            img = QPixmap(resource_path("assets/icons/circle-check.svg"))
            qp = QPainter(img)
            qp.setCompositionMode(QPainter.CompositionMode_SourceIn)
            qp.fillRect( img.rect(), QColor(255,255,255))
            qp.end()
            self.validateButton.setIcon(QIcon(img))
            self.table_update_etalon()

            self.canvas_update()
        else :
            dlg = CustomDialog("Veuillez entrer la valeur correspondante à l'étalon défini (en m) !")
            if dlg.exec():
                print("Success!")
                self.valeurEtalon.setStyleSheet("background-color:'#5a7a68';")
            else:
                print("Cancel!")
                self.valeurEtalon.setStyleSheet("background-color:'#5a7a68';")

    def etalon_event(self, event):
        self.showEtalon = True
        if self.etalonnage["status"] == "stage1" and event.xdata!=None and event.ydata!=None:
            self.etalonnage["x1"] = event.xdata
            self.etalonnage["y1"] = event.ydata
        elif self.etalonnage["status"] == "stage2" and event.xdata!=None and event.ydata!=None:
            self.etalonnage["x2"] = event.xdata
            self.etalonnage["y2"] = event.ydata
        self.canvas_update()

    def settings_update(self):
        logger.info("Clic formeButton")
        colorValue = self.comboColor.currentText()
        if colorValue == "Bleu":
            self.settings["color"] = "b"
        elif colorValue == "Rouge":
            self.settings["color"] = "r"
        elif colorValue == "Vert":
            self.settings["color"] = "g"
        elif colorValue == "Cyan":
            self.settings["color"] = "c"
        elif colorValue == "Magenta":
            self.settings["color"] = "m"
        elif colorValue == "Jaune":
            self.settings["color"] = "y"
        elif colorValue == "Blanc":
            self.settings["color"] = "w"
        elif colorValue == "Noir":
            self.settings["color"] = "k"
        else:
            self.settings["color"] = "b"

        formeValue = self.comboFormat.currentText()
        if formeValue == "Point":
            self.settings["point"] = "."
        elif formeValue == "Disque":
            self.settings["point"] = "o"
        elif formeValue == "Croix":
            self.settings["point"] = "x"
        elif formeValue == "Plus":
            self.settings["point"] = "+"
        elif formeValue == "Carré":
            self.settings["point"] = "s"
        elif formeValue == "Triangle":
            self.settings["point"] = "v"
        else:
            self.settings["point"] = "o"
        
        if self.checkLine.isChecked():
            self.settings["line"] = "--"
        else:
            self.settings["line"] = ""

        if self.checkGrid.isChecked():
            self.settings["grid"] = True
        else:
            self.settings["grid"] = False

        if self.checkTicks.isChecked():
            self.settings["ticks"] = True
        else:
            self.settings["ticks"] = False

        self.canvas_update()

    def measure_event(self, event):
        if self.mesures == True and event.xdata!=None and event.ydata!=None:
            # print('Event received:',event.xdata,event.ydata)

            self.table_update(self.current_image,event.xdata,event.ydata)

            self.t[self.current_image]=round(self.current_image*self.duration/self.nb_images,3);
            self.x[self.current_image]=event.xdata;
            self.y[self.current_image]=event.ydata;

            
            self.next_clicked()

            self.loupe_update(event)


    # --------------------------------------------------   
    # Gestion des évènements sur le tableau
    # --------------------------------------------------  

    def table_update(self,i,xdata,ydata):
        logger.info("Mise à jour de la table")
        # Ajout de la valeur de t dans la ligne correspondant à l'image
        self.item = QTableWidgetItem()
        self.item.setText(str(round(self.video_timestamp[self.current_image]/1000,3)))
        self.tableWidget.setItem(i, 0, self.item)

        # Ajout de la valeur de x dans la ligne correspondant à l'image
        self.item = QTableWidgetItem()
        self.item.setText(str(round(xdata*self.etalonnage["valeurMetres"]/self.etalonnage["valeurPixels"],3)))
        self.tableWidget.setItem(i, 1, self.item)

        # Ajout de la valeur de y dans la ligne correspondant à l'image
        self.item = QTableWidgetItem()
        self.item.setText(str(round(ydata*self.etalonnage["valeurMetres"]/self.etalonnage["valeurPixels"],3)))
        self.tableWidget.setItem(i, 2, self.item)

    def table_update_etalon(self):
        logger.info("Mise à jour de la table sur au changement de valeur d'étalon")
        if "old_valeurMetres" in self.etalonnage:
            for row in range(self.tableWidget.rowCount()):
                x_item = self.tableWidget.item(row, 1)
                y_item = self.tableWidget.item(row, 2)
                if x_item is not None and y_item is not None:
                    x_value = round(float(x_item.text())*self.etalonnage["valeurMetres"]*self.etalonnage["old_valeurPixels"]/(self.etalonnage["valeurPixels"]*self.etalonnage["old_valeurMetres"]),3)
                    y_value = round(float(y_item.text())*self.etalonnage["valeurMetres"]*self.etalonnage["old_valeurPixels"]/(self.etalonnage["valeurPixels"]*self.etalonnage["old_valeurMetres"]),3)
                    self.tableWidget.item(row, 1).setText(str(x_value))
                    self.tableWidget.item(row, 2).setText(str(y_value))



    def table_clicked(self,item):
        logger.info("Valeur de la table modifiée par l'utilisateur")
        self.tableWidget.itemChanged.connect(lambda : self.table_changed(item))
        # print("Item modified : "+str(item.row())+str(", ")+str(item.column())+str(", ")+str(item.text()))
        # print("Coresponding values in x y lists :"+str(self.x[item.row()])+str(", ")+str(self.y[item.row()]))

    def table_changed(self,item):
        
        if item.column() == 1:
            if item.text() != '':
                self.x[item.row()] = float(item.text())*self.etalonnage["valeurPixels"]/self.etalonnage["valeurMetres"]
            else:
                self.x[item.row()] = None
        elif item.column() == 2:
            if item.text() != '':
                self.y[item.row()] = float(item.text())*self.etalonnage["valeurPixels"]/self.etalonnage["valeurMetres"]
            else:
                self.y[item.row()] = None
        try: self.tableWidget.itemChanged.disconnect() 
        except Exception as ex: 
            logger.warning("Impossible de déconnecter l'évènement itemChanged sur tableWidget. Déjà déconnecté ?!")
        self.canvas_update()

    def row_changed(self,item):
        self.current_image = item.row()
        self.horizontalSlider.setValue(self.current_image+1)
        self.canvas_update()


    # --------------------------------------------------   
    # Fonction principale
    # --------------------------------------------------  

    def canvas_update(self):
        logger.info("Mise à jour du canvas")
        if self.etalonnage["done"] == True:
            old_labels = self.sc.axes.get_xticklabels()

        self.imageLabel.setText('Image : '+str(self.current_image+1)+'/'+str(self.nb_images))
        self.tableWidget.selectRow(self.current_image)
        # print("New image is " + str(self.current_image))
        self.sc.axes.cla() 

        if self.axisType == 1:
            self.Vaxis_orient = 1
            self.Haxis_orient = 1
        elif self.axisType == 2:
            self.Vaxis_orient = -1
            self.Haxis_orient = 1
        elif self.axisType == 3:
            self.Vaxis_orient = 1
            self.Haxis_orient = -1
        elif self.axisType == 4:
            self.Vaxis_orient = -1
            self.Haxis_orient = -1

        
        bottom = -self.mywidth*self.Haxis_ratio
        top = self.mywidth-abs(bottom)
        left = -self.myheight*self.Vaxis_ratio
        right = self.myheight-abs(left)
        # print(self.Haxis_orient*left,self.Haxis_orient*right,self.Vaxis_orient*bottom,self.Vaxis_orient*top)
        self.myextent=[self.Haxis_orient*left, self.Haxis_orient*right,self.Vaxis_orient*bottom, self.Vaxis_orient*top]
        self.ratio = [left,right,bottom,top]

        #self.myextent=[-self.ycoef*self.myheight*self.ycenter, self.ycoef*self.myheight*(1-self.ycenter),-self.xcoef*self.mywidth*self.xcenter, self.xcoef*self.mywidth*(1-self.xcenter)]
        
        self.sc.axes.imshow(self.images[self.current_image], extent=self.myextent)

        if self.etalonnage["x1"] != 0 or self.etalonnage["x2"] != 0 or self.etalonnage["y1"] != 0 or self.etalonnage["y2"] != 0:
            if self.applyOrient == True:

                self.etalonnage["x1"]*=self.Haxis_orient*self.old_axisParam[1]
                self.etalonnage["x2"]*=self.Haxis_orient*self.old_axisParam[1]
                self.etalonnage["y1"]*=self.Vaxis_orient*self.old_axisParam[0]
                self.etalonnage["y2"]*=self.Vaxis_orient*self.old_axisParam[0]

                
            if self.showEtalon == True:
                self.sc.axes.plot([self.etalonnage["x1"],self.etalonnage["x2"]],[self.etalonnage["y1"],self.etalonnage["y2"]], "ro-")

        for k in range(len(self.x)):
            if self.x[k] != None or self.y[k] != None:
                if self.applyOrient == True:
                    self.x[k]*=self.Haxis_orient*self.old_axisParam[1]
                    self.y[k]*=self.Vaxis_orient*self.old_axisParam[0]
                    self.table_update(k,self.x[k],self.y[k])

        
        if self.etalonnage["done"] == True:
            # labels = [round(float(item.get_text().replace('−','-'))*self.etalonnage["valeurMetres"]/self.etalonnage["valeurPixels"],3)  for item in old_labels]
            list = linspace(-max(abs(left),abs(right)), max(abs(left),abs(right)), 6)
            self.sc.axes.set_xticks(list)
            labels = [round(i*self.etalonnage["valeurMetres"]/self.etalonnage["valeurPixels"],3)  for i in list]
            
            self.sc.axes.set_xticklabels(labels)

            list = linspace(-max(abs(bottom),abs(top)), max(abs(bottom),abs(top)), 6)
            self.sc.axes.set_yticks(list)
            labels = [round(i*self.etalonnage["valeurMetres"]/self.etalonnage["valeurPixels"],3)  for i in list]
            self.sc.axes.set_yticklabels(labels)

        self.sc.axes.set_xlim([self.Haxis_orient*left, self.Haxis_orient*right])
        self.sc.axes.set_ylim([self.Vaxis_orient*bottom, self.Vaxis_orient*top])
        self.applyOrient = False
        self.sc.axes.plot(self.x,self.y,str(self.settings["color"]+self.settings["point"]+self.settings["line"]))

    
        self.sc.axes.grid(self.settings["grid"])
        if self.settings["ticks"] == False :
            self.sc.axes.set_xticklabels([])
            self.sc.axes.set_yticklabels([])

        self.sc.draw_idle()

        self.axis_update()

    # --------------------------------------------------   
    # Mise à jour de l'interface et des évènements
    # --------------------------------------------------  

    def start_measures(self):
        logger.info("Démarrage des mesures")
        if self.etalonnage["done"] == True:
            self.tabWidget.setTabEnabled(1, True);
            self.tabWidget.setCurrentIndex(1)
            self.tableWidget.selectRow(self.current_image)
            self.repere_clicked()
            self.ruler_clicked()
            try:
                self.sc.mpl_disconnect(self.clickEvent)
            except:
                logger.warning("Impossible de déconnecter l'évènement de clic sur canvas. Déjà déconnecté ?!") 
            logger.info("Connexion de l'évènement clic sur canvas avec la fonction measure_event")
            self.clickEvent = self.sc.mpl_connect('button_press_event',self.measure_event)
            self.mesures = True
        else:
            dlg = CustomDialog("Veuillez réaliser l'étalonnage avant de commencer les mesures !")
            if dlg.exec():
                self.repere_clicked()
                print("Success!")
            else:
                self.repere_clicked()
                print("Cancel!")

    def tabbar_clicked(self, index):
        logger.info("Clic sur tab : " + str(index))
        # print("Tab index : "+str(index))
        if index == 0:
            self.mesures = False
            try:
                self.sc.mpl_disconnect(self.clickEvent)
            except:
                logger.warning("Impossible de déconnecter l'évènement de clic sur canvas. Déjà déconnecté ?!") 
            
        elif index == 1:
            self.mesures = True
            self.start_measures()
        

    def play_update(self,value,axes):
        # print(value)
        self.current_image = value
        self.horizontalSlider.setValue(self.current_image+1)
        self.imageLabel.setText('Image : '+str(self.current_image+1)+'/'+str(self.nb_images))
        self.sc.axes=axes
        self.sc.draw_idle()
        self.axis_update()
        #self.canvas_update()

    def slider_update(self,value):
        if self.playStatus == False:
            self.current_image = value-1
            self.canvas_update()

    def icon_from_svg(self,svg_filepath):
        img = QPixmap(svg_filepath)
        qp = QPainter(img)
        qp.setCompositionMode(QPainter.CompositionMode_SourceIn)
        qp.fillRect( img.rect(), self.label_8.palette().color(QPalette.Foreground) )
        qp.end()
        return QIcon(img)


    def save_clicked(self,value):
        logger.info("Clic sur saveButton avec option : " + str(value))
        if value == 0:
            clipboard = 'Temps (s)\tx (m)\ty(m)\r\n'
            for row in range(self.tableWidget.rowCount()):
                rowdata = []
                for column in range(self.tableWidget.columnCount()):
                    item = self.tableWidget.item(row, column)
                    if item is not None:
                        mytext = item.text()
                        mytext = mytext.replace('.',',',1)
                        rowdata.append(mytext)
                    else:
                        rowdata.append('')
                if rowdata != ['','','']:
                    clipboard+=str(rowdata[0])+'\t'+str(rowdata[1])+'\t'+str(rowdata[2])+'\r\n'
            try :
                pccopy(clipboard)
                logger.info("Copie dans le presse-papier réussie !")
            except Exception as ex :
                logger.warning("Une erreur est survenue : " + ex)
        elif value == 1:
            path, ok = QFileDialog.getSaveFileName(
                None, 'Sauvegarder les données', os.getenv('HOME'), 'Fichier CSV (*.csv)')
            if ok:
                columns = range(self.tableWidget.columnCount())
                header = [self.tableWidget.horizontalHeaderItem(column).text()
                        for column in columns]
                suffix = ".csv"
                if ".csv" in path:
                    suffix = ""
                try :
                    with open(path+suffix, 'w') as csvfile:
                        writer = csv.writer(
                            csvfile, dialect='excel', lineterminator='\n')
                        writer.writerow(header)
                        for row in range(self.tableWidget.rowCount()):
                            rowdata = []
                            for column in range(self.tableWidget.columnCount()):
                                item = self.tableWidget.item(row, column)
                                if item is not None:
                                    mytext = item.text()
                                    mytext = mytext.replace('.',',',1)
                                    rowdata.append(mytext)
                                else:
                                    rowdata.append('')
                            if rowdata != ['','','']:
                                writer.writerow(rowdata)
                    logger.info("Écriture du fichier csv terminée avec succès")
                except Exception as ex:
                    logger.warning("Une erreur est survenue : " + ex)
        elif value == 2:
            path, ok = QFileDialog.getSaveFileName(
                None, 'Sauvegarder les données', os.getenv('HOME'), 'Script Python (*.py)')
            if ok:
                newt,newx,newy=[],[],[]
                for row in range(self.tableWidget.rowCount()):
                    try :
                        item = self.tableWidget.item(row, 0).text()
                        newt.append(float(item))
                        item = self.tableWidget.item(row, 1).text()
                        newx.append(float(item))
                        item = self.tableWidget.item(row, 2).text()
                        newy.append(float(item))
                    except :
                        pass

                if self.etalonnage["done"] == True:
                    left = self.ratio[0]*self.etalonnage["valeurMetres"]/self.etalonnage["valeurPixels"]
                    right = self.ratio[1]*self.etalonnage["valeurMetres"]/self.etalonnage["valeurPixels"]
                    bottom = self.ratio[2]*self.etalonnage["valeurMetres"]/self.etalonnage["valeurPixels"]
                    top = self.ratio[3]*self.etalonnage["valeurMetres"]/self.etalonnage["valeurPixels"]
                filecontent ='import matplotlib.pyplot as plt\r\n\r\nt='+str(newt)+'\r\nx='+str(newx)+'\r\ny='+str(newy)+'\r\n\r\nplt.xlim(['+str(left)+','+str(right)+'])\r\nplt.ylim(['+str(bottom)+','+str(top)+'])\r\nplt.plot(x,y,\'o\')\r\nplt.xlabel("x (m)")\r\nplt.ylabel("y (m)")\r\nplt.grid()\r\nplt.show()'
                suffix = ".py"
                if ".py" in path:
                    suffix = ""
                try :
                    with open(path+suffix, 'w') as pyfile:
                        pyfile.write(filecontent)
                    logger.info("Écriture du fichier py terminée avec succès")
                except Exception as ex:
                    logger.warning("Une erreur est survenue : " + ex)
                    
        elif value == 3:
            filePath, _ = QFileDialog.getSaveFileName(self, "Image", "",
                            "PNG(*.png);;JPEG(*.jpg *.jpeg);;All Files(*.*) ")
    
            if filePath == "":
                return
            
            try :
                # Sauvegarde du canvas
                self.sc.print_figure(filePath)
                logger.info("Écriture du fichier png terminée avec succès")
            except Exception as ex:
                logger.warning("Une erreur est survenue : " + ex)

    def infos_clicked(self):
        dlg = CustomDialog(self.version)
        if dlg.exec():
            print("Success!")
        else:
            print("Cancel")
    
    # --------------------------------------------------   
    # Gestion de la fermeture
    # -------------------------------------------------- 

    def closeEvent(self, event):
        dlg = CustomDialog("Voulez-vous vraiment quitter ?")
        if dlg.exec_():
            event.accept() # let the window close
        else:
            event.ignore()

# --------------------------------------------------   
# Classe pour les boîtes de dialogue simples
# -------------------------------------------------- 
class CustomDialog(QDialog):
    def __init__(self, themessage, qrcode=None):
        super().__init__()

        logger.info("Affichage de CustomDialog")

        self.setWindowTitle("Message")
        

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        self.mainlayout = QHBoxLayout()
        self.mainwidget = QWidget()

        message = QLabel(themessage)
        message.setTextFormat(Qt.RichText)
        message.setTextInteractionFlags(Qt.TextSelectableByMouse)
           
        self.mainlayout.addWidget(message)
        self.mainwidget.setLayout(self.mainlayout)
        self.layout.addWidget(self.mainwidget)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


    def stop(self):
        logger.info("Fermeture de CustomDialog")
        self.done(0)

# --------------------------------------------------   
# Classe pour les boîtes de dialogue simples
# -------------------------------------------------- 
class WebDialog(QDialog):
    def __init__(self):
        super().__init__()
        logger.info("Affichage de WebDialog")

        logger.info("Chargement de webserver.ui")
        loadUi(resource_path('assets/ui/webserver.ui'), self)
        self.setWindowTitle("Importation depuis un smartphone")
        
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        address = get_address()

        self.instructions = "<p style=\"font-size: 16px;\"><ul><li>Connecter le périphérique (smartphone, tablette...) sur le même réseau (wifi ou partage de connexion) que l'ordinateur executant ChronoPhys.</li><li>Scanner le QRCode suivant à l'aide du périphérique ou entrer l'adresse suivante dans le navigateur : <b>http://"+address+":8080<b></li><li>Suivre les instructions sur le périphérique.</li></ul><hr>Vous retrouverez les fichiers videos ici : <b>"+str(os.path.join(application_path ,  "videos", ""))+"</b></p>"
        self.message.setText(self.instructions)

        self.message.setTextFormat(Qt.RichText)
        self.message.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.message.setStyleSheet("padding :15px")
      
        self.message.setWordWrap(True)
        pixmap = self.pil2pixmap(self.generate_qr()).scaled(150, 150, Qt.KeepAspectRatio)
        self.label_qr.setPixmap(pixmap) 
        self.label_qr.resize(150,150) 

        self.openFolderButton.clicked.connect(openFolder);
        self.openFolderButton.setIcon(self.icon_from_svg(resource_path("assets/icons/folder-open.svg")))

    def generate_qr(self):
        input_data = "http://"+get_address()+":8080"
        qr = qrcode.QRCode(version=1, box_size=20, border=2)
        qr.add_data(input_data)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        return img

    def pil2pixmap(self, im):
        im2 = im.convert("RGBA")
        data = im2.tobytes("raw", "RGBA")
        qim = QImage(data, im.size[0], im.size[1], QImage.Format_ARGB32)
        pixmap = QPixmap.fromImage(qim)
        return pixmap

    def icon_from_svg(self,svg_filepath):
        img = QPixmap(svg_filepath)
        qp = QPainter(img)
        qp.setCompositionMode(QPainter.CompositionMode_SourceIn)
        qp.fillRect( img.rect(), self.message.palette().color(QPalette.Foreground) )
        qp.end()
        return QIcon(img)

    def stop(self):
        logger.info("Fermeture de WebDialog")
        self.done(0)

# --------------------------------------------------   
# Classe pour la boîte de dialogue d'attente
# -------------------------------------------------- 

class WaitDialog(QDialog):
    def __init__(self):
        super().__init__()
        logger.info("Affichage de WaitDialog")

        self.setWindowTitle("Importation en cours...")
        self.setFixedSize(200, 100)

        self.layout = QVBoxLayout()

        message = QLabel("Importation en cours...")
        message.setAlignment(Qt.AlignCenter)

        spinner = QtWaitingSpinner(self)

        spinner.setRoundness(70.0)
        spinner.setMinimumTrailOpacity(15.0)
        spinner.setTrailFadePercentage(70.0)
        spinner.setNumberOfLines(12)
        spinner.setLineLength(10)
        spinner.setLineWidth(5)
        spinner.setInnerRadius(10)
        spinner.setRevolutionsPerSecond(1)
        spinner.setColor(message.palette().color(QPalette.Foreground))

        verticalSpacer = QSpacerItem(20, 50, QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.layout.addWidget(message)
        self.layout.addItem(verticalSpacer)
        self.layout.addWidget(spinner)
        self.setLayout(self.layout)

        spinner.start()
  

    def start(self):
        self.setWindowModality(Qt.ApplicationModal)
        self.show()
        return True

    def stop(self):
        logger.info("Fermeture de WaitDialog")
        self.done(0)

    def closeEvent(self, evnt):
        evnt.ignore()

# --------------------------------------------------   
# Classe pour la boîte de dialogue d'importation
# -------------------------------------------------- 

class ImportDialog(QDialog):
    def __init__(self,frame,camera_Width,camera_Height ,fps,frame_count,duration):
        super().__init__()
        logger.info("Affichage de ImportDialog")

        self.frame = frame
        self.duration = duration
        self.frame_count = frame_count
        self.camera_Width = camera_Width
        self.camera_Height = camera_Height

        self.newframe_count = self.frame_count
        self.newcamera_Width = self.camera_Width
        self.newcamera_Height = self.camera_Height

        logger.info("Chargement de import.ui")
        loadUi(resource_path('assets/ui/import.ui'), self)
        self.setWindowTitle("Importation d'une vidéo")

        self.right_btn.setIcon(self.icon_from_svg(resource_path("assets/icons/arrow-rotate-right.svg")))
        self.left_btn.setIcon(self.icon_from_svg(resource_path("assets/icons/arrow-rotate-left.svg")))

        self.img = QImage(frame, frame.shape[1], frame.shape[0], frame.shape[1] * 3,QImage.Format_RGB888)
        pixmap = QPixmap(self.img).scaled(200, 200,Qt.KeepAspectRatio, Qt.FastTransformation)
        self.img_label.setPixmap(pixmap)
        self.rotation = 0

        self.left_btn.clicked.connect(lambda : self.rotate(-90));
        self.right_btn.clicked.connect(lambda : self.rotate(90));

        self.largeur_ref.setText(str(camera_Width))
        self.hauteur_ref.setText(str(camera_Height))
        self.images_ref.setText(str(self.frame_count))
        self.duree_ref.setText(str(round(self.duration,2)))
        self.duree_perso.setText(str(round(self.duration,2)))
        self.fps_ref.setText(str(round(fps,2)))
        self.fps_perso.setText(str(round(fps,2)))

        self.onlyInt = QIntValidator()
        self.onlyInt .setLocale(QLocale("en_US"))
        self.largeur_perso.setValidator(self.onlyInt)
        self.hauteur_perso.setValidator(self.onlyInt)
        self.images_perso.setValidator(self.onlyInt)

        self.largeur_perso.setText(str(camera_Width))
        self.hauteur_perso.setText(str(camera_Height))
        self.images_perso.setText(str(self.frame_count))

        self.images_perso.textChanged.connect(self.calculate_fps)
        self.largeur_perso.textChanged.connect(self.largeur_test)
        self.hauteur_perso.textChanged.connect(self.hauteur_test)

        self.btn_apply = self.buttonBox.button(QDialogButtonBox.Ok)

        if self.frame_count >= 150:
            self.images_perso.setStyleSheet("background-color:'#880000';")
            self.newframe_count = 0
        self.check_state()

    def calculate_fps(self, string):
        if string == '' or int(string) > self.frame_count or int(string) > 150:
            self.fps_perso.setText("-")
            self.images_perso.setStyleSheet("background-color:'#880000';")
            self.newframe_count = 0
        else :
            self.fps_perso.setText(str(round(int(string)/self.duration,2)))
            self.images_perso.setStyleSheet("")
            self.newframe_count = int(string)
        self.check_state()

    def largeur_test(self, string):
        if string == '' or int(string) > self.camera_Width:
            self.largeur_perso.setStyleSheet("background-color:'#880000';")
            self.newcamera_Width = 0
        else :
            self.largeur_perso.setStyleSheet("")
            self.newcamera_Width = int(string)
        self.check_state()
    
    def hauteur_test(self, string):
        if string == '' or int(string) > self.camera_Height:
            self.hauteur_perso.setStyleSheet("background-color:'#880000';")
            self.newcamera_Height = 0
        else :
            self.hauteur_perso.setStyleSheet("")
            self.newcamera_Height = int(string)
        self.check_state()

    def check_state(self):
        if self.newcamera_Height != 0 and self.newcamera_Width  != 0 and self.newframe_count != 0:
            self.btn_apply.setEnabled(True)
        else :
            self.btn_apply.setEnabled(False)

    def rotate(self, rot):
        my_transform = QTransform()
        my_transform.rotate(rot)
        self.img = self.img.transformed(my_transform)
        pixmap = QPixmap(self.img).scaled(200, 200,Qt.KeepAspectRatio, Qt.FastTransformation)
        self.img_label.setPixmap(pixmap)
        self.rotation += rot
        if self.rotation == 270:
            self.rotation = -90
        elif self.rotation == 360 or self.rotation == -360:
            self.rotation = 0
        elif self.rotation == -180:
            self.rotation = 180
        elif self.rotation == -270:
            self.rotation = 90

        #print(self.rotation)

    def icon_from_svg(self,svg_filepath):
        img = QPixmap(svg_filepath)
        qp = QPainter(img)
        qp.setCompositionMode(QPainter.CompositionMode_SourceIn)
        qp.fillRect( img.rect(), self.label.palette().color(QPalette.Foreground) )
        qp.end()
        return QIcon(img)

    def GetValue(self):
        logger.info("Envoie des valeurs choisies lors de l'importation")
        if self.newcamera_Height != 0 and self.newcamera_Width  != 0 and self.newframe_count != 0:
            return (self.newcamera_Width,self.newcamera_Height, self.newframe_count, self.rotation    )                                                        

# --------------------------------------------------   
# Classe pour la boîte de dialogue de la webcam
# -------------------------------------------------- 

class WebcamDialog(QDialog):
    def __init__(self):
        super().__init__()
        logger.info("Affichage de WabcamDialog")

        loadUi(resource_path('assets/ui/webcam.ui'), self)
        self.setWindowTitle("Enregistrement d'une vidéo")

        self.btn_apply = self.buttonBox.button(QDialogButtonBox.Ok)
        self.btn_apply.setEnabled(False)     

        img = QPixmap(resource_path("assets/icons/video.svg"))
        qp = QPainter(img)
        qp.setCompositionMode(QPainter.CompositionMode_SourceIn)
        qp.fillRect( img.rect(), QColor(255,255,255))
        qp.end()
        self.capture.setIcon(QIcon(img))
        self.capture.setStyleSheet("font-weight: bold;background-color:'#1b7a46';color:'#fff'")

        self.refreshButton.setIcon(self.icon_from_svg(resource_path("assets/icons/arrow-rotate-right.svg")))
        self.applyButton.setIcon(self.icon_from_svg(resource_path("assets/icons/check.svg")))
        
        self.infos.setText("<p><b>"+str(os.path.join(application_path ,  "videos", ""))+"</b></p>")
        self.infos.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        self.openFolderButton.clicked.connect(openFolder);
        self.openFolderButton.setIcon(self.icon_from_svg(resource_path("assets/icons/folder-open.svg")))

        self.camera_id = None
        self.recordDone = False
        self.firstStart = True
        self.cap = None 
        
        self.refreshButton.clicked.connect(self.refresh)
        self.applyButton.clicked.connect(self.apply)
        self.selectWebcam.activated.connect(self.changeCamera)
        self.refresh()
        
        self.capture.clicked.connect(self.capture_start)

        self.btn_apply = self.buttonBox.button(QDialogButtonBox.Ok)
        self.onlyDouble = QDoubleValidator()
        self.onlyDouble.setLocale(QLocale("en_US"))
        self.heightEdit.setValidator(self.onlyDouble)
        self.widthEdit.setValidator(self.onlyDouble)
        self.expositionEdit.setValidator(self.onlyDouble)

        #self.image_label.setScaledContents(True)

    def refresh(self):
        logger.info("Recherche des ports pour les webcams")
        if self.cap != None and self.firstStart != True:
            release_cap(self.cap)
            self.timer.stop()
            self.cap = None 

        self.selectWebcam.clear()
        camera_ports = list_webcam_ports()
        logger.info("Webcams trouvées aux ports : "+str(camera_ports))
        if len(camera_ports) != 0:
            for i in range(len(camera_ports)):
                self.selectWebcam.addItem("Camera " + str(camera_ports[i]))
                
            
            self.camera_id = camera_ports[0]
            self.capture.setEnabled(True)
        else:
            self.capture.setEnabled(False)

        self.apply()


    def apply(self):
        logger.info("Application des paramètres")
        if self.cap != None and self.firstStart != True:
            release_cap(self.cap)
            self.timer.stop()
            self.cap = None 
            
        self.captureStatus = False    
        self.image = None 
        self.ret = False  
        self.out1 = None 

        self.timer = QTimer(self, interval=5)
        self.timer.timeout.connect(self.update_frame)


        if self.cap is None:
            if self.firstStart:
                logger.info("Première initialisation de la webcam")
                self.cap, self.fps, self.res_width, self.res_height, self.exposition = webcam_init(self.camera_id)
            else:
                logger.info("Initialisation de la webcam avec les paramètres personnalisés")
                self.cap, self.fps, self.res_width, self.res_height, self.exposition = webcam_init(self.camera_id,int(float(self.widthEdit.text())),int(float(self.heightEdit.text())),int(float(self.expositionEdit.text())))
            self.widthEdit.setText(str(self.res_width))
            self.heightEdit.setText(str(self.res_height))
            if sys.platform == "win32":
                logger.info("L'exposition choisies est : " + self.exposition)
                self.expositionEdit.setText(str(self.exposition))
            else:
                self.expositionEdit.setText(str(self.exposition))
            self.timer2 = QTimer(self)
            self.timer2.timeout.connect(self.capture_image)
            self._image_counter = 0
            self.firstStart = False
        logger.info("Démarrage du timer pour le rafraichissement de l'affichage")
        self.timer.start()

    def changeCamera(self):
        release_cap(self.cap)
        self.camera_id = int(self.selectWebcam.currentText().replace('Camera ', ''))
        self.refresh()

    pyqtSlot()
    def update_frame(self):
        if self.cap != None:
            self.ret, self.image = webcam_get_image(self.cap)
            if self.ret:
                self.displayImage(self.image)

    pyqtSlot()
    def capture_start(self):
        if self.captureStatus == True:
            logger.info("Fin de l'enregistrement")
            self.captureStatus = False
            self.capture.setText("Démarrer l'enregistrement")
            self.capture.setStyleSheet("font-weight: bold;background-color:'#1b7a46';color:'#fff'")
            self.btn_apply.setEnabled(True)
            #print("Capture terminée")
            self.end = time.time()

            # Time elapsed
            seconds = self.end - self.start
            logger.info("Temps écoulé : "+str(seconds))

            # Calculate frames per second
            fps  = self._image_counter / seconds
            logger.info("Nombre d'images par seconde estimé : "+str(fps))
            webcam_end_capture(self.out1)
            logger.info("Arrêt du timer pour l'enregistrement")
            self.timer2.stop()
            self.recordDone = True
            self.btn_apply.setEnabled(True)
        else:
            logger.info("Démarrage de l'enregistrement")
            self.captureStatus = True
            self.out1, self.video_path = webcam_init_capture(self.fps, application_path, self.res_width, self.res_height)
            #print("Capture en cours")
            self.capture.setText("Arrêter l'enregistrement")
            self.capture.setStyleSheet("font-weight: bold;background-color:'#880000';color:'#fff'")
            self.btn_apply.setEnabled(False)
            self.start = time.time()
            logger.info("Démarrage du timer pour l'enregistrement")
            self.timer2.start()

    pyqtSlot()
    def capture_image(self):
        if self.captureStatus == True and self.ret == True:
            #QtWidgets.QApplication.beep()
            webcam_write_image(self.out1, self.image)
            self._image_counter += 1

    def displayImage(self, img):
        qformat = QImage.Format_Indexed8
        if len(img.shape)==3 :
            if img.shape[2]==4:
                qformat = QImage.Format_RGBA8888
            else:
                qformat = QImage.Format_RGB888
        outImage = QImage(img, img.shape[1], img.shape[0], img.strides[0], qformat)
        outImage = outImage.rgbSwapped()
        self.image_label.setPixmap(QPixmap.fromImage(outImage).scaled(self.image_label.width(), self.image_label.height(),Qt.KeepAspectRatio, Qt.FastTransformation))

    def release(self):
        release_cap(self.cap)

    def icon_from_svg(self,svg_filepath):
        img = QPixmap(svg_filepath)
        qp = QPainter(img)
        qp.setCompositionMode(QPainter.CompositionMode_SourceIn)
        qp.fillRect( img.rect(), self.infos.palette().color(QPalette.Foreground) )
        qp.end()
        return QIcon(img)


# --------------------------------------------------   
# Classe Worker exécutant la lecture dans un thread
# -------------------------------------------------- 

class Worker(QObject):
    finished = pyqtSignal()
    data = pyqtSignal(int,object)

    def __init__(self, images,x,y, axes,myextent,etalonnage,showEtalon,ratio,settings,current_image, nb_images, parent=None):
        super(Worker, self).__init__(parent)
        logger.info("Démarrage du Worker pour la lecture")

        self.axes = axes
        self.current_number = current_image
        self.nb_images = nb_images
        self.images = images
        self.x = x
        self.y = y
        self.myextent = myextent
        self.etalonnage = etalonnage
        self.left = ratio[0]
        self.right = ratio[1]
        self.bottom = ratio[2]
        self.top = ratio[3]
        self.settings=settings
        self.showEtalon = showEtalon

        self.threadactive=True

    def run(self):

        k = self.current_number
        for i in range(k,self.nb_images):
            self.axes.cla() 
            self.axes.imshow(self.images[i], extent=self.myextent)
            self.axes.plot(self.x,self.y,str(self.settings["color"]+self.settings["point"]+self.settings["line"]))
            if self.showEtalon == True:
                self.axes.plot([self.etalonnage["x1"],self.etalonnage["x2"]],[self.etalonnage["y1"],self.etalonnage["y2"]], "ro-")

            if self.etalonnage["done"] == True:
                list = linspace(-max(abs(self.left),abs(self.right)), max(abs(self.left),abs(self.right)), 6)
                self.axes.set_xticks(list)
                labels = [round(i*self.etalonnage["valeurMetres"]/self.etalonnage["valeurPixels"],3)  for i in list]
                self.axes.set_xticklabels(labels)

                list = linspace(-max(abs(self.bottom),abs(self.top)), max(abs(self.bottom),abs(self.top)), 6)
                self.axes.set_yticks(list)
                labels = [round(i*self.etalonnage["valeurMetres"]/self.etalonnage["valeurPixels"],3)  for i in list]

                self.axes.grid(self.settings["grid"])
                self.axes.get_xaxis().set_visible(self.settings["ticks"])
                self.axes.get_yaxis().set_visible(self.settings["ticks"])

                self.axes.set_yticklabels(labels)

            self.data.emit(i,self.axes)
            sleep(0.3)
            if self.threadactive != True:
                break
        self.threadactive = False
        self.finished.emit()

    def stop(self):
        self.threadactive = False
        self.finished.emit()
        logger.info("Arrêt Worker pour la lecture")


# --------------------------------------------------   
# Classe Worker exécutant la lecture dans un thread
# -------------------------------------------------- 

class ImportWorker(QObject):
    finished = pyqtSignal()
    data = pyqtSignal(list,dict,bool,list)

    def __init__(self, filename, value, parent=None):
        super(ImportWorker, self).__init__(parent)
        self.filename = filename
        self.value = value
        logger.info("Démarrage du Worker pour l'importation de vidéo")

    def run(self):

        self.images, self.videoConfig, error, self.video_timestamp = extract_images(str(self.filename),self.value)

        self.data.emit(self.images, self.videoConfig, error, self.video_timestamp)
        self.finished.emit()

    def stop(self):
        self.finished.emit()
        logger.info("Arrêt du Worker pour l'importation de vidéo")

# --------------------------------------------------   
# Classe WebWorker exécutant le serveur web dans un thread
# -------------------------------------------------- 

class WebWorker(QObject):
    finished = pyqtSignal()
    video = pyqtSignal(str)

    def __init__(self, parent=None):
        super(WebWorker, self).__init__(parent)
        logger.info("Démarrage du Worker pour le serveur web")
        self.threadactive=True

    def run(self):
        try:
            start_server(self)
        except Exception as ex:
            logger.exception("Une erreur est survenue : " + str(ex))
        self.threadactive = False
        self.finished.emit()

    def stop(self):
        self.threadactive = False
        self.finished.emit()
        logger.info("Arrêt du Worker pour le serveur web")

# class WebcamWorker(QObject):
#     finished = pyqtSignal()
#     data = pyqtSignal(str)

#     def __init__(self, parent=None):
#         super(WebcamWorker, self).__init__(parent)

#     def run(self):
#         self.webcam_dlg = WebcamDialog()
#         if self.webcam_dlg.exec():
#             print("Success!")
#             self.webcam_dlg.release()
#             if self.webcam_dlg.recordDone == True:
#                 self.data.emit(self.webcam_dlg.video_path)
#             self.finished.emit()
#         else:
#             print("Cancel!")
#             self.webcam_dlg.release()
#             self.data.emit("")
#             self.finished.emit()

#     def stop(self):
#         self.webcam_dlg.stop()

# --------------------------------------------------   
# Gestion du chemin des ressources pour les executables
# -------------------------------------------------- 
    
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def openFolder():
    logger.info("Ouverture du dossier contenant les vidéos")
    if sys.platform == "win32":
        opener = "explorer"
    elif sys.platform == "darwin":
        opener = "open" 
    else :
        opener = "xdg-open"
    try :
        subprocess.call([opener, os.path.join(application_path ,  "videos", "")])
    except Exception as ex:
        logger.exception("Une erreur est survenue : " + str(ex))

# --------------------------------------------------   
# Execution de l'application
# -------------------------------------------------- 

if __name__ == "__main__":
    logger.info("-------------------------------------------------------------")
    logger.info("Démarrage de l'application")
    logger.info("-------------------------------------------------------------")
    try:
        os.mkdir("./videos")
    except FileExistsError:
        logger.warning("Le dossier videos existe déjà")

    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    ui = Window()
    sys.exit(app.exec_())
