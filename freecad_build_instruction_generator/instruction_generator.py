## Works in FreeCAD 0.21.2
## We do need a GUI though to run this: https://wiki.freecadweb.org/Headless%20FreeCAD

## When changing this file, you need to reinstall it:
# > import subprocess
# > import sys
# > import os
# > from pathlib import Path
# > os.chdir(path to_this_repo)
# > py = str((Path(sys.executable) / "../python").resolve())
# > subprocess.check_call([py, "-m", "pip", "install", "."])


import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore,QtGui
import ImportGui
import Import
import Part
import time
import os
from PIL import Image
from pivy import coin
from pathlib import Path

Gui.runCommand('Std_CloseAllWindows',0)

# Global variables
including_parts = False
image_id = 0
step_id = 0
parts_in_assembly_step = []
warning = ""

CWD_PATH = ""
SOURCES_PATH = {}
WARNING_PATH = ""
MIRTE = ""

def setMIRTEVersion(name):
   global MIRTE
   MIRTE = name

   # clear or generate build path
   build_path = (CWD_PATH / "build")
   if not build_path.exists():
     os.mkdir(build_path)

   build_path = (CWD_PATH / "build" / MIRTE)
   if build_path.exists():
     for f in os.listdir(build_path.resolve()):
       os.remove(os.path.join(build_path.resolve(), f))
   else:
     os.mkdir(build_path)
   SOURCES_PATH["build"] = build_path

def addSourcesPath(name, path):
   global SOURCES_PATH
   SOURCES_PATH[name] = Path(path)
   print("Added sources: " + path)

def setCwdPath(path):
   global CWD_PATH
   print("CWD path: " + path)
   CWD_PATH = Path(path)

def setWarningPath(path):
   global WARNING_PATH
   WARNING_PATH = Path(path)

def refreshFix():
   # Refresh QT and wait to avaoid black screenshots
   QtGui.QApplication.processEvents()
   time.sleep(0.5)

def add_foreground(bg_filename, fg_filename):
   background = Image.open(bg_filename)
   foreground = Image.open(fg_filename)
   foreground = foreground.convert("RGBA")
   background.paste(foreground, (0, 0), foreground)
   background.save(bg_filename, format="png")

# Save image
def save_image(toggled = False, part_id = -1, show_warning=False):
 global image_id, warning
 refreshFix()
 text = str(step_id) + ("_part" + str(part_id) if part_id > -1 else "_step" + str(image_id))
 filename = str((CWD_PATH / 'build' / MIRTE / (text + '.png')).resolve())
 Gui.activeDocument().activeView().saveImage(filename,4000,4000,'#00ffffff')
 if (toggled):
   add_foreground(filename, WARNING_PATH / "mirte-rotate.png")
 if (warning and show_warning):
   add_foreground(filename, WARNING_PATH / (warning + "warning.png"))
   warning = ""

 Gui.Selection.clearSelection()
 image_id += 1

def drawLine(begin, end):
    App.ActiveDocument.addObject("Part::Line","Line")
    App.ActiveDocument.Line.X1=begin[0]
    App.ActiveDocument.Line.Y1=begin[1]
    App.ActiveDocument.Line.Z1=begin[2]
    App.ActiveDocument.Line.X2=end[0]
    App.ActiveDocument.Line.Y2=end[1]
    App.ActiveDocument.Line.Z2=end[2]
    App.ActiveDocument.Line.Placement=App.Placement(App.Vector(0.00,0.00,0.00),App.Rotation(App.Vector(0.00,0.00,1.00),0.00))
    App.ActiveDocument.Line.Label='Line'

class Step:
    def __init__(self, object, move_vector, rotate_vector=App.Vector(0,0,0), rotate_angle=0):
      self.object = object
      self.move_vector = move_vector
      self.rotate_vector = rotate_vector
      self.rotate_angle = rotate_angle

    def execute(self):
      self.explode_step()
      self.implode_step()

    def explode_step(self, take_screenshot=True):
      self.object.Placement.move(self.move_vector)
      self.object.Placement.rotate(App.Vector(0,0,0), self.rotate_vector, self.rotate_angle)
      activeDoc = App.ActiveDocument
      Gui.Selection.addSelection(activeDoc.Name, self.object.Name)
      if take_screenshot:
         save_image()

    def implode_step(self, take_screenshot=True):
      self.object.Placement.move(self.move_vector.negative())
      self.object.Placement.rotate(App.Vector(0,0,0), self.rotate_vector, -self.rotate_angle)
      activeDoc = App.ActiveDocument
      Gui.Selection.addSelection(activeDoc.Name, self.object.Name)
      if take_screenshot:
         save_image(show_warning=True)

