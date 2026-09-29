#!/usr/bin/env python3
"""Carga el contenido de una carpeta en el HxC USB como disquete para un robot ABB S4.

Crea una imagen FAT12 (1.44 MB) con los archivos de la carpeta y,
opcionalmente, la envía al emulador con `hxcfe -usb`.

  abb_disk.py build  carpeta [-o disco.img] 
  abb_disk.py send   carpeta  [--drive 0]
  abb_disk.py load   disco.img [--drive 0]
  abb_disk.py list   disco.img
  abb_disk.py pull   disco.img carpeta_destino

Requiere: dosfstools (mkfs.vfat) y mtools (mcopy, mdir). Envío al HxC: hxcfe (install.sh).
"""
import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SIZE_KB = 1440
FAT_83 = re.compile(r"^[A-Za-z0-9_$~!#%&\-{}()@']{1,8}(\.[A-Za-z0-9_$~!#%&\-{}()@']{1,3})?$")


def die(msg):
    sys.exit(f"error: {msg}")


def need(tool, pkg):
    if not shutil.which(tool):
        die(f"falta '{tool}' (sudo apt install {pkg})")


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        die(f"{' '.join(map(str, cmd))}\n{r.stdout}{r.stderr}".strip())
    return r.stdout


def build_image(folder, img, size_kb=SIZE_KB, label="ABB"):
    need("mkfs.vfat", "dosfstools")
    need("mcopy", "mtools")
    folder = Path(folder)
    if not folder.is_dir():
        die(f"'{folder}' no es una carpeta")
    files = sorted(p for p in folder.iterdir() if not p.name.startswith("."))
    if not files:
        die(f"'{folder}' está vacía")
    total = sum(p.stat().st_size for p in files if p.is_file())
    if total > size_kb * 1024:
        die(f"el contenido ({total // 1024} KB) no cabe en {size_kb} KB")
    for p in files:
        if not FAT_83.match(p.name):
            print(f"aviso: '{p.name}' no es un nombre 8.3; el robot puede no verlo bien", file=sys.stderr)
    img = Path(img)
    img.unlink(missing_ok=True)
    run(["mkfs.vfat", "-C", "-F", "12", "-n", label, str(img), str(size_kb)])
    run(["mcopy", "-i", str(img), "-s", "-m", *map(str, files), "::"])
    print(f"{img}: {len(files)} elementos, {total // 1024} KB de {size_kb} KB")
    return img


def send_image(img, drive, ifmode=None):
    if not shutil.which("hxcfe"):
        die("no encuentro 'hxcfe' (ejecuta ./install.sh)")
    print(f"enviando {img} al HxC USB (escribe q + Enter para terminar la emulación)...")
    cmd = ["hxcfe", f"-finput:{Path(img).resolve()}", f"-usb:{drive}"]
    if ifmode:
        cmd.append(f"-ifmode:{ifmode}")
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        pass
    except subprocess.CalledProcessError as e:
        die(f"hxcfe terminó con código {e.returncode}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="crear imagen desde una carpeta")
    b.add_argument("folder")
    b.add_argument("-o", "--output", default="disco.img")
    s = sub.add_parser("send", help="crear imagen desde una carpeta y enviarla al HxC")
    s.add_argument("folder")
    s.add_argument("--drive", default="0")
    ld = sub.add_parser("load", help="enviar una imagen existente al HxC")
    ld.add_argument("image")
    ld.add_argument("--drive", default="0")
    ld.add_argument("--ifmode", help="modo de interfaz de hxcfe -interfacelist (defecto: automático)")
    ls = sub.add_parser("list", help="listar el contenido de una imagen")
    ls.add_argument("image")
    pl = sub.add_parser("pull", help="extraer los archivos de una imagen a una carpeta")
    pl.add_argument("image")
    pl.add_argument("folder")
    a = ap.parse_args()

    if a.cmd == "build":
        build_image(a.folder, a.output)
    elif a.cmd == "send":
        with tempfile.TemporaryDirectory() as tmp:
            img = build_image(a.folder, Path(tmp) / "disco.img")
            send_image(img, a.drive, "IBMPC_HD_FLOPPYMODE")
    elif a.cmd == "load":
        send_image(a.image, a.drive, a.ifmode)
    elif a.cmd == "list":
        need("mdir", "mtools")
        print(run(["mdir", "-/", "-i", a.image, "::"]), end="")
    elif a.cmd == "pull":
        need("mcopy", "mtools")
        Path(a.folder).mkdir(parents=True, exist_ok=True)
        run(["mcopy", "-i", a.image, "-s", "-n", "::*", a.folder])
        print(f"extraído en {a.folder}")


if __name__ == "__main__":
    main()
