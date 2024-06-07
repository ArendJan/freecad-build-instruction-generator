Installation
============

Open FreeCAD and the Python console (View > Panels > Python console). In the pytohn console:

> import os
> import sys
> import subprocess
> from pathlib import Path
>
> os.chdir('<freecad-build-instruction-generator directory')
> subprocess.check_call([(Path(sys.executable) / "../python").resolve() , "-m", "pip", "install", "."])

To check if this is installed correctly. The following should work:

> from freecad_build_instruction_generator import instruction_generator as gen
