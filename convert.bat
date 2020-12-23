rem SLICER is path to a recent Slicer-4.11 executable
rem set SLICER=c:\Users\andra\AppData\Local\NA-MIC\Slicer 4.11.0-2020-09-18\Slicer.exe
set SLICER=c:\Users\andra\AppData\Local\NA-MIC\Slicer 4.13.0-2020-12-18\Slicer.exe

rem DATA_ROOT is this folder
set DATA_ROOT=c:\D\LabelmapToDICOMSeg

"%SLICER%" --python-script "%DATA_ROOT%\convert.py" ^
  --conversion-list "%DATA_ROOT%\todicomseg.csv" ^
  --data-root-dir "%DATA_ROOT%\inputvolumes" ^
  --ref-dicom-images-dir "%DATA_ROOT%\inputdicom" ^
  --output-dir "%DATA_ROOT%\output"

pause
