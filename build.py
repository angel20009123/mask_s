"""Build the versioned Windows client with embedded product metadata."""
from pathlib import Path
import subprocess
import sys
from version import __version__

root = Path(__file__).resolve().parent
version_tuple = tuple(int(part) for part in __version__.split(".")) + (0,)
resource = root / "build" / "version-info.txt"
resource.parent.mkdir(exist_ok=True)
resource.write_text(f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers={version_tuple!r}, prodvers={version_tuple!r},
    mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[StringFileInfo([StringTable('040904B0', [
    StringStruct('CompanyName', 'Mask Studio'),
    StringStruct('FileDescription', 'IPv4 subnet and ACL wildcard calculator'),
    StringStruct('FileVersion', '{__version__}'),
    StringStruct('ProductName', 'Mask Studio'),
    StringStruct('ProductVersion', '{__version__}'),
    StringStruct('OriginalFilename', 'MaskStudio-v{__version__}.exe')
  ])]), VarFileInfo([VarStruct('Translation', [1033, 1200])])])
""", encoding="utf-8")
subprocess.run([
    sys.executable, "-m", "PyInstaller", "--noconfirm", "--onefile", "--windowed",
    "--name", f"MaskStudio-v{__version__}", "--icon", str(root / "assets/mask-studio.ico"),
    "--add-data", f"{root / 'assets'};assets", "--version-file", str(resource), str(root / "app.py"),
], cwd=root, check=True)
