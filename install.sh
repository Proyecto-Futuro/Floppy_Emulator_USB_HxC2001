#!/bin/bash
# Instalación del software HxC Floppy Emulator (USB) en Linux (Ubuntu/Debian), sin root salvo apt y udev.
# Autosuficiente: basta copiar solo este fichero. Uso: ./install.sh
# (clona el código en ./src junto al script)
set -e
PROJ="$(cd "$(dirname "$0")" && pwd)"
DEST="$HOME/.local/opt/hxcfloppyemulator"

# 1. Dependencias (requiere sudo)
sudo apt install -y build-essential git cmake pkg-config libusb-1.0-0-dev libftdi1-2 \
  libx11-dev libxft-dev libxinerama-dev libxcursor-dev libxfixes-dev libxrender-dev \
  libpango1.0-dev libcairo2-dev libwayland-dev libxkbcommon-dev libdbus-1-dev libpulse-dev
# libdecor solo existe en Ubuntu >= 24.04 (Xubuntu 24.04+); opcional
sudo apt install -y libdecor-0-dev || true

# 2. Código fuente (el zip de docs/ solo trae binarios de Windows/macOS)
# Fork con el parche de PIDs FTDI para Linux (PR jfdelnero/HxCFloppyEmulator#50)
[ -d "$PROJ/src" ] || git clone --branch linux-ftdi-more-pids https://github.com/racarla96/HxCFloppyEmulator.git "$PROJ/src"

# 3. Compilar (descarga y compila FLTK automáticamente)
make -C "$PROJ/src/build" -j"$(nproc)" HxCFloppyEmulator_cmdline HxCFloppyEmulator_software

# 4. Instalar en ~/.local
mkdir -p "$DEST" "$HOME/.local/bin"
B="$PROJ/src/build"
cp "$B/hxcfloppyemulator" "$B/hxcfe" "$B/libhxcfe.so" "$B/libusbhxcfe.so" "$DEST/"
# config.script (opcional): solo si está el zip de docs/
[ -f "$PROJ/docs/HxCFloppyEmulator_soft.zip" ] && unzip -o -j -q "$PROJ/docs/HxCFloppyEmulator_soft.zip" \
  'HxCFloppyEmulator_soft/HxCFloppyEmulator_Software/Windows_x64/config.script' -d "$DEST" || true
# En Linux el programa hace dlopen("libftdi.so"); Ubuntu solo trae libftdi1.so.2
ln -sf "$(ls /usr/lib/*/libftdi1.so.2 | head -1)" "$DEST/libftdi.so"
for b in hxcfloppyemulator hxcfe; do
  printf '#!/bin/sh\ncd "%s" && LD_LIBRARY_PATH="%s:$LD_LIBRARY_PATH" exec ./%s "$@"\n' "$DEST" "$DEST" "$b" > "$HOME/.local/bin/$b"
  chmod +x "$HOME/.local/bin/$b"
done

# Entrada en el menú de Xfce (Xubuntu)
mkdir -p "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/hxcfloppyemulator.desktop" <<D
[Desktop Entry]
Type=Application
Name=HxC Floppy Emulator
Exec=$HOME/.local/bin/hxcfloppyemulator
Terminal=false
Categories=Utility;
D

# 5. Permisos USB (requiere sudo)
sudo tee /etc/udev/rules.d/99-hxc-usb.rules >/dev/null <<'R'
# HxC Floppy Emulator USB (FTDI FT2232/FT232/FT245 based) - user access without root
SUBSYSTEM=="usb", ATTR{idVendor}=="0403", MODE="0666", GROUP="plugdev"
R
sudo udevadm control --reload && sudo udevadm trigger
echo "Listo. Si ~/.local/bin no está en el PATH, cierra sesión y vuelve a entrar (Xubuntu lo añade en el login). Reconecta el HxC y ejecuta: hxcfloppyemulator  (asegúrate de que ~/.local/bin está en el PATH)"
