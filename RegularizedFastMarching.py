import os
# import unittest
import logging
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

from Resources.Segmentation import *
from Resources.Regularization import *

import numpy as np
import os.path
import time
from csv import reader

#
# RegularizedFastMarching
#
class RegularizedFastMarching(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Regularized Fast Marching"  # TODO: make this more human readable by adding spaces
        self.parent.categories = ["Segmentation"]  # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["Aldrick FAURE (IMT)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        self.parent.helpText = """
    This module performs a regularized fast marching on volumes.
    Seeds can be set manually or from file 
    Seeds label can be set from csv file 
    """
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = """
    This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
    and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
    """

        # Additional initialization step after application startup is complete
        slicer.app.connect("startupCompleted()", registerSampleData)

def getSegmentationFileName(seedsFile, distance, gamma, marginMask, regularizationDiameter):
    segmentationFile = seedsFile.replace(".", "")
    segmentationFile += "_" + str(distance)
    segmentationFile += "_" + str(gamma).replace(".", "")
    segmentationFile += "_" + str(marginMask) 
    segmentationFile += "_" + str(regularizationDiameter) + ".seg.nrrd"
    return segmentationFile

#
# Register sample data sets in Sample Data module
#
def registerSampleData():
  """
  Add data sets to Sample Data module.
  """
  # It is always recommended to provide sample data for users to make it easy to try the module,
  # but if no sample data is available then this method (and associated startupCompeted signal connection) can be removed.

  import SampleData
  iconsPath = os.path.join(os.path.dirname(__file__), 'Resources/Icons')

  # To ensure that the source code repository remains small (can be downloaded and installed quickly)
  # it is recommended to store data sets that are larger than a few MB in a Github release.

  # RegularizedFastMarching1
  SampleData.SampleDataLogic.registerCustomSampleDataSource(
    # Category and sample name displayed in Sample Data module
    category='RegularizedFastMarching',
    sampleName='RegularizedFastMarching1',
    # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
    # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
    thumbnailFileName=os.path.join(iconsPath, 'RegularizedFastMarching1.png'),
    # Download URL and target file name
    uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
    fileNames='RegularizedFastMarching1.nrrd',
    # Checksum to ensure file integrity. Can be computed by this command:
    #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
    checksums = 'SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95',
    # This node name will be used when the data set is loaded
    nodeNames='RegularizedFastMarching1'
  )

  # RegularizedFastMarching2
  SampleData.SampleDataLogic.registerCustomSampleDataSource(
    # Category and sample name displayed in Sample Data module
    category='RegularizedFastMarching',
    sampleName='RegularizedFastMarching2',
    thumbnailFileName=os.path.join(iconsPath, 'RegularizedFastMarching2.png'),
    # Download URL and target file name
    uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
    fileNames='RegularizedFastMarching2.nrrd',
    checksums = 'SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97',
    # This node name will be used when the data set is loaded
    nodeNames='RegularizedFastMarching2'
  )

#
# RegularizedFastMarchingWidget
#

class RegularizedFastMarchingWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None):
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._updatingGUIFromParameterNode = False
    

    def fillComboBox(self, combobox, path, extension):
        """
        Fill this combobox with the path's files ending with this extension
        Inputs:
            * combobox : the combobox to fill
            * path : folder path containing the files with correct extension
            * extension : the desired file's extension
        Outputs:
            * combobox : the combobox filled 
        """
        files = []
        for file in os.listdir(path):
            if file.endswith(extension):
                files.append(file)
        files = np.sort(np.array(files))
        for file in files: 
            combobox.addItem(file)
        return combobox

    def setup(self):
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        ScriptedLoadableModuleWidget.setup(self)

        globalPath, _ = os.path.split( os.path.splitext( slicer.modules.regularizedfastmarching.path )[0] )
        self.globalPath = globalPath + "/Resources/SegmentationFastMarching/"
        self.volumesPath = self.globalPath + "Volumes/"
        self.seedsCsvPath = self.globalPath + "SeedsLabels/"
        self.seedsPath = self.globalPath + "Seeds/"
        self.regularizationsPath = self.globalPath + "Regularizations/"
        self.segmentationsPath = self.globalPath + "Segmentations/"

        self.logic = RegularizedFastMarchingLogic()
        # self.logic.previousVolumeName = None
        # self.logic.imgLabel = np.array([])
        # self.logic.previousImgIds = np.array([])
        # self.logic.imgIds = np.array([])
        # self.logic.imgDist = np.array([])

        # Hide the Slicer Logo to increase space
        slicer.util.findChild(slicer.util.mainWindow(), 'LogoLabel').visible = False
        
        #
        #region Restart Slicer Area
        #
        parametersCollapsibleButton = ctk.ctkCollapsibleButton()
        parametersCollapsibleButton.text = "Reload"
        self.layout.addWidget(parametersCollapsibleButton)
        parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)
        self.restartSlicerButton = qt.QPushButton("Restart Slicer")
        self.restartSlicerButton.connect('clicked(bool)', slicer.util.restart)
        parametersFormLayout.addRow(self.restartSlicerButton)
        #endregion 

        #
        #region Load Data Area
        #
        parametersCollapsibleButton = ctk.ctkCollapsibleButton()
        parametersCollapsibleButton.text = "Seeds"
        self.layout.addWidget(parametersCollapsibleButton)
        parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)
        
        #
        # File name volume .nii
        # 
        # self.volueNameComboBox = qt.QComboBox()     
        # self.volueNameComboBox = self.fillComboBox(self.volueNameComboBox, self.volumesPath, ".nii")
        # parametersFormLayout.addRow("Volumes .nii : ", self.volueNameComboBox)
    
        #
        # Load volume buttons
        #
        # horizontalLayout = qt.QHBoxLayout()
        # self.loadBrainVolumeButton = qt.QPushButton("Load Example Volume")
        # self.loadBrainVolumeButton.enabled = True
        # horizontalLayout.addWidget(self.loadBrainVolumeButton)
        
        #
        # Load custom volumes buttons
        #
        # self.loadCustomVolumeButton = qt.QPushButton("Load Selected Volume")
        # self.loadCustomVolumeButton.enabled = True
        # horizontalLayout.addWidget(self.loadCustomVolumeButton)       
        # parametersFormLayout.addRow(horizontalLayout)
    
        
        #
        # Add vertical spacing
        # 
        # verticalSpacer = qt.QSpacerItem(0, 20, qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
        # parametersFormLayout.addItem(verticalSpacer)
        
        #
        # Seeds files and a text line to load / save seeds from the scene
        #
        horizontalLayout = qt.QHBoxLayout()
        fileNameSeedsLabel = qt.QLabel("Seeds : ")
        self.fileNameSeedsComboBox = qt.QComboBox() 
        self.fileNameSeedsComboBox = self.fillComboBox(self.fileNameSeedsComboBox, self.seedsPath, ".seed")   
        self.fileNameSeedsLineEdit = qt.QLineEdit()
        horizontalLayout.addWidget(fileNameSeedsLabel)
        horizontalLayout.addWidget(self.fileNameSeedsComboBox)
        horizontalLayout.addWidget(self.fileNameSeedsLineEdit)
        self.fileNameSeedsComboBox.currentTextChanged.connect(self.setSelectedSeedsFile)
        self.setSelectedSeedsFile(self.fileNameSeedsComboBox.currentText)
        parametersFormLayout.addRow(horizontalLayout)
          
        #
        # Add vertical spacing
        # 
        verticalSpacer = qt.QSpacerItem(0, 20, qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
        parametersFormLayout.addItem(verticalSpacer)
             
        #
        # Save markers Button
        #
        horizontalLayout = qt.QHBoxLayout()
        self.saveMarkersButton = qt.QPushButton("Save markers")
        self.saveMarkersButton.toolTip = "Save the markers in a fcsv file"
        self.saveMarkersButton.enabled = True
        horizontalLayout.addWidget(self.saveMarkersButton)
    
        #
        # Load markers Button
        #
        self.loadMarkersButton = qt.QPushButton("Load markers")
        self.loadMarkersButton.toolTip = "Load the markers from fcsv file."
        self.loadMarkersButton.enabled = True
        horizontalLayout.addWidget(self.loadMarkersButton)      
    
        #
        # Clear markups Button
        #
        self.clearButton = qt.QPushButton("Clear all markups")
        self.clearButton.toolTip = "Remove all fiducial markers."
        self.clearButton.enabled = True
        horizontalLayout.addWidget(self.clearButton)
        parametersFormLayout.addRow(horizontalLayout)
        
        #
        # Add vertical spacing
        # 
        verticalSpacer = qt.QSpacerItem(0, 25, qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
        parametersFormLayout.addItem(verticalSpacer)
    
        #
        # Fiducial placement button
        #
        """
            Add this markup in the markupsList and rename it depending on seeds combobox's value
        """
        @vtk.calldata_type(vtk.VTK_INT)
        def onMarkupAdded(caller, event, index):    
            markupsNode = caller
            # Label, Name
            seedTokens = self.currentSeedNameComboBox.currentText.replace(" ", "").split(":")
            markupsNode.SetNthFiducialLabel(index, seedTokens[1])
            markupsNode.SetNthControlPointDescription(index, seedTokens[0])
    
        self.w=slicer.qSlicerMarkupsPlaceWidget()
        self.w.setMRMLScene(slicer.mrmlScene)
    
        markupsNode = slicer.mrmlScene.GetFirstNodeByName("MarkupsFiducial")
        if markupsNode == None:    
            markupsNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")
            markupsNode.CreateDefaultDisplayNodes()
            
        # On markuk added event : format the added markup
        markupsNode.AddObserver(slicer.vtkMRMLMarkupsNode.PointPositionDefinedEvent, onMarkupAdded)
        self.w.setCurrentNode(markupsNode)
        # Hide all buttons and only show place button
        self.w.buttonsVisible=True
        self.w.placeButton().show()
        self.w.show()
        parametersFormLayout.addRow(self.w)
        
        #
        # Add vertical spacing
        # 
        verticalSpacer = qt.QSpacerItem(0, 20, qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
        parametersFormLayout.addItem(verticalSpacer)
    
        #
        # File name data's seeds
        # 
        self.fileNameDataComboBox = qt.QComboBox() 
        self.fileNameDataComboBox = self.fillComboBox(self.fileNameDataComboBox, self.seedsCsvPath, ".csv")   
        self.fileNameDataComboBox.currentTextChanged.connect(self.setSeedsLabelFromFile)
        parametersFormLayout.addRow("Seeds labels csv: ", self.fileNameDataComboBox)

        #
        # Add vertical spacing
        # 
        verticalSpacer = qt.QSpacerItem(0, 30, qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
        parametersFormLayout.addItem(verticalSpacer)
    
        horizontalLayout = qt.QHBoxLayout()
        # Seeds label 
        self.seedsLabelText = qt.QLabel()
        self.seedsLabelText.text = "Labels :"
        horizontalLayout.addWidget(self.seedsLabelText)
        
        # ComboxBox containing names and labels
        self.currentSeedNameComboBox= qt.QComboBox()
        
        # Add labels depending on first csv file found
        self.setSeedsLabelFromFile(self.fileNameDataComboBox.currentText)
        horizontalLayout.addWidget(self.currentSeedNameComboBox)
        
        self.clearOrganButton = qt.QPushButton("Clear this organ")
        self.clearOrganButton.toolTip = "Remove all fiducial markers for this organ."
        self.clearOrganButton.enabled = True
        horizontalLayout.addWidget(self.clearOrganButton)
        parametersFormLayout.addRow(horizontalLayout)
    
        #endregion


        #
        #region Segmentation Parameters Area
        #
        parametersCollapsibleButton = ctk.ctkCollapsibleButton()
        parametersCollapsibleButton.text = "Parameters"
        self.layout.addWidget(parametersCollapsibleButton)
        parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

        #
        # input volume selector
        #
        self.inputSelector = slicer.qMRMLNodeComboBox()
        self.inputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.inputSelector.selectNodeUponCreation = True
        self.inputSelector.addEnabled = False
        self.inputSelector.removeEnabled = False
        self.inputSelector.noneEnabled = False
        self.inputSelector.showHidden = False
        self.inputSelector.showChildNodeTypes = False
        self.inputSelector.setMRMLScene( slicer.mrmlScene )
        self.inputSelector.setToolTip( "Pick the input to the algorithm." )
        parametersFormLayout.addRow("Input Volume : ", self.inputSelector)

        #
        # Add vertical spacing
        # 
        verticalSpacer = qt.QSpacerItem(0, 30, qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
        parametersFormLayout.addItem(verticalSpacer)
        
        #
        # Segmentation distance to stop the algo
        #
        self.distance = ctk.ctkSliderWidget()
        self.distance.singleStep = 10
        self.distance.minimum = 0
        self.distance.maximum = 1000
        self.distance.value = 100
        self.distance.setToolTip("Set the maximum geodesic distance allowed from a seed")
        parametersFormLayout.addRow("Distance", self.distance)
        
        #
        # Margin to build masks
        #
        self.marginMask = ctk.ctkSliderWidget()
        self.marginMask.singleStep = 1
        self.marginMask.minimum = 0
        self.marginMask.maximum = 50
        self.marginMask.value = 15
        self.marginMask.setToolTip("Margin used to build masks for each seed")
        parametersFormLayout.addRow("Mask Margin (voxel)", self.marginMask)

        #
        # Gamma to prevent the seeds to cross bridges between organs
        #
        self.gammaSlider = qt.QSlider(qt.Qt.Horizontal)
        self.gammaSlider.setRange(0, 1000)
        self.gammaSlider.setSingleStep(1)
        self.gammaSlider.setPageStep(10)
        self.gammaSlider.setValue(25)

        self.gammaSpinBox = qt.QDoubleSpinBox()
        self.gammaSpinBox.setDecimals(3)
        self.gammaSpinBox.setRange(0, 1)
        self.gammaSpinBox.setSingleStep(0.001)
        self.gammaSpinBox.setValue(0.025)

        self.gammaSlider.valueChanged.connect(self.setGammaValueFromSlider)
        self.gammaSpinBox.valueChanged.connect(self.setGammaValueFromSpinBox)
        
        horizontalLayout = qt.QHBoxLayout()
        horizontalLayout.addWidget(self.gammaSlider)
        horizontalLayout.addWidget(self.gammaSpinBox)

        parametersFormLayout.addRow("Regularization weight", horizontalLayout)
        
        #
        # Regularization radius
        #
        self.regularizationDiameter = ctk.ctkSliderWidget()
        self.regularizationDiameter.singleStep = 1
        self.regularizationDiameter.minimum = 1
        self.regularizationDiameter.maximum = 20
        self.regularizationDiameter.value = 4
        self.regularizationDiameter.setToolTip("Margin used to build masks for each seed")
        parametersFormLayout.addRow("Regularization Diameter (voxels)", self.regularizationDiameter)
        
        #
        # Threshold to prevent the seeds to spread over a range intensities
        #
        self.minThresholdSlider = ctk.ctkSliderWidget()
        self.minThresholdSlider.singleStep = 1
        self.minThresholdSlider.minimum = 0
        self.minThresholdSlider.maximum = 255
        self.minThresholdSlider.value = 40
        self.minThresholdSlider.setToolTip("Seeds cannot spread below this value")
        self.minThresholdSlider.valueChanged.connect(self.setMinThresholdValue)
        parametersFormLayout.addRow("Min Threshold (digital level)", self.minThresholdSlider)

        self.maxThresholdSlider = ctk.ctkSliderWidget()
        self.maxThresholdSlider.singleStep = 1
        self.maxThresholdSlider.minimum = 0
        self.maxThresholdSlider.maximum = 255
        self.maxThresholdSlider.value = 255
        self.maxThresholdSlider.setToolTip("Seeds cannot spread over this value")
        self.maxThresholdSlider.valueChanged.connect(self.setMaxThresholdValue)
        parametersFormLayout.addRow("Max Threshold (digital level)", self.maxThresholdSlider)

        #
        # Add vertical spacing
        # 
        verticalSpacer = qt.QSpacerItem(0, 30, qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
        parametersFormLayout.addItem(verticalSpacer)
        
        #
        # Check box to keep or not last segmentation
        #
        self.removeLastSegmentationCheckBox = qt.QCheckBox("")
        self.removeLastSegmentationCheckBox.setChecked(True)
        parametersFormLayout.addRow("Remove last segmentation", self.removeLastSegmentationCheckBox)
        
        #
        # Show the background seed of the next segmentation
        #
        self.showBackGroundCheckBox = qt.QCheckBox("")
        self.showBackGroundCheckBox.setChecked(False)
        parametersFormLayout.addRow("Show background", self.showBackGroundCheckBox)
        
        #
        # Add vertical spacing
        # 
        verticalSpacer = qt.QSpacerItem(0, 30, qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
        parametersFormLayout.addItem(verticalSpacer)
        
        #
        # Segment Button
        #
        self.segmentButton = qt.QPushButton("Segment")
        self.segmentButton.toolTip = "Run the algorithm."
        self.segmentButton.enabled = False
        parametersFormLayout.addRow(self.segmentButton)
        #endregion 

        #
        #region Load Save segmentations
        #
        parametersCollapsibleButton = ctk.ctkCollapsibleButton()
        parametersCollapsibleButton.text = "Segmentations"
        self.layout.addWidget(parametersCollapsibleButton)
        parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

        #
        # Checkbox to save the segmentation using the labels   
        #
        self.saveByLabelsCheckBox = qt.QCheckBox("")
        self.saveByLabelsCheckBox.setChecked(True)
        parametersFormLayout.addRow("Save by labels", self.saveByLabelsCheckBox)

        #
        # Checkbox to save the segmentation using the voxels intensities   
        #
        self.saveByIntensitiesCheckBox = qt.QCheckBox("")
        self.saveByIntensitiesCheckBox.setChecked(False)
        parametersFormLayout.addRow("Save by intensities", self.saveByIntensitiesCheckBox)

        #
        # Checkbox to generate segments data   
        #
        self.generateDataCsvCheckBox = qt.QCheckBox("")
        self.generateDataCsvCheckBox.enabled = False
        self.generateDataCsvCheckBox.setChecked(False)
        parametersFormLayout.addRow("Generate segments data CSV", self.generateDataCsvCheckBox)


        #
        # Name of the segmentation to save
        #
        self.saveSegmentationName = qt.QLineEdit()
        self.saveSegmentationName.textChanged.connect(self.onSaveSegmentationFileChange)
        parametersFormLayout.addRow("Segmentation name :", self.saveSegmentationName) 

        #
        # Save segmentationButton Button
        #
        self.saveSegmentationButton = qt.QPushButton("Save segmentation")
        self.saveSegmentationButton.toolTip = "Save this segmentation with used parameters."
        parametersFormLayout.addRow(self.saveSegmentationButton)   

        #
        # Add vertical spacing
        # 
        verticalSpacer = qt.QSpacerItem(0, 30, qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
        parametersFormLayout.addItem(verticalSpacer)

        horizontalLayout = qt.QHBoxLayout()
        self.segmentationLoadLabelText = qt.QLabel()
        self.segmentationLoadLabelText.text = "Segmentation files :"
        horizontalLayout.addWidget(self.segmentationLoadLabelText)
        
        #
        # Segmentation files 
        # 
        self.segmentationFilesComboBox = qt.QComboBox() 
        self.segmentationFilesComboBox = self.fillComboBox(self.segmentationFilesComboBox, self.segmentationsPath, ".seg.nrrd")
        horizontalLayout.addWidget(self.segmentationFilesComboBox)
        parametersFormLayout.addRow(horizontalLayout)
    
        #
        # Load segmentationButton Button
        #
        self.loadSegmentationButton = qt.QPushButton("Load segmentation")
        self.loadSegmentationButton.toolTip = "Load the segmenation from this file."
        parametersFormLayout.addRow(self.loadSegmentationButton)   
        #end region
        

        #
        #region Connections & Shortcuts
        #
        # self.loadBrainVolumeButton.connect('clicked(bool)', self.onLoadBrainVolumeButton)
        # self.loadCustomVolumeButton.connect('clicked(bool)', self.onLoadCustomVolumeButton)
        
        self.clearButton.connect('clicked(bool)', self.onClearButton)
        self.clearOrganButton.connect('clicked(bool)', self.onClearOrganButton)
        self.segmentButton.connect('clicked(bool)', self.onSegmentButton)
        self.saveByIntensitiesCheckBox.connect('stateChanged(int)', self.onSaveByIntensitiesCheckBox)
        self.saveSegmentationButton.connect('clicked(bool)', self.onSaveSegmentationButton)
        self.loadSegmentationButton.connect('clicked(bool)', self.onLoadSegmentationButton)
        self.saveMarkersButton.connect('clicked(bool)', self.onSaveMarkersButton)
        self.loadMarkersButton.connect('clicked(bool)', self.onLoadMarkersButton)
        self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    
        # Keyboard shortcut bind : press ctrl button to add markup        
        markupShortcut = qt.QShortcut(slicer.util.mainWindow())
        markupShortcut.setKey( qt.QKeySequence("w") )
        markupShortcut.connect('activated()', self.addMarkupcallback)
        
        markupShortcut = qt.QShortcut(slicer.util.mainWindow())
        markupShortcut.setKey( qt.QKeySequence("x") )
        markupShortcut.connect('activated()', self.addBgMarkupcallback)
        #endregion 

        # Refresh Apply button state
        self.onSelect()
        
        # Refresh segmentation save button state
        self.onSaveSegmentationFileChange()

    #region On event functions
    def cleanup(self):
        pass
    

    def onSelect(self):
        self.segmentButton.enabled = self.inputSelector.currentNode()
        if self.segmentButton.enabled:
            self.setMaxThresholdMaximumByVolume(self.inputSelector.currentNode())
            self.setMinThresholdMaximumByVolume(self.inputSelector.currentNode())
    
    def setMaxThresholdMaximumByVolume(self, volume):
        voxels = slicer.util.arrayFromVolume(volume)
        maxIntensity = np.amax(voxels)
        self.maxThresholdSlider.maximum = maxIntensity
        self.minThresholdSlider.maximum = maxIntensity

    def setMinThresholdMaximumByVolume(self, volume):
        voxels = slicer.util.arrayFromVolume(volume)
        minIntensity = np.amin(voxels)
        self.maxThresholdSlider.minimum = minIntensity
        self.minThresholdSlider.minimum = minIntensity

    # def onLoadBrainVolumeButton(self) : 
    #     """
    #     Load the brain volume from SampleData's module
    #     """
    #     import SampleData
    #     SampleData.downloadFromURL(
    #         nodeNames='BrainTumor',
    #         fileNames='RegLib_C01_1.nrrd',
    #         uris='http://slicer.kitware.com/midas3/download/item/292312/RegLib_C01_1.nrrd')
    #     volumeNode = slicer.util.getNode(pattern="BrainTumor")
    #     self.setMaxThresholdMaximumByVolume(volumeNode)
    #     self.setMinThresholdMaximumByVolume(volumeNode)
    
    
    # def onLoadCustomVolumeButton(self):
    #     """
    #     Load a volume by the current text in combobox
    #     """
    #     volumeName = self.volueNameComboBox.currentText
    #     loadedVolumeNode = slicer.util.loadVolume(self.volumesPath + volumeName)
    #     self.setMaxThresholdMaximumByVolume(loadedVolumeNode)
    #     self.setMinThresholdMaximumByVolume(volumeNode)

    def onClearButton(self):
        """
        Remove all the markups fiducial from the scene
        """
        markupsNode = slicer.util.getNode( "MarkupsFiducial" ) 
        markupsNode.RemoveAllMarkups()
      

    def onClearOrganButton(self):
        """
        Remove all the markups fiducial from the scene named with the selected organ's name 
        """
        markupsNode = slicer.util.getNode( "MarkupsFiducial" ) 
        organName = self.currentSeedNameComboBox.currentText.replace(" ", "").split(":")[1]
        i = 0
        while i < markupsNode.GetNumberOfFiducials():
          name = markupsNode.GetNthFiducialLabel(i)
          if name == organName :
              markupsNode.RemoveMarkup(i)
          else :
              i += 1


    def onSaveMarkersButton(self):
        """
        Save all the markups fiducial in the given path's file
        The created file must end with .seed extension 
        """
        fileName = self.seedsPath + self.fileNameSeedsLineEdit.text
        markupsNode  = slicer.util.getNode( slicer.modules.markups.logic().GetActiveListID() )
        
        if self.fileNameSeedsComboBox.findText(self.fileNameSeedsLineEdit.text) == -1:
            self.fileNameSeedsComboBox.addItem(self.fileNameSeedsLineEdit.text)
        
        with open(fileName, "w+") as fp:
            fp.write("# columns = name, x, y, z, label\n")
            for i in range(markupsNode.GetNumberOfFiducials()): 
                point_ras = [0, 0, 0]
                markupsNode.GetNthFiducialPosition(i, point_ras)
                name = markupsNode.GetNthFiducialLabel(i)
                label = int(markupsNode.GetNthControlPointDescription(i))
                fp.write("{};{};{};{};{}\n".format(name, point_ras[0], point_ras[1], point_ras[2], label))
      
        logging.info('Markers saved in ' + fileName)
    

    def onLoadMarkersButton(self):  
        """
        Load the markups fiducial from the given path's file
        """
        start_time = time.time() 
        fileName = self.seedsPath + self.fileNameSeedsLineEdit.text
      
        markupsNode = slicer.mrmlScene.GetFirstNodeByName("MarkupsFiducial")
        if markupsNode == None:
            markupsNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")
      
        markupsNode.RemoveAllMarkups()
      
        # name, point_ras, label
        markups = self.loadMarkupsFromSeedFile(fileName)
      
        for i in range(len(markups)):
            point_ras = markups[i][1]
            markupsNode.AddFiducial(point_ras[0], point_ras[1], point_ras[2])
            markupsNode.SetNthFiducialLabel(i, markups[i][0])
            markupsNode.SetNthControlPointDescription(i, str(markups[i][2]))
            markupsNode.SetNthMarkupLocked (i, False)

        loadTime = time.time() - start_time
        logging.info('Markers loaded from ' + fileName + ' : ' + str(loadTime) + " seconds")
    

    def onSaveSegmentationFileChange(self):
        self.saveSegmentationButton.enabled = self.saveSegmentationName.text != ""
            

    def onSaveByIntensitiesCheckBox(self):
        self.generateDataCsvCheckBox.enabled = self.saveByIntensitiesCheckBox.isChecked()
        

    def onSaveSegmentationButton(self):
        inputVolume = self.inputSelector.currentNode()
        seedsFileName = self.fileNameSeedsLineEdit.text
        segmentationFileName = self.saveSegmentationName.text
        
        if not inputVolume:
            logging.debug('no input volume node defined')
            return
        
        if segmentationFileName == "":
            logging.debug('no segmentation name defined')
            return
        
        if not self.saveByLabelsCheckBox.isChecked() and not self.saveByIntensitiesCheckBox.isChecked():
            logging.debug('At least one segmentation save mode must be checked')
            return

        if self.saveByLabelsCheckBox.isChecked():
            self.saveSegmentation(inputVolume, segmentationFileName)
        
        if self.saveByIntensitiesCheckBox.isChecked():
            # Create volume keeping only intensities where labels are not equal to 0 or are background
            backgroundLabel = len(self.seedsData)
            inputVoxels = slicer.util.arrayFromVolume(inputVolume)
            outputVoxels = slicer.util.arrayFromVolume(self.outputVolume)
            
            voxelsToSave = np.copy(inputVoxels)
            voxelsShape = voxelsToSave.shape
            voxelsToSave = np.array( [0 if y == 0 or y == backgroundLabel else x for x, y in zip(inputVoxels.ravel(), outputVoxels.ravel())], dtype=np.int16 )
            voxelsToSave = voxelsToSave.reshape( voxelsShape )

            volumesLogic = slicer.modules.volumes.logic()
            toSaveNode = volumesLogic.CloneVolume(slicer.mrmlScene, inputVolume, self.outputVolume.GetName() + "_intensities")
            slicer.util.updateVolumeFromArray(toSaveNode, voxelsToSave)
            slicer.util.saveNode(toSaveNode, self.globalPath + "Segmentations/" + segmentationFileName)
            self.outputVolumeWithIntensities = toSaveNode

            if self.generateDataCsvCheckBox.isChecked():

                csvFile =   os.path.splitext(self.globalPath + "Segmentations/" + segmentationFileName)[0] + ".csv"
                with open(csvFile, 'w') as csvfile:
                    writer = csv.writer(csvfile, delimiter=',',
                        quotechar='|', quoting=csv.QUOTE_MINIMAL)
                    writer.writerow(["Label", "voxels count", "min", "max", "mean", "std"])
                    
                    # For each label
                    for seedData in self.seedsData:
                        label = int(seedData[0])

                        if label == len(self.seedsData):
                            continue
                        
                        voxelsByLabel = np.array( [ x for x, y in zip(inputVoxels.ravel(), outputVoxels.ravel()) if y == label ] )
                    
                        voxelsCount = len(voxelsByLabel)
                        minIntensity = 0 if voxelsCount == 0 else np.amin(voxelsByLabel)
                        maxIntensity = 0 if voxelsCount == 0 else np.amax(voxelsByLabel)
                        meanIntensity = 0 if voxelsCount == 0 else np.mean(voxelsByLabel)
                        stdIntensity = 0 if voxelsCount == 0 else np.std(voxelsByLabel)    

                        writer.writerow([label, str(voxelsCount), str(minIntensity), str(maxIntensity), str(meanIntensity), str(stdIntensity)])


        # Add new segmentation file to the segmentation's combobox
        if self.segmentationFilesComboBox.findText(segmentationFileName) == -1:
            self.segmentationFilesComboBox.addItem(segmentationFileName)


    def onLoadSegmentationButton(self):
        """
        Load the selected segmentation from combobox on the scene 
        Clone the current node and create a segmentation based on the loaded label map
        """
        inputVolume = self.inputSelector.currentNode()
        segmentationFile = self.segmentationsPath + self.segmentationFilesComboBox.currentText
        
        loadedSegmentationVolumeNode = slicer.util.loadVolume(segmentationFile)
        voxels = slicer.util.arrayFromVolume(loadedSegmentationVolumeNode)
        imgLabel = np.copy(voxels)
             
        tmpVoxels = np.copy(voxels)
        tmpVoxels[:] = imgLabel[:]
      
        slicer.util.updateVolumeFromArray(loadedSegmentationVolumeNode, tmpVoxels)
    
        removeLastSegmentation = self.removeLastSegmentationCheckBox.isChecked()       
        showBackGround = self.showBackGroundCheckBox.isChecked()
        displaySegmentationMap(loadedSegmentationVolumeNode, imgLabel, self.labelColorsList, removeLastSegmentation, showBackGround)
        
        slicer.util.setSliceViewerLayers(background=inputVolume)
        

    def onSegmentButton(self):
        """
        Start the segmentation and save it in a file named with all the given parameters
        Add this new segmentation in combobox

        If no markups fiducial are on the scene, try to load them from the current seeds path 
        """
        markupsNode = slicer.mrmlScene.GetFirstNodeByName("MarkupsFiducial")

        seedsFileName = self.fileNameSeedsLineEdit.text
        marginMask = int(self.marginMask.value)
        distance = int(self.distance.value)
        gamma = float(self.gammaSpinBox.value)
        regularizationDiameter = int(self.regularizationDiameter.value)
        minThreshold = int(self.minThresholdSlider.value)
        maxThreshold = int(self.maxThresholdSlider.value)
        
        # Tous les points convertis dans le repere RAS
        self.markupsList = []
        
        if markupsNode != None:
            for i in range(markupsNode.GetNumberOfFiducials()):
                point_ras = [0, 0, 0]
                markupsNode.GetNthFiducialPosition(i, point_ras)
                name = markupsNode.GetNthFiducialLabel(i)
                label = int(markupsNode.GetNthControlPointDescription(i))
                self.markupsList.append([name, point_ras, label])
        
        if len(self.markupsList) == 0:
            fileName = self.seedsPath + self.fileNameSeedsLineEdit.text
            self.markupsList  = self.loadMarkupsFromSeedFile(fileName)
        
        if len(self.markupsList) == 0:
            print("There is no fiducial markups !")
            return
        
        # logic = RegularizedFastMarchingLogic()
        self.logic.setGlobalPath(self.globalPath)
        self.logic.setSeedsFileName(seedsFileName)
        self.logic.setRemoveLastSegmentation(self.removeLastSegmentationCheckBox.isChecked())
        self.logic.setShowBackGround(self.showBackGroundCheckBox.isChecked())
        result = self.logic.run(self.inputSelector.currentNode(), self.labelColorsList, self.markupsList,
            marginMask, distance, gamma, regularizationDiameter, [minThreshold, maxThreshold])

        if result : # Run succeed
            # Set the segmentation file UI name with this seeds file name and the used paramaters
            segmentationFileName = getSegmentationFileName(seedsFileName, distance, gamma, marginMask, regularizationDiameter)
            self.saveSegmentationName.text = segmentationFileName 
            self.outputVolume = result
            
    def addMarkupcallback(self):
        """
        Set the selected seed as the next seed to add and toggle the fiducial placement
        """
        if self.currentSeedNameComboBox.currentIndex == self.currentSeedNameComboBox.count - 1:
            self.currentSeedNameComboBox.setCurrentIndex( self.lastLabelIndex )
        interactionNode = slicer.app.applicationLogic().GetInteractionNode()
        interactionNode.SetCurrentInteractionMode(interactionNode.Place)
      

    def addBgMarkupcallback(self):
        """
        Set the background seed as the next seed to add and toggle the fiducial placement
        """
        #print("Markup background markup index  : " + str(self.lastLabelIndex ))
        if self.currentSeedNameComboBox.currentIndex != self.currentSeedNameComboBox.count - 1:
            self.lastLabelIndex = self.currentSeedNameComboBox.currentIndex
        self.currentSeedNameComboBox.setCurrentIndex( self.currentSeedNameComboBox.count - 1 )
        interactionNode = slicer.app.applicationLogic().GetInteractionNode()
        interactionNode.SetCurrentInteractionMode(interactionNode.Place)
    
    def setGammaValueFromSlider(self): 
        """
        Setter connect on slider, allow to have higher float precision
        """
        self.gammaSpinBox.setValue( self.gammaSlider.value / 1000 )


    def setGammaValueFromSpinBox(self): 
        """
        Setter connect on slider, allow to have higher float precision
        """
        self.gammaSlider.setValue( self.gammaSpinBox.value * 1000)

    
    def setMinThresholdValue(self):
        self.minThresholdSlider.value = min(self.minThresholdSlider.value ,self.maxThresholdSlider.value )

    def setMaxThresholdValue(self):
        self.maxThresholdSlider.value = max(self.minThresholdSlider.value ,self.maxThresholdSlider.value )


    def setSelectedSeedsFile(self, seedFile):    
        """
        Setter connect on combobox to select the seeds file name
        Inputs:
          * seedFile : selected seeds file name
        """
        self.fileNameSeedsLineEdit.text = seedFile
    

    def setSeedsLabelFromFile(self, labelFile):
        """
        Load the labels from file in combobox, connect on combobox
        Inputs:
          * labelFile : selected seeds file name
        """
        self.seedsData = self.loadCSVSeeds(self.seedsCsvPath + labelFile)
        self.labelColorsList = [[s[1], s[2]] for s in self.seedsData]
        
        self.currentSeedNameComboBox.clear() 
        for seed in self.seedsData: 
            self.currentSeedNameComboBox.addItem(str(seed[0]) + " : " + str(seed[1]))
        self.lastLabelIndex = self.currentSeedNameComboBox.currentIndex


    def loadCSVSeeds(self, csvFilePath):
        """
        Load and return the labels file from the given path in a list
        Inputs:
          * csvFilePath : the labels file
        Ouputs:
          * labels : the labels list containing the index, name and color of each label
        """
        labels = []
        with open(csvFilePath) as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='|')
            for row in reader:
                labels.append([row[0], row[1], [float(row[2]), float(row[3]), float(row[4]) ]])
        print(csvFilePath + " : labels loaded")
        return labels
    

    def loadMarkupsFromSeedFile(self, seedFile):
        """
        Load and return the markups file from the given path in a list
        Inputs:
          * seedFile : the seedFile to load
        Ouputs:
          * markups : the markups list containing the name, label and coordinate in RAS (Right, Anterior, Superior) coordinates of each label
        """
        markups = []
        with open(seedFile, "r") as fp:
            lines = fp.readlines()
          
            for line in lines: 
            # for line in fp: 
                if "#" in line: # comment line
                    continue
                tokens = line.replace(" ", "").split(";")
                name = tokens[0]
                point_ras = [float(tokens[1]), float(tokens[2]), float(tokens[3])]
                label= int(tokens[4])
                markups.append([name, point_ras, label])
        return markups


    #def saveSegmentation(self, inputVolume, seedsFile, distance, gamma, marginMask, regularizationDiameter):
    def saveSegmentation(self, inputVolume, segmentationFileName):
        """
        Save this segmentation / labels image in a file named with the given parameters 
        Inputs:
          * inputVolume : labels image to save 
        """
        segmentationFileName = self.globalPath + "Segmentations/" + segmentationFileName
        segmentationNode = slicer.mrmlScene.GetFirstNodeByClass('vtkMRMLSegmentationNode')
        labelmapVolumeNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLabelMapVolumeNode')
        slicer.modules.segmentations.logic().ExportVisibleSegmentsToLabelmapNode(segmentationNode, labelmapVolumeNode, inputVolume)

        slicer.util.saveNode(labelmapVolumeNode, segmentationFileName)
        print("Segmentation saved : " + segmentationFileName)

    #endregion

    def cleanup(self):
        """
        Called when the application closes and the module widget is destroyed.
        """
        self.removeObservers()


