SCRIPT_PATH = "C:\\"
#Archaeo-Astro Insight#

#################################################
# Global parameters                            #
#################################################
QGIS_CRS = "EPSG:3857" #canvas coordinates
TARGET_CRS = "EPSG:4326" #coordinates of your map

RESULTS_PATH =''
R_PATH = ''
LINE_WIDTH = 0.7

SCRIPT_SLEEP = 10

DOWNLOAD_MAP = True 
MAP_TYPE = "mt1.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}"

#################################################
#sys.path.append(SCRIPT_PATH)
from .resources import *
import requests
import time
import subprocess
import csv
import os.path
from os import path
from qgis.gui import QgsMapToolEmitPoint
from qgis.core import QgsProject
from qgis.core import QgsCoordinateReferenceSystem
from qgis.core import QgsCoordinateTransform
from qgis.core import Qgis
from qgis.gui import QgsMapTool
from qgis.core import QgsPoint
from qgis.core import QgsVectorLayer
from qgis.core import QgsFeature
from qgis.core import QgsGeometry

from qgis.PyQt.QtGui import QIcon
from .utility import *
from .dialog import *
from .save_data import *
from pathlib import Path

#Main tool
class DeclinationTool(QgsMapToolEmitPoint):
    def __init__(self, canvas, iface, plugin_dir, resultsPath, RPath, scriptSleep, lineWidth, downloadMap):
        self.pointList = []
        self.transformedPoints = []
        self.code = ""
        self.az = 0
        self.altitude = 0
        self.decl = 0
        self.stars = []
        self.canvas = canvas
        self.iface = iface
        self.scriptPath = plugin_dir
        global RESULTS_PATH 
        RESULTS_PATH = resultsPath
        global R_PATH
        R_PATH = RPath
        global LINE_WIDTH
        LINE_WIDTH = lineWidth
        global SCRIPT_SLEEP
        SCRIPT_SLEEP = scriptSleep
        global DOWNLOAD_MAP
        DOWNLOAD_MAP = downloadMap

        QgsMapToolEmitPoint.__init__(self, self.canvas)

    def canvasPressEvent( self, e ):
        #get point on click
        point = self.toMapCoordinates(self.canvas.mouseLastXY())

        #transform from map CRS to target CRS
        tr = QgsCoordinateTransform(QgsCoordinateReferenceSystem(QGIS_CRS), QgsCoordinateReferenceSystem(TARGET_CRS), QgsProject.instance())
        transformed_point = tr.transform(point)
        
        #append points to respective lists
        self.pointList.append(point)
        self.transformedPoints.append(transformed_point)

        if len(self.transformedPoints) == 1:
            print('Point 1: ({:.4f}, {:.4f})'.format(transformed_point[1], transformed_point[0]))
        else:
            print('Point 2: ({:.4f}, {:.4f})'.format(transformed_point[1], transformed_point[0]))

        #print(point)
        #print(transformed_point)
        if len(self.pointList) == 2:
            self.drawLine()
            self.az = computeAzimuth(self.pointList)
    
    def canvasReleaseEvent( self, e ):
        if len(self.pointList) == 2:
            self.handleRequest()
            self.iface.messageBar().clearWidgets()
            self.iface.messageBar().pushSuccess("Success","[HeyWhatsThat.com] response received")

            if (self.code == ""):
                return
            
            self.iface.messageBar().clearWidgets()
            self.iface.messageBar().pushMessage("Running horizon R script, please wait....", Qgis.Info)
            self.handleScript()
            self.iface.messageBar().clearWidgets()
            self.iface.messageBar().pushSuccess("Success","Horizon R script finished succesfuly")

            self.decl = computeDeclination(self.altitude, self.az, self.transformedPoints)

            self.stars = checkDeclinationBSC5(self.decl, self.scriptPath)
            sunMoon = checkDeclinationSunMoon(self.decl)

            if sunMoon != "None":
                self.stars.append(sunMoon)

            write_to_csv(self, self.scriptPath, self.transformedPoints[0].x(), self.transformedPoints[0].y(), self.az, self.altitude, self.decl, self.stars)

            self.pointList = []
            self.transformedPoints = []
    
    #draw the line and compute azimuth
    def drawLine(self):

        #create layer for the line
        start_point = QgsPoint(self.pointList[0].x(),self.pointList[0].y())
        end_point = QgsPoint(self.pointList[1].x(),self.pointList[1].y())
        line_layer = QgsVectorLayer('LineString?crs=epsg:3857', 'line', 'memory')
        line_layer.setAbstract('Point one ({:.4f},{:.4f}) and point two ({:.4f},{:.4f})'.format(
            self.transformedPoints[0].y(), self.transformedPoints[0].x(), self.transformedPoints[1].y(), self.transformedPoints[1].x()))
        line_layer.renderer().symbol().setWidth(LINE_WIDTH)
        pr = line_layer.dataProvider()
        seg = QgsFeature()
        seg.setGeometry(QgsGeometry.fromPolyline([start_point, end_point]))
        pr.addFeatures([ seg ])
        QgsProject.instance().addMapLayers([line_layer])

            
            #gLine = QgsGeometry.fromPolyline([QgsPoint(self.pointList[0].x(),self.pointList[0].y()), QgsPoint(self.pointList[1].x(),self.pointList[1].y())])
            #self.rubberBand.setToGeometry(gLine, None)
            #print(self.pointList)
    
    #send request for HeyWhatsThat.com code
    def handleRequest(self):
        self.iface.messageBar().pushMessage("Sending HTTP request to [HeyWhatsThat.com]. Please wait for the response.....", Qgis.Info, 2)
        point = QgsPoint(self.transformedPoints[0].x(),self.transformedPoints[0].y())
        #print(point)
        req = "http://heywhatsthat.com/bin/query.cgi?lat={0:.4f}&lon={1:.4f}1&name={2}".format(self.transformedPoints[0].y(), self.transformedPoints[0].x(), "Horizon1")
        print(req) 
        #req_test = "http://heywhatsthat.com/bin/query.cgi?lat=44.297147&lon=69.129591&name={}".format("Horizon1")
        r = requests.get(req)
        #print(r)
        i = 0
        while r.text == "" and i <= 10:
            time.sleep(2)
            r = requests.get(req)
            print("[HeyWhatsThat.com] Waiting for server response, please wait...")
            i += 1
        print("[HeyWhatsThat.com] Horizon profile code is " + r.text.strip("\n"))
        self.code = r.text.strip("\n")
        
     
    #call script and get altitude value   
    def handleScript(self):
        rscript_path = os.path.join(self.scriptPath, "script.R")
        #print(rscript_path)
        #print(R_PATH)
        args = [R_PATH, rscript_path, self.code, str(self.az)]
        result = ''
        #print(args)
        #time.sleep(SCRIPT_SLEEP)

        result = subprocess.run(args, capture_output=True, shell=True)
        i = 1
        while result.returncode != 0 and i <= 10:
            print("Horizon R script running, please wait...")
            time.sleep(SCRIPT_SLEEP)
            result = subprocess.run(args, capture_output=True, shell=True)
            i += 1

        #print(result.stdout)
        
        #print(result)
        #print(float(result))
        print("Altitude is {}".format(float(result.stdout)))
        self.altitude = float(result.stdout)

    def reset(self):
        self.pointList = []
        self.transformedPoints = []
        self.isEmittingPoint = False
        self.rubberBand.reset(True)
        
    def deactivate(self):
        QgsMapTool.deactivate(self)
        self.deactivated.emit()


