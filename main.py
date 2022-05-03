# ChronoPhys est un logiciel gratuit pour réaliser des exploitations chronophotographiques en Sciences-Physiques
# License Créative Commons : Attribution - Pas d'Utilisation Commerciale - Partage dans les Mêmes Conditions (BY-NC-SA)
# Auteur : Thibault Giauffret, ensciences.fr (2022)
# Version : dev-beta v0.2 (01 mai 2022)

import sys, os, csv

# Gestion de l'interface
from PyQt5.QtCore import (
    QObject,
    pyqtSignal,
    QLocale,
    QRect,
    QPoint,
    QThread,
    Qt,
)
from PyQt5.QtGui import (
    QIcon,
    QDoubleValidator,
    QPixmap,
    QPainter,
    QPen,
    QBrush,
    QImage,
    QColor,
    QPalette
)
from PyQt5.QtWidgets import (
    QMainWindow,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QDialogButtonBox,
    QLabel,
    QApplication,
    QDialog, 
    QLabel,
    QWidget, 
    QTableWidgetItem
)
from PyQt5.uic import loadUi

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
from extract import extract_images


# --------------------------------------------------   
# Classe principale gérant l'application
# -------------------------------------------------- 
class Window(QMainWindow):

    # --------------------------------------------------   
    # Initialisation de la fenêtre
    # --------------------------------------------------  
    def __init__(self):
        super().__init__()

        # Importation de l'interface de base
        loadUi(resource_path('assets/main.ui'), self)
        self.setWindowIcon(QIcon(resource_path('assets/icon.png')))
       
        # Initialisation des variables
        self.mesures = False
        self.t = array([])
        self.x = array([])
        self.y = array([])
        self.images = []
        self.loupe = False
        self.newopen = False
        self.version = "<b>ChronoPhys</b> est un logiciel gratuit pour réaliser des exploitations chronophotographiques en Sciences-Physiques<br><br><b>License Créative Commons</b> : Attribution - Pas d'Utilisation Commerciale - Partage dans les Mêmes Conditions (BY-NC-SA)<br><b>Auteur</b> : Thibault Giauffret, <a href=\"https://ensciences.fr\">ensciences.fr</a>(2022)<hr><b>Version</b> : dev-beta (01 mai 2022)<br><b>Bugs</b> : <a href=\"mailto:contact@ensciences.fr\">contact@ensciences.fr</a>"

        # Ajout du plot au canvas
        figure = Figure()
        self.sc = FigureCanvasQTAgg(figure)
        figure.patch.set_facecolor("None")
        figure.tight_layout()
        self.sc.axes = figure.add_subplot(111)

        # Gestion de la taille du plot
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.sc.setSizePolicy(sizePolicy)

        # Affichage de l'image initiale
        self.sc.setStyleSheet("background-color:transparent;")
        img = matplotlib.image.imread(resource_path('assets/stopwatch.png'))
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
        self.mainWidget.setLayout(layout)
        
        # Mise en arrière plan du canvas
        self.sc.lower()
 
        # Préparation des autres éléments de l'interface (activation, remplacement des libellés, utilisation d'icônes...)
        self.tabWidget.setTabEnabled(1, False);
        self.openButton.clicked.connect(self.video_open);
        self.actionOuvrir_un_fichier_vid_o.triggered.connect(self.video_open)
        self.loupeBox.hide()


        self.playButton.setText('')
        self.playButton.setIcon(self.icon_from_svg(resource_path("assets/play.svg")))
        self.pauseButton.setText('')
        self.pauseButton.setIcon(self.icon_from_svg(resource_path("assets/pause.svg")))
        self.nextButton.setText('')
        self.nextButton.setIcon(self.icon_from_svg(resource_path("assets/forward.svg")))
        self.prevButton.setText('')
        self.prevButton.setIcon(self.icon_from_svg(resource_path("assets/backward.svg")))
        
        img = QPixmap(resource_path("assets/video.svg"))
        qp = QPainter(img)
        qp.setCompositionMode(QPainter.CompositionMode_SourceIn)
        qp.fillRect( img.rect(), QColor(255,255,255))
        qp.end()
        self.openButton.setIcon(QIcon(img))
            

        self.saveButton.setText('')
        self.saveButton.setStyleSheet("font-weight: bold;background-color:'#1b7a46';")
        img = QPixmap(resource_path("assets/floppy-disk.svg"))
        qp = QPainter(img)
        qp.setCompositionMode(QPainter.CompositionMode_SourceIn)
        qp.fillRect( img.rect(), QColor(255,255,255))
        qp.end()
        self.saveButton.setIcon(QIcon(img))
        self.loupeButton.setText('')
        self.loupeButton.setIcon(self.icon_from_svg(resource_path("assets/magnifying-glass.svg")))
        
        self.validateButton.setIcon(self.icon_from_svg(resource_path("assets/circle-check.svg")))
        self.rulerButton.setIcon(self.icon_from_svg(resource_path("assets/ruler-triangle.svg")))
        self.repereButton.setIcon(self.icon_from_svg(resource_path("assets/bullseye-arrow.svg")))
        self.formeButton.setIcon(self.icon_from_svg(resource_path("assets/paintbrush.svg")))
        self.imageLabel.setText('')

        self.axeButton_1.setIcon(self.icon_from_svg(resource_path("assets/axis1.svg")))
        self.axeButton_3.setIcon(self.icon_from_svg(resource_path("assets/axis4.svg")))
        self.axeButton_4.setIcon(self.icon_from_svg(resource_path("assets/axis2.svg")))
        self.axeButton_5.setIcon(self.icon_from_svg(resource_path("assets/axis3.svg")))

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

    # --------------------------------------------------   
    # Complétion de l'interface une fois la video ouverte
    # --------------------------------------------------  

    def ui_update(self):

        self.canvas_resize()

        try:
            self.sc.mpl_disconnect(self.clickEvent)
        except:
            print("An exception occurred") 

        self.label_nombre.setText(str(self.videoConfig["nb_images"]))
        self.label_ips.setText(str(self.videoConfig["fps"]))
        self.label_duree.setText(str(self.videoConfig["duration"]))
        self.label_largeur.setText(str(self.videoConfig["width"]))
        self.label_hauteur.setText(str(self.videoConfig["height"]))
        self.tabWidget.setTabEnabled(2, True)

        self.pixmap = QPixmap(resource_path("assets/ensciences.svg")).scaled(78, 78, Qt.KeepAspectRatio)
        self.label_ensciences.setPixmap(self.pixmap) 
        self.label_ensciences.resize(80,80) 

        self.pixmap = QPixmap(resource_path("assets/icon.svg")).scaled(78, 78, Qt.KeepAspectRatio)
        self.label_chrono.setPixmap(self.pixmap) 
        self.label_chrono.resize(80,80) 

        self.label_infos.setText(self.version)
        self.label_infos.setTextFormat(Qt.RichText)

        self.openButton.setStyleSheet("font-weight: bold;")
        self.openButton.setIcon(self.icon_from_svg(resource_path("assets/video.svg")))

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
        dialog = QFileDialog(self)
        dialog.setNameFilter(str("Video (*.mp4 *.avi *.wmv *mov);;All Files (*.*)"))
        dialog.setDirectory(os.getenv('HOME'))
        if dialog.exec_():
            filename = dialog.selectedFiles()[0]
            # print(filename)
            self.images, self.videoConfig, error = extract_images(str(filename))
            if error == False:
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
                if dlg.exec():
                    print("Success!")
                else:
                    print("Cancel!")

    # --------------------------------------------------   
    # Gestion des contrôles
    # --------------------------------------------------  

    def play(self):
        if self.images != []:
            self.playButton.setEnabled(False);
            self.scrollArea.setEnabled(False);
            self.playStatus = True

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

    def stop(self):
        self.playStatus = False
        self.playButton.setEnabled(True);
        self.scrollArea.setEnabled(True);

    def pause(self):
        try:
            self.worker.stop()
        except:
            print("An exception occurred") 
        

    def next_clicked(self):
        if self.current_image < self.nb_images-1 and self.playStatus == False:
            self.current_image+=1
            self.horizontalSlider.setValue(self.current_image+1)
            self.canvas_update()

    def prev_clicked(self):
        if self.current_image > 0 and self.playStatus == False:
            self.current_image-=1
            self.horizontalSlider.setValue(self.current_image+1)
            self.canvas_update()

    # --------------------------------------------------   
    # Gestion de la loupe
    # --------------------------------------------------  

    def loupe_clicked(self):
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
        self.axis_set = True
        self.applyOrient = True

        self.old_axisParam = self.orient_update(self.axisType)

        self.axisType = value

        try:
            self.sc.mpl_disconnect(self.clickEvent)
        except:
            print("An exception occurred") 
        self.clickEvent = self.sc.mpl_connect('button_press_event',self.axis_event)

    def orient_update(self,value):
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
        self.etalonBox.setEnabled(True)
        try:
            self.sc.mpl_disconnect(self.clickEvent)
        except:
            print("An exception occurred") 
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
            print("An exception occurred") 
        self.clickEvent = self.sc.mpl_connect('button_press_event',self.etalon_event)
        self.validateButton.setStyleSheet("font-weight: bold;color:'#fff'")
        if value == 1:
            self.etalonnage["status"] = "stage1"
            print("Prise du premier point pour l'étalonnage")
        elif value == 2:
            self.etalonnage["status"] = "stage2"
            print("Prise du second point pour l'étalonnage")

    def ruler_clicked(self):
        if self.valeurEtalon.text() != "":
            self.buttonGroup.setExclusive(False)
            self.firstPoint.setChecked(False)
            self.secondPoint.setChecked(False)
            self.buttonGroup.setExclusive(True)

            self.validateButton.setEnabled(True)

            self.styleBox.setEnabled(True)
            self.valeurEtalon.setStyleSheet("")
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
                print("An exception occurred") 
            self.clickEvent = self.sc.mpl_connect('button_press_event',self.measure_event)

            self.etalonBox.setStyleSheet("QGroupBox {\n    border: 2px solid gray;\n    border-color: #FF17365D;\n    margin-top: 27px;\n    font-size: 14px;\n    border-bottom-left-radius: 0px;\n    border-bottom-right-radius: 0px;\n}\n\nQGroupBox::title {\n    subcontrol-origin: margin;\n    subcontrol-position: top center;\n    border-top-left-radius: 0px;\n    border-top-right-radius: 0px;\n    padding: 5px 150px;\n    background-color: #FF17365D;\n    color: rgb(255, 255, 255);\n}")
            self.validateButton.setStyleSheet("font-weight: bold;background-color:'#1b7a46';color:'#fff'")
            img = QPixmap(resource_path("assets/circle-check.svg"))
            qp = QPainter(img)
            qp.setCompositionMode(QPainter.CompositionMode_SourceIn)
            qp.fillRect( img.rect(), QColor(255,255,255))
            qp.end()
            self.validateButton.setIcon(QIcon(img))
            

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
        # Ajout de la valeur de t dans la ligne correspondant à l'image
        self.item = QTableWidgetItem()
        self.item.setText(str(round(i*self.duration/self.nb_images,3)))
        self.tableWidget.setItem(i, 0, self.item)

        # Ajout de la valeur de x dans la ligne correspondant à l'image
        self.item = QTableWidgetItem()
        self.item.setText(str(round(xdata*self.etalonnage["valeurMetres"]/self.etalonnage["valeurPixels"],3)))
        self.tableWidget.setItem(i, 1, self.item)

        # Ajout de la valeur de y dans la ligne correspondant à l'image
        self.item = QTableWidgetItem()
        self.item.setText(str(round(ydata*self.etalonnage["valeurMetres"]/self.etalonnage["valeurPixels"],3)))
        self.tableWidget.setItem(i, 2, self.item)

    def table_clicked(self,item):
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
        except Exception: pass
        self.canvas_update()

    def row_changed(self,item):
        self.current_image = item.row()
        self.horizontalSlider.setValue(self.current_image+1)
        self.canvas_update()


    # --------------------------------------------------   
    # Fonction principale
    # --------------------------------------------------  

    def canvas_update(self):
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
        if self.etalonnage["done"] == True:
            self.tabWidget.setTabEnabled(1, True);
            self.tabWidget.setCurrentIndex(1)
            self.tableWidget.selectRow(self.current_image)
            self.repere_clicked()
            self.ruler_clicked()
            try:
                self.sc.mpl_disconnect(self.clickEvent)
            except:
                print("An exception occurred") 
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
        # print("Tab index : "+str(index))
        if index == 0:
            self.mesures = False
            try:
                self.sc.mpl_disconnect(self.clickEvent)
            except:
                print("An exception occurred") 
            
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
        qp.fillRect( img.rect(), self.label_3.palette().color(QPalette.Foreground) )
        qp.end()
        return QIcon(img)


    def save_clicked(self,value):
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
            pccopy(clipboard)
            print("Copied to clipboard !")
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
                with open(path+suffix, 'w') as pyfile:
                    pyfile.write(filecontent)
        elif value == 3:
            filePath, _ = QFileDialog.getSaveFileName(self, "Image", "",
                            "PNG(*.png);;JPEG(*.jpg *.jpeg);;All Files(*.*) ")
    
            if filePath == "":
                return
            
            # Sauvegarde du canvas
            self.sc.print_figure(filePath)

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
        if dlg.exec():
            event.accept() # let the window close
        else:
            event.ignore()

# --------------------------------------------------   
# Classe pour les boîtes de dialogue simples
# -------------------------------------------------- 
class CustomDialog(QDialog):
    def __init__(self, themessage):
        super().__init__()

        self.setWindowTitle("Message")

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        message = QLabel(themessage)
        message.setTextFormat(Qt.RichText)
        self.layout.addWidget(message)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

# --------------------------------------------------   
# Classe Worker exécutant la lecture dans un thread
# -------------------------------------------------- 

# On crée le thread secondaire
class Worker(QObject):
    finished = pyqtSignal()
    data = pyqtSignal(int,object)

    def __init__(self, images,x,y, axes,myextent,etalonnage,showEtalon,ratio,settings,current_image, nb_images, parent=None):
        super(Worker, self).__init__(parent)

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
        print("Worker stop")

# --------------------------------------------------   
# Gestion du chemin des ressources pour les executables
# -------------------------------------------------- 
    
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# --------------------------------------------------   
# Execution de l'application
# -------------------------------------------------- 

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    ui = Window()
    sys.exit(app.exec_())