#
# RegularizedFastMarchingLogic
#

class RegularizedFastMarchingLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self):
        """
        Called when the logic class is instantiated. Can be used for initializing member variables.
        """
        ScriptedLoadableModuleLogic.__init__(self)

    def isValidInputOutputData(self, inputVolumeNode):
        """Validates if the output is not the same as input
        """
        if not inputVolumeNode:
          logging.debug('isValidInputOutputData failed: no input volume node defined')
          return False
        return True

    def setGlobalPath(self, path):
        """
        Setter globalPath
        """
        self.globalPath = path

    def setSeedsFileName(self, fileName):
        """
        Setter seedsFileName
        """
        self.seedsFileName = fileName
     
    def setRemoveLastSegmentation(self, state):
        """
        Setter removeLastSegmentation bool
        """
        self.removeLastSegmentation = state

    def setShowBackGround(self, state):
        """
        Setter showBackGround bool
        """
        self.showBackGround = state

    # def getSeedsByState(self, previousSeeds, newSeeds):
    #     """
    #     # Return the seeds in newSeeds that are not in previousSeeds
    #     Return the added, modified, deleted seeds in differents arrays
    #     """
    #     seeds = [[], [], []] # added, modified, deleted

    #     # Fill dicts by id
    #     previousSeedsDict = {}
    #     for seed in previousSeeds:
    #         previousSeedsDict[seed["id"]] = seed

    #     newSeedsDict = {}
    #     for seed in newSeeds:
    #         newSeedsDict[seed["id"]] = seed

    #     # Find added and modified seeds
    #     for key in newSeedsDict.keys():
    #         if not key in previousSeedsDict: # added
    #             seeds[0].append(newSeedsDict[key])
    #         elif newSeedsDict[key] != previousSeedsDict[key] : # modified
    #             seeds[1].append(newSeedsDict[key])
        
    #     # Find deleted seeds
    #     for key in previousSeedsDict.keys():
    #         if not key in newSeedsDict: # deleted
    #             seeds[2].append(previousSeedsDict[key])

    #     return seeds 

    # def updatePreviousSegmentation(self, imgLabel, imgIds, imgDist, seeds, distance):
    #     """
    #         Set modified or removed points label, id and dist to 0, 0 and distance
    #     """
    #     for seed in seeds:
    #         indexes = np.where(imgIds == seed.get("id"))
            
    #         for i in range(len(indexes[0])):
    #             imgLabel[indexes[0][i]] [indexes[1][i]] [indexes[2][i]] = 0
    #             imgIds[indexes[0][i]] [indexes[1][i]] [indexes[2][i]] = 0
    #             imgDist[indexes[0][i]] [indexes[1][i]] [indexes[2][i]] = distance
            
    #     return imgLabel, imgIds, imgDist
         
    def getSeedsFromMarkups(self, markupsList, nbLabel):
        """
        Return a formatted markups list from the given markups list.
        The background seeds have unique label because there using a unique mask 
        Inputs:
          * markupsList : the raw markups list
          * nbLabel : the number of label to know which seed is a background seed
        Ouputs: 
          * seeds : the formatted markups list
        """
        seeds = []
        i = 1
        backGroundCount = 0
        for markup in markupsList:
            label = markup[2]
            if markup[2] == nbLabel:
                label += backGroundCount
                backGroundCount += 1
            seeds.append({"id": i, "label": label, "pos": markup[1]})
            i += 1
        
        return seeds
   
    def getIJKSeeds(self, inputVolume, seeds) :
        """
        Return the given seeds list where each seed is transform from RAS (Right, Anterior, Superior) coordinates to IJK (image) coordinates
        Inputs:
          * inputVolume : volume transform reference 
          * seeds : list containing all the seeds in RAS coordinates
        Outputs:
            seeds : list containing all the seeds in IJK coordinates
        """
        for i in range(len(seeds)): # pour chaque point 
            point_ras = seeds[i].get("pos")
                
            # If volume node is transformed, apply that transform to get volume's RAS coordinates
            transformRasToVolumeRas = vtk.vtkGeneralTransform()
            slicer.vtkMRMLTransformNode.GetTransformBetweenNodes(None, inputVolume.GetParentTransformNode(), transformRasToVolumeRas)
            point_VolumeRas = transformRasToVolumeRas.TransformPoint(point_ras[0:3])
                
            # Get voxel coordinates from physical coordinates
            volumeRasToIjk = vtk.vtkMatrix4x4()
            inputVolume.GetRASToIJKMatrix(volumeRasToIjk)
            point_Ijk = [0, 0, 0, 1]
            volumeRasToIjk.MultiplyPoint(np.append(point_VolumeRas,1.0), point_Ijk)
            point_Ijk = [ int(round(c)) for c in point_Ijk[0:3] ]
            point_Ijk = [point_Ijk[2], point_Ijk[1], point_Ijk[0]]
            seeds[i]["pos"] = point_Ijk
        return seeds   
    
    # def sortSeedsBackgroundFirst(self, seeds, nbLabel):
    #     """
    #     Return the seeds list with the background seeds at the beginning
    #     Inputs:
    #       * seeds : list of seeds unsorted
    #     Outputs:
    #       * seeds : list with the background seeds at the beginning
    #     """
    #     for i in range(len(seeds)):
    #         if seeds[i]["pos"] >= nbLabel:
    #             seeds.insert(0, seeds.pop(i))
    #     return seeds


    def run(self, inputVolume, labelColorsList, markupsList, marginMask, distance, gamma, regularizationDiameter, threshold):
        """
        Run the segmentation algorithm with the given parameters and get the labels image
        Put the result in inputVolume's clone
        Create and display the segmentation based on this result   
        """        
        if not self.isValidInputOutputData(inputVolume):
            slicer.util.errorDisplay('Input volume is the same as output volume. Choose a different output volume.')
            return False
          
        #Clone un node  
        volumesLogic = slicer.modules.volumes.logic()
        clonedVolumeNode = volumesLogic.CloneVolume(slicer.mrmlScene, inputVolume, "clone")
      
        # Ajoute une zone coloree autour de chaque marqueurs
        voxels = slicer.util.arrayFromVolume(clonedVolumeNode)
        tmpVoxels = np.copy(voxels)
        
        seeds = self.getSeedsFromMarkups(markupsList, len(labelColorsList))
        seeds = self.getIJKSeeds(inputVolume, seeds)  
        #seeds = self.sortSeedsBackgroundFirst(seeds, len(labelColorsList))

        # Si nouvelle segmentation avec meme volume
        # les prochaines graines utilisees seront les nouvelles et les modifiees
        # Retrait des graines modifiees et supprimees de imgLabel et imgDist 
        # if self.previousVolumeName == inputVolume.GetName():
        #     seedsStates = self.getSeedsByState(self.previousSeeds, seeds)
        #     newSeeds = seedsStates[1] + seedsStates[2]
        #     nextSeeds = seedsStates[0] + seedsStates[1]
            
        #     self.imgLabel, self.imgIds, self.imgDist = self.updatePreviousSegmentation(self.imgLabel, self.imgIds, self.imgDist, newSeeds, distance)

        #     self.previousSeeds = seeds
        #     seeds = nextSeeds

        #     print("seeds states", seedsStates)
        #     print("new seeds", newSeeds)

        # else : # reset
        #     self.imgLabel = np.array([])
        #     self.imgIds = np.array([])
        #     self.imgDist = np.array([])
        #     self.previousSeeds = seeds
        
        # self.previousVolumeName = inputVolume.GetName()

        # Map de regularisation - dilatation de l'image
        start_time = time.time()
        R = np.copy(tmpVoxels)

        # Check if regularization exists 
        regularizationFile = self.globalPath + "Regularizations/" + inputVolume.GetName() + "_" + str(regularizationDiameter) + ".nii.gz"
        # If it exists, load this one
        if os.path.isfile(regularizationFile):
            print("--- Alredy existing regularization")
            regularizationVolumeNode = slicer.util.loadVolume(regularizationFile)
            voxels = slicer.util.arrayFromVolume(regularizationVolumeNode)
            R = np.copy(voxels)
            slicer.mrmlScene.RemoveNode(regularizationVolumeNode)
        # Else, create a new one
        else :
            print("- Creating new regularization start : ")
            R = regularization(voxels, int(regularizationDiameter/2))
            print("- Creating new regularization end")

            regularizationVolumeNode = volumesLogic.CloneVolume(slicer.mrmlScene, inputVolume, inputVolume.GetName() + "_regularization_" + str(regularizationDiameter))
            slicer.util.updateVolumeFromArray(regularizationVolumeNode, R)
            slicer.util.saveNode(regularizationVolumeNode, regularizationFile)

        regularization_time = time.time() - start_time
        print("- Regularization time : %s seconds -" % regularization_time)


        # def segmentation(globalPath, volume, voxels, seeds, marginMask, distance, regDiameter):
        self.imgLabel, self.imgIds, self.imgDist = segmentation(inputVolume, tmpVoxels, R, seeds, 
            len(labelColorsList), marginMask, distance, gamma, regularizationDiameter, threshold)    
       
        tmpVoxels[:] = self.imgLabel[:]
        
        slicer.util.updateVolumeFromArray(clonedVolumeNode, tmpVoxels)

        #Copie le resultat dans le node d'arrive
        outputVolume = slicer.vtkSlicerVolumesLogic().CloneVolume(slicer.mrmlScene, clonedVolumeNode, inputVolume.GetName() + "_segmentation", True)
        
        # Affiche les segments en couleur de chaque graine
        displaySegmentationMap(clonedVolumeNode, self.imgLabel, labelColorsList, self.removeLastSegmentation, self.showBackGround)
        
        # Supprime la copie
        if slicer.mrmlScene:
            slicer.mrmlScene.RemoveNode(clonedVolumeNode)        
      
        slicer.util.setSliceViewerLayers(background=inputVolume)
        return outputVolume


