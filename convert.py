segmentDescription = {
    "Liver": {
        "terminology": "Segmentation category and type - DICOM master list~SCT^123037004^Anatomical Structure~SCT^10200004^Liver~^^~Anatomic codes - DICOM master list~^^~^^",
        "color": (0.8666666666666667, 0.5098039215686274, 0.396078431372549)},
    "Tumor": {
        "terminology": "Segmentation category and type - DICOM master list~SCT^49755003^Morphologically Altered Structure~SCT^4147007^Mass~^^~Anatomic codes - DICOM master list~SCT^10200004^Liver~^^",
        "color": (0.5647058823529412, 0.9333333333333333, 0.5647058823529412)},
    "Venous": {
        "terminology": "Segmentation category and type - DICOM master list~SCT^85756007^Tissue~SCT^29092000^Vein~^^~Anatomic codes - DICOM master list~SCT^10200004^Liver~^^",
        "color": (0.0, 0.592156862745098, 0.807843137254902)},
    }

#####################################

def installExtensions():
    extensionsName = ['SlicerDevelopmentToolbox', 'DCMQI', 'PETDICOMExtension', 'QuantitativeReporting']
    em = slicer.app.extensionsManagerModel()
    restarNeeded = False
    for extensionName in extensionsName:
        if em.isExtensionInstalled(extensionName):
            continue
        extensionMetaData = em.retrieveExtensionMetadataByName(extensionName)
        url = em.serverUrl().toString()+'/download/item/'+extensionMetaData['item_id']
        extensionPackageFilename = slicer.app.temporaryPath+'/'+extensionMetaData['md5']
        slicer.util.downloadFile(url, extensionPackageFilename)
        em.installExtension(extensionPackageFilename)
        restarNeeded = True
    if restarNeeded:
        slicer.util.restart()

def setupDicomDatabase(databaseDirectory):
    if slicer.dicomDatabase.databaseDirectory==databaseDirectory and slicer.dicomDatabase.isOpen:
        # database already exists and opened
        return
    # Make sure DICOM browser widget exists
    if slicer.modules.DICOMInstance.browserWidget is None:
        slicer.util.selectModule('DICOM')
    # Set database directory
    slicer.modules.DICOMInstance.browserWidget.dicomBrowser.setDatabaseDirectory(databaseDirectory)
    if not slicer.dicomDatabase.isOpen:
        # no database could be opened, try creating a new folder in the same parent folder
        slicer.modules.DICOMInstance.browserWidget.dicomBrowser.createNewDatabaseDirectory()
    if not slicer.dicomDatabase.isOpen:
        # all attempts failed
        raise(ValueError("Failed to open/create DICOM database at {0}".format(databaseDirectory)))

def importReferenceImages(referenceDicomImagesDir, databaseDirectory):
    # Use DICOM module's browser widget so that user can see progress on GUI
    if slicer.modules.DICOMInstance.browserWidget is None:
        slicer.util.selectModule('DICOM')
    # Use default import mode of adding link to imported files (do not copy)
    slicer.modules.DICOMInstance.browserWidget.dicomBrowser.importDirectory(referenceDicomImagesDir)
    slicer.modules.DICOMInstance.browserWidget.dicomBrowser.waitForImportFinished()

def getConversionList(conversionListCsvFile):
    import csv
    reader = csv.DictReader(open(conversionListCsvFile), delimiter=",")
    conversionList = []
    import csv
    with open(conversionListCsvFile, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            conversionList.append(dict(row))
    return conversionList

def convertLabelmapToDicomSeg(conversion, dataRootDir, outputDir):
    slicer.mrmlScene.Clear()
    idColumnName = "id"
    id = conversion[idColumnName]
    refImageSeriesInstanceUIDColumnName = "ReferenceImageSeriesInstanceUID"
    refImageSeriesInstanceUID = conversion[refImageSeriesInstanceUIDColumnName]

    # Load reference volume
    from DICOMLib import DICOMUtils
    loadedImageSeriesNodeIds = DICOMUtils.loadSeriesByUID([refImageSeriesInstanceUID])
    if not loadedImageSeriesNodeIds:
        raise ValueError("Could not load reference image: id={0}, seriesInstanceUID={0}".format(id, refImageSeriesInstanceUID))
    referenceVolumeNode = slicer.mrmlScene.GetNodeByID(loadedImageSeriesNodeIds[0])
    referenceVolumeIjkToRas = vtk.vtkMatrix4x4()
    referenceVolumeNode.GetIJKToRASMatrix(referenceVolumeIjkToRas)

    # Create segmentation node
    segmentationNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLSegmentationNode')
    segmentationNode.SetNodeReferenceID(segmentationNode.GetReferenceImageGeometryReferenceRole(), referenceVolumeNode.GetID())
    segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(referenceVolumeNode)

    # Add each segment
    for columnName in conversion.keys():
        if columnName in [idColumnName, refImageSeriesInstanceUIDColumnName]:
            continue
        if not conversion[columnName]:
            continue
        segmentFileName = dataRootDir + "/" + conversion[columnName]
        segmentVolumeNode = slicer.util.loadLabelVolume(segmentFileName)
        # Fix geometry based on reference volume node
        segmentVolumeNode.SetIJKToRASMatrix(referenceVolumeIjkToRas)
        # Binarize volume (outside the segment if value is -1000)
        voxels = slicer.util.arrayFromVolume(segmentVolumeNode)
        voxels[voxels>-1000]=1
        voxels[voxels<=-1000]=0
        slicer.util.arrayFromVolumeModified(segmentVolumeNode)
        # Import segment to segmentation node
        slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(segmentVolumeNode, segmentationNode)
        importedSegmentId = segmentationNode.GetSegmentation().GetNthSegmentID(segmentationNode.GetSegmentation().GetNumberOfSegments()-1)
        importedSegment = segmentationNode.GetSegmentation().GetSegment(importedSegmentId)
        importedSegment.SetName(columnName)
        importedSegment.SetTag("TerminologyEntry", segmentDescription[columnName]["terminology"])
        importedSegment.SetColor(segmentDescription[columnName]["color"])
        slicer.mrmlScene.RemoveNode(segmentVolumeNode)

    # Export lightbox image
    # segmentationNode.CreateClosedSurfaceRepresentation()
    segmentationNode.GetDisplayNode().SetOpacity2DFill(0.2)
    slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpView)
    captureLightboxImage("{0}/lightbox_{1}.png".format(outputDir, id))

    shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
    referenceVolumeShItem = shNode.GetItemByDataNode(referenceVolumeNode)
    studyShItem = shNode.GetItemParent(referenceVolumeShItem)
    segmentationShItem = shNode.GetItemByDataNode(segmentationNode)
    shNode.SetItemParent(segmentationShItem, studyShItem)

    # Export to DICOM
    import DICOMSegmentationPlugin
    exporter = DICOMSegmentationPlugin.DICOMSegmentationPluginClass()
    exportables = exporter.examineForExport(segmentationShItem)
    for exp in exportables:
        exp.directory = outputDir
        print(exp.name)
    exporter.export(exportables)

