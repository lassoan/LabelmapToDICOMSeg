# LabelmapToDICOMSeg
Script for converting labelmap volumes to DICOM segmentation objects

## Usage

1. Install 3D Slicer (4.11 or later)
2. Create a CSV file that contains which segmentation (stored as one label per volume, as nrrd/mha/nii file) belong to which DICOM image (identified by its series instance UID)
3. Run `convert.py` using 3D Slicer's Python environment 

If this repository is checked out to c:\D\LabelmapToDICOMSeg and input DICOM images (e.g., CT scans in DICOM format) are stored in `inputdicom` subfolder and segmentation labelmap volumes (nrrd/mha/nii files) are stored in `inputvolumes` subfolder and generated DICOM segmentation objects will be stored in `output` subfolder then this command can be used:

```console
set SLICER="c:\Users\andra\AppData\Local\NA-MIC\Slicer 4.11.20210226" 
set DATA_ROOT=c:\D\LabelmapToDICOMSeg
"%SLICER%" --python-script "%DATA_ROOT%\convert.py" --conversion-list "%DATA_ROOT%\todicomseg.csv" --data-root-dir "%DATA_ROOT%\inputvolumes" --ref-dicom-images-dir "%DATA_ROOT%\inputdicom" --output-dir "%DATA_ROOT%\output"
```