def displaySegmentationMap(inputVolume, segmentationMap, labelColorsList, removeLastSegmentation, showBackGround):
    """
    Create a segmentation like using the segment editor's tool, create a segment for each different label in the segmentation image
    Inputs: 
      *  :
    """    
    # Remove last segmentation, including 3D representation
    if removeLastSegmentation:
        countSegmentationNode = slicer.mrmlScene.GetNumberOfNodesByClass("vtkMRMLSegmentationNode")
        if countSegmentationNode > 0:
            slicer.mrmlScene.RemoveNode( slicer.mrmlScene.GetNthNodeByClass(countSegmentationNode-1, "vtkMRMLSegmentationNode") )
    
    segmentationNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
    segmentationNode.CreateDefaultDisplayNodes() # only needed for display
    segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(inputVolume)
    
    segmentationNode.RemoveClosedSurfaceRepresentation()
    
    displayNode = slicer.vtkMRMLSegmentationDisplayNode()
    slicer.mrmlScene.AddNode(displayNode)
    segmentationNode.SetAndObserveDisplayNodeID(displayNode.GetID())
     
    # Create segment editor to get access to effects
    segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
    segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
    segmentEditorNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentEditorNode")
    segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
    segmentEditorWidget.setSegmentationNode(segmentationNode)
    segmentEditorWidget.setMasterVolumeNode(inputVolume)
    
    for i in range(len(labelColorsList)):
        addedSegmentID = segmentationNode.GetSegmentation().AddEmptySegment(labelColorsList[i][0])
        segmentationNode.GetSegmentation().GetSegment(addedSegmentID).SetColor(labelColorsList[i][1])
        segmentEditorWidget.setCurrentSegmentID(addedSegmentID);
    
        # Thresholding
        segmentEditorWidget.setActiveEffectByName("Threshold")
        effect = segmentEditorWidget.activeEffect()
        thresh = i+1
        effect.setParameter("MinimumThreshold", str(clip(thresh, 0, 255)))
        effect.setParameter("MaximumThreshold", str(clip(thresh, 0, 255)))

        if not showBackGround and i+1 == len(labelColorsList):
            displayNode.SetSegmentVisibility (addedSegmentID, False)

        effect.self().onApply()
        # segmentEditorWidget.setActiveEffectByName("Smoothing")
        # effect = segmentEditorWidget.activeEffect()
        # effect.setParameter("SmoothingMethod", "MEDIAN")
        # effect.setParameter("KernelSizeMm", 11)
        # effect.self().onApply()
    
        # Clean up
        # segmentEditorWidget = None
        # slicer.mrmlScene.RemoveNode(segmentEditorNode)
        
        # surfaceMesh = None
        # segmentationNode.GetClosedSurfaceRepresentation(addedSegmentID, surfaceMesh)
    # print 3D representation
    segmentationNode.CreateClosedSurfaceRepresentation()