def captureLightboxImage(resultImageFilename, viewName=None, rows=None, columns=None, positionRange=None, rangeShrink=None):
    viewName = viewName if viewName else "Red"
    rows = rows if rows else 4
    columns = columns if columns else 6

    sliceWidget = slicer.app.layoutManager().sliceWidget(viewName)

    if positionRange is None:
        sliceBounds = [0,0,0,0,0,0]
        sliceWidget.sliceLogic().GetLowestVolumeSliceBounds(sliceBounds)
        slicePositionRange = [sliceBounds[4], sliceBounds[5]]
    else:
        slicePositionRange = [positionRange[0], positionRange[1]]

    if rangeShrink:
        slicePositionRange[0] += rangeShrink[0]
        slicePositionRange[1] -= rangeShrink[1]

    import ScreenCapture
    screenCaptureLogic = ScreenCapture.ScreenCaptureLogic()
    destinationFolder = slicer.app.temporaryPath
    numberOfFrames = rows*columns
    filenamePattern = "_lightbox_tmp_image_%05d.png"
    viewNode = sliceWidget.mrmlSliceNode()
    # Suppress log messages
    def noLog(msg):
       pass
    screenCaptureLogic.addLog=noLog
    # Capture images
    screenCaptureLogic.captureSliceSweep(viewNode, slicePositionRange[0], slicePositionRange[1], numberOfFrames, destinationFolder, filenamePattern)
    # Create lightbox image
    screenCaptureLogic.createLightboxImage(columns, destinationFolder, filenamePattern, numberOfFrames, resultImageFilename)

    # Clean up
    screenCaptureLogic.deleteTemporaryFiles(destinationFolder, filenamePattern, numberOfFrames)

def main(argv):
    import argparse
    parser = argparse.ArgumentParser(description="Convert labelmap images to DICOM Segmentation Objects")
    parser.add_argument("-r", "--ref-dicom-images-dir", dest="referenceDicomImagesDir", metavar="PATH",
                        default="", required=True,
                        help="Folder that contains input reference DICOM images")
    parser.add_argument("-c", "--conversion-list", dest="conversionListCsvFile", metavar="PATH",
                        default="", required=True,
                        help="CSV file containing list of files to convert")
    parser.add_argument("-d", "--data-root-dir", dest="dataRootDir", metavar="PATH",
                        default="",
                        help="Folder containing input labelmap images")
    parser.add_argument("-o", "--output-dir", dest="outputDir", metavar="PATH",
                        default="",
                        help="Folder for output DICOM segmentation objects")
    args = parser.parse_args(argv)

    databaseDirectory = args.outputDir

    installExtensions()
    setupDicomDatabase(args.outputDir)
    importReferenceImages(args.referenceDicomImagesDir, databaseDirectory)
    conversionList = getConversionList(args.conversionListCsvFile)

    # Convert
    for conversion in conversionList:
        convertLabelmapToDicomSeg(conversion, args.dataRootDir, args.outputDir)

    print("Conversion successfully completed")
    return 0  # success

if __name__ == "__main__":
    import sys
    try:
        result = main(sys.argv[1:])
        sys.exit(result)
    except Exception as e:
      import traceback
      traceback.print_exc()
      logging.error("Conversion failed")
      sys.exit(1)