#Various functions
def write_to_csv(self, scriptPath, xcoord, ycoord, azimuth, altitude, declination, stars):
    global RESULTS_PATH
    if stars:
        starsString = ', '.join(stars)
    else:
        starsString = ''

    data = []
    data.append(ycoord)
    data.append(xcoord)
    data.append(azimuth)
    data.append(altitude)
    data.append(declination)
    data.append(starsString)

    if (starsString == ''):
        starsString = 'None'

    messageString = "The bearing of the line is: Az: " + str(azimuth) + " Alt: " + str(altitude) + " Declination: " + str(declination) + " pointing to: " + starsString 
    print(messageString)
    self.iface.messageBar().pushMessage("Result", messageString, Qgis.Info)

    if RESULTS_PATH == "Empty":
        RESULTS_PATH = os.getcwd()

    save = Ui_Save(data, RESULTS_PATH, os.path.join(scriptPath, "save_data.ui"))
    save.setWindowIcon(QtGui.QIcon(':/plugins/a2i/logo/icons/logo.png'))
    save.exec()
    
def zoom_to_coords():
    qid = QInputDialog()
    qid.setWindowIcon(QtGui.QIcon(logo_icon_path))
    canvas = iface.mapCanvas()
    input, ok = QInputDialog.getText( qid, "Enter Coordinates", "Enter New Coordinates as 'x.xxx, y.yyy'", QLineEdit.Normal, "lat" + "," + "long")
    if ok:
        y = input.split( "," )[ 0 ]
        #print (y)
        x = input.split( "," )[ 1 ]
        #print (x)
        while (y == "lat" or x == "long") and ok:
            input, ok = QInputDialog.getText( qid, "Enter Coordinates", "Enter New Coordinates as 'x.xxx,y.yyy'", QLineEdit.Normal, "lat" + "," + "long")
            if ok:
                y = input.split( "," )[ 0 ]
                x = input.split( "," )[ 1 ]
        if ok:
            point = QgsPointXY(float(x), float(y))
            tr = QgsCoordinateTransform(QgsCoordinateReferenceSystem(QGIS_CRS), QgsCoordinateReferenceSystem(TARGET_CRS), QgsProject.instance())
            transformed_point = tr.transform(point, QgsCoordinateTransform.ReverseTransform)
            x = transformed_point.x()
            y = transformed_point.y()
            if not x:
                print ("x value is missing!")
            if not y:
                print ("y value is missing!")
            scale=200
            #print(x)
            #print(y)
            rect = QgsRectangle(x-scale,y-scale,x+scale,y+scale)
            canvas.setExtent(rect)
            canvas.refresh()

