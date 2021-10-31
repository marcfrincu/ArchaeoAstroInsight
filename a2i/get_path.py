from inspect import getsourcefile
from os.path import abspath, join
from qgis.core import QgsSettings
import sys

s = QgsSettings()
path = s.value("pythonConsole/lastDirPath")

path = path[:-12]

script_path = join(path, "Archaeo-Astro Insight" + "." + "py")
print(script_path)

line = "SCRIPT_PATH = " + '"' + path + '"'

outstr = ''
for character in line:
    if character == "\\":
        outstr = outstr + "/"
    else:
        outstr = outstr + character

print(outstr)

with open(script_path, 'r+') as f:
    f.readline()
    content = f.read()
    f.seek(0, 0)
    f.write(outstr.rstrip('\r\n') + '\n' + content)