class ParallelSequence:
   def __init__(self, sequence):
      self.sequence = sequence

   def execute(self):
      self.explode()
      self.implode()

   def explode(self):
     for i in range(0, len(self.sequence[0].sequence)):
         for j in self.sequence:
            j.explode_step(i, False)
         if (i == len(self.sequence[0].sequence) -1):
            save_image()

   def implode(self):
     for i in range(len(self.sequence[0].sequence)-1, -1, -1):
         for j in self.sequence:
            j.implode_step(i, False)
         save_image(show_warning=True)

class Sequence:
   def __init__(self, sequence):
      self.sequence = sequence

   def execute(self):
      self.explode()
      self.implode()

   def explode(self, take_screenshot=True):
      for i in range(0, len(self.sequence)):
         self.explode_step(i, take_screenshot)

   def explode_step(self, step, take_screenshot=True):
      take_screenshot = isinstance(self.sequence[step], Step) and take_screenshot
      self.sequence[step].explode_step(take_screenshot)

   def implode(self, take_screenshot=True):
      for i in range(len(self.sequence) -1, -1, -1):
         self.implode_step(i, take_screenshot)

   def implode_step(self, step, take_screenshot=True):
      take_screenshot = isinstance(self.sequence[step], Step) and take_screenshot
      self.sequence[step].implode_step(take_screenshot)


class AssemblyProject:
    def __init__(self, name, including_parts=True):
       self.project_name = name
       self.including_parts = including_parts
       self.image_id = 0
       self.step_id = 0
       self.parts_in_assembly_step = []
       self.doc = App.newDocument(name)
       self.warning= ""
       App.setActiveDocument(self.doc.Name)
       self.topView = True
       Gui.ActiveDocument.ActiveView.getCameraNode().orientation = coin.SbRotation((-0.3320808410644531, 0.3825216293334961, 0.2297523319721222, 0.8310315608978271))

    # Import step file and move to correct orientation/location
    # NOTE: Part.read icw Part.show does not include colors of STEP
    # NOTE: Nor does Import.insert()
    def import_object(self, sourceName, file, position=App.Vector(0,0,0), rotation=App.Rotation(0,0,0)):
      # get current lsit of objects
      old_object_list = App.ActiveDocument.Objects
      file_path = str( (SOURCES_PATH[sourceName] / file).resolve() )
      ImportGui.insert(file_path, self.project_name)

      # Get the refecnde to the latest import object
      new_object_list = App.ActiveDocument.Objects
      new_items = [part for part in new_object_list if part not in old_object_list]
      for item in new_items:
        if not item.Parents:
            item.Placement=App.Placement(position, rotation, App.Vector(0,0,0))
            #item.ViewObject.DisplayMode = 1
            self.parts_in_assembly_step.append(item)
            if len(self.parts_in_assembly_step) == 1:
               Gui.SendMsgToActiveView("ViewFit")
            return item

    # Change camera view
    # You can get these values by using:
    # Gui.ActiveDocument.ActiveView.getCameraNode().orientation.getValue().getValue()
    def toggleView(self):

     if self.topView:
      Gui.ActiveDocument.ActiveView.getCameraNode().orientation = coin.SbRotation((-0.8310316205024719, -0.22975212335586548, 0.3825218379497528, -0.33208033442497253))
     else:
      Gui.ActiveDocument.ActiveView.getCameraNode().orientation = coin.SbRotation((-0.3320808410644531, 0.3825216293334961, 0.2297523319721222, 0.8310315608978271))

     Gui.SendMsgToActiveView("ViewFit")
     #Gui.ActiveDocument.ActiveView.getCameraNode().position = coin.SbVec3f((41.63908767700195, 30.38764190673828, 42.459869384765625))
     self.topView = not self.topView

     # Save image
     #toggle_image.Visibility = True
     save_image(True)
     #toggle_image.Visibility = False

    ## Close the document, and optionally save step-file
    def close(self, export=False):
        if export:
            objects = self.doc.RootObjects
            ImportGui.export(objects, str(CWD_PATH / "build" / MIRTE / (self.project_name + ".step")))
        App.closeDocument(self.doc.Name)

    def addWarning(self, type):
        global warning
        warning = type

    def addStep(self, step):
       step.execute()

    def save_image_new_parts(self):
      global step_id, image_id, warning
      if self.including_parts:
        part_id = 0
        for part in self.parts_in_assembly_step:
          part_doc = App.newDocument("Part")
          App.setActiveDocument(part_doc.Name)
          App.getDocument('Part').copyObject(self.doc.getObject(part.Name), True)
          obj = App.getDocument('Part').getObject(part.Name)
          Gui.ActiveDocument.ActiveView.getCameraNode().orientation = coin.SbRotation((-0.3320808410644531, 0.3825216293334961, 0.2297523319721222, 0.8310315608978271))
          Gui.SendMsgToActiveView("ViewFit")
          save_image(part_id = part_id)
          part_id += 1
          App.setActiveDocument(self.doc.Name)
          App.closeDocument("Part")

        self.parts_in_assembly_step.clear()
      step_id += 1
      image_id = 0
      warning = ""