def azimuth_tool():
    iface.mapCanvas().setMapTool( canvas_clicked )

def rmvLyr(lyrname):
    qinst = QgsProject.instance()
    qinst.removeMapLayer(qinst.mapLayersByName(lyrname)[0].id())

def set_params():

    change = False

    ui = Ui_Dialog(SCRIPT_PATH)
    ui.setWindowIcon(QtGui.QIcon(logo_icon_path))
    ui.exec()

    with open(config_path, 'r') as f:
        #SCRIPT_PATH = f.readline().rstrip("\n")
        f.readline()
        RESULTS_PATH = f.readline().rstrip("\n")
        R_PATH = f.readline().rstrip("\n")

        if f.readline().rstrip("\n") == "Yes":
            DOWNLOAD_MAP = True
            mapType = f.readline().rstrip("\n")
            
            if mapType == "Roadmap":
                if MAP_TYPE != "mt1.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}":
                    change = True
                MAP_TYPE = "mt1.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}"
            elif mapType == "Terrain":
                if MAP_TYPE != "mt1.google.com/vt/lyrs=p&hl=en&x={x}&y={y}&z={z}":
                    change = True
                MAP_TYPE = "mt1.google.com/vt/lyrs=p&hl=en&x={x}&y={y}&z={z}"
            elif mapType == "Satellite":
                if MAP_TYPE != "mt1.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}":
                    change = True
                MAP_TYPE = "mt1.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}"
            elif mapType == "Hybrid":
                if MAP_TYPE != "mt1.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}":
                    change = True
                MAP_TYPE = "mt1.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}"
            else:
                DOWNLOAD_MAP = False
                f.readline()

        LINE_WIDTH = float(f.readline().rstrip("\n"))
        SCRIPT_SLEEP = float(f.readline().rstrip("\n"))

    if change:
        rmvLyr("Google Sat")
        service_url = MAP_TYPE
        service_uri = "type=xyz&zmin=0&zmax=21&url=https://"+requests.utils.quote(service_url)
        iface.addRasterLayer(service_uri, "Google Sat", "wms")


#'Main' code, executed first when you run the script
def initA2i(scriptPath, iface):
    #Print empty line between console ouputs
    print('\n')
    SCRIPT_PATH = scriptPath

    #Set paths to useful files
    config_path = os.path.join(SCRIPT_PATH, "config.txt")
    ui_path = os.path.join(SCRIPT_PATH, "dialog.ui")
    save_path = os.path.join(SCRIPT_PATH, "save_data.ui")
    tool_icon_path = ':/plugins/a2i/toolbar/icons/bearing.png'
    location_icon_path = ':/plugins/a2i/toolbar/icons/location.png'
    params_icon_path = ':/plugins/a2i/toolbar/icons/settings.png'
    logo_icon_path = ':/plugins/a2i/logo/icons/logo.png'

    #Read config file
    with open(config_path, 'r') as f:
        #SCRIPT_PATH = f.readline().rstrip("\n")
        f.readline()
        RESULTS_PATH = f.readline().rstrip("\n")
        R_PATH = f.readline().rstrip("\n")

        if f.readline().rstrip("\n") == "Yes":
            DOWNLOAD_MAP = True
            mapType = f.readline().rstrip("\n")
            if mapType == "Roadmap":
                MAP_TYPE = "mt1.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}"
            elif mapType == "Terrain":
                MAP_TYPE = "mt1.google.com/vt/lyrs=p&hl=en&x={x}&y={y}&z={z}"
            elif mapType == "Satellite":
                MAP_TYPE = "mt1.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}"
            elif mapType == "Hybrid":
                MAP_TYPE = "mt1.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}"
            else:
                DOWNLOAD_MAP = False
                f.readline()

        LINE_WIDTH = float(f.readline().rstrip("\n"))
        SCRIPT_SLEEP = float(f.readline().rstrip("\n"))

    #Set the first too as the pan tool
    iface.actionPan().trigger()

    #Deal with map download and type
    if DOWNLOAD_MAP:
        service_url = MAP_TYPE
        service_uri = "type=xyz&zmin=0&zmax=21&url=https://"+requests.utils.quote(service_url)
        #print ("YES!")

        if QgsProject.instance().mapLayersByName("Google Sat"):
            print("Google image is already loaded!")
        else:
            iface.addRasterLayer(service_uri, "Google Sat", "wms")

    #Initialize the tool
    canvas_clicked = DeclinationTool(iface.mapCanvas(), iface)

    #Set the buttons on the toolbar
    action_tool = QAction(QIcon(tool_icon_path), 'Start Tool')
    action_tool.triggered.connect(azimuth_tool)
    iface.addToolBarIcon(action_tool)

    action_zoom = QAction(QIcon(location_icon_path), 'Go to Coords')
    action_zoom.triggered.connect(zoom_to_coords)
    iface.addToolBarIcon(action_zoom)

    set_parameters = QAction(QIcon(params_icon_path), 'Set Params')
    set_parameters.triggered.connect(set_params)
    iface.addToolBarIcon(set_parameters)

    print ('OK')



	  	