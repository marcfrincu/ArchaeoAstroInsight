# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ArchaeoAstroInsight
                                 A QGIS plugin
 This plugin enables users to perform archaeoastronomy studies by computing the azimuth and horizon altitude indicated by a specific bearing (line).
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-10-30
        git sha              : $Format:%H$
        copyright            : (C) 2021 by Marc Frincu, Stefania Ionescu
        email                : frincu.marc@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .core import DeclinationTool
import os.path

import requests
from qgis.core import QgsProject
from qgis.core import QgsPointXY
from qgis.core import QgsCoordinateReferenceSystem
from qgis.core import QgsCoordinateTransform
from qgis.core import QgsRectangle

from .utility import *
from .dialog import *
from .save_data import *

################################################
# Global parameters                            #
#################################################
QGIS_CRS = "EPSG:3857" #canvas coordinates
TARGET_CRS = "EPSG:4326" #coordinates of your map

DOWNLOAD_MAP = True 
MAP_TYPE = "mt1.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}"


class ArchaeoAstroInsight:
    """QGIS Plugin Implementation."""

    RESULTS_PATH = ''
    R_PATH = ''
    DOWNLOAD_MAP = True
    MAP_TYPE = ''
    LINE_WIDTH = 1
    SCRIPT_SLEEP = ''

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'ArchaeoAstroInsight_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&ArchaeoAstroInsight')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = True

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('ArchaeoAstroInsight', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        tool_icon_path = ':/plugins/a2i/toolbar/icons/bearing.png'
        location_icon_path = ':/plugins/a2i/toolbar/icons/location.png'
        params_icon_path = ':/plugins/a2i/toolbar/icons/settings.png'
        self.add_action(
            params_icon_path,
            text=self.tr(u'A2i settings'),
            callback=self.set_params,
            parent=self.iface.mainWindow())
        self.add_action(
            location_icon_path,
            text=self.tr(u'A2i set location'),
            callback=self.zoom_to_coords,
            parent=self.iface.mainWindow())
        self.add_action(
            tool_icon_path,
            text=self.tr(u'A2i compute land and sky orientation'),
            callback=self.azimuth_tool,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True
        self.run()

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&ArchaeoAstroInsight'),
                action)
            self.iface.removeToolBarIcon(action)


    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        #if self.first_start == True:
        #    self.first_start = False
        #    self.dlg = Ui_Dialog(self.plugin_dir) # plugin_dir was sent as backwards compatibility for the non-plugin version
        # show the dialog
        #self.dlg.show()
        # Run the dialog event loop
        #result = self.dlg.exec_()
        # See if OK was pressed
        #if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
        global config_path 
        config_path = os.path.join(self.plugin_dir, "config.txt")
        global ui_path 
        ui_path = os.path.join(self.plugin_dir, "dialog.ui")
        global save_path 
        save_path = os.path.join(self.plugin_dir, "save_data.ui")

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

        #Deal with map download and type
        if DOWNLOAD_MAP:
            service_url = MAP_TYPE
            service_uri = "type=xyz&zmin=0&zmax=21&url=https://"+requests.utils.quote(service_url)
            #print ("YES!")

            if QgsProject.instance().mapLayersByName("Google Sat"):
                print("Google image is already loaded!")
            else:
                self.iface.addRasterLayer(service_uri, "Google Sat", "wms")

        #Initialize the tool
        global canvas_clicked
        canvas_clicked = DeclinationTool(self.iface.mapCanvas(), self.iface, self.plugin_dir, RESULTS_PATH, R_PATH, SCRIPT_SLEEP, LINE_WIDTH, DOWNLOAD_MAP)

    def zoom_to_coords(self):
        if (self.first_start == True):
            self.first_start = False
            self.run()

        logo_icon_path = ':/plugins/a2i/logo/icons/logo.png'
        qid = QInputDialog()
        qid.setWindowIcon(QtGui.QIcon(logo_icon_path))
        canvas = self.iface.mapCanvas()
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

    def azimuth_tool(self):
        if (self.first_start == True):
            self.first_start = False
            self.run()

        self.iface.mapCanvas().setMapTool( canvas_clicked )

    def rmvLyr(lyrname, self):
        qinst = QgsProject.instance()
        qinst.removeMapLayer(qinst.mapLayersByName(lyrname)[0].id())

    def set_params(self):
        global RESULTS_PATH
        global R_PATH
        global DOWNLOAD_MAP
        global MAP_TYPE
        global LINE_WIDTH
        global SCRIPT_SLEEP

        if (self.first_start == True):
            self.first_start = False
            self.run()

        change = False
        logo_icon_path = ':/plugins/a2i/logo/icons/logo.png'
        ui = Ui_Dialog(self.plugin_dir)
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
            self.iface.addRasterLayer(service_uri, "Google Sat", "wms")