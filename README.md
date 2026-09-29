# HxC Floppy Emulator (USB) on Linux

Installer for the [HxC Floppy Emulator](https://hxc2001.com) software on Ubuntu / Xubuntu (and other Debian-based distros) for the **USB HxC Floppy Emulator**.

The official download only ships Windows and macOS binaries, so this builds the software from source and sets up USB access.

## What `install.sh` does

1. Installs build dependencies with `apt` (needs `sudo`).
2. Clones [racarla96/HxCFloppyEmulator](https://github.com/racarla96/HxCFloppyEmulator) (branch `linux-ftdi-more-pids`) into `./src`.
3. Builds the GUI (`hxcfloppyemulator`) and the command-line tool (`hxcfe`). FLTK is downloaded and built automatically.
4. Installs to `~/.local/opt/hxcfloppyemulator`, with launchers in `~/.local/bin` and a menu entry for Xfce/GNOME.
5. Links `libftdi.so` to `libftdi1.so.2`: the software loads `libftdi.so`, which current distros do not ship.
6. Installs a udev rule (`99-hxc-usb.rules`) so the FTDI device can be used without root (needs `sudo`).

## Install

```sh
git clone https://github.com/Proyecto-Futuro/Floppy_Emulator_USB_HxC2001.git
cd Floppy_Emulator_USB_HxC2001
./install.sh
```

`install.sh` is self-contained: you can also copy just that file to another machine and run it.

Then unplug and reconnect the HxC, log out and in if `~/.local/bin` is not in your `PATH`, and run:

```sh
hxcfloppyemulator
```

The log should show **"USB HxC Floppy Emulator ready!"**.

## The FTDI patch

Upstream only opens the FTDI chip `0403:6001` on Linux. A USB HxC built around another chip (mine is an FT240X, `0403:6015`) is reported as "not detected". The fork adds `6015`, `6014`, `6010` and `6011` to the list. Upstream PR: [jfdelnero/HxCFloppyEmulator#50](https://github.com/jfdelnero/HxCFloppyEmulator/pull/50). Once it is merged, `install.sh` can clone upstream directly.

## Loading files to the ABB S4 robot

The S4 reads a FAT12 floppy. `abb_disk.py` (Python 3, needs `dosfstools` and `mtools`, both installed by `install.sh`) turns a folder into a floppy image and sends it to the HxC:

```sh
./abb_disk.py send  my_program/            # build 1.44 MB image from the folder and load it in the HxC
./abb_disk.py build my_program/ -o disk.img  # only build the image
./abb_disk.py load  disk.img               # send an existing image
./abb_disk.py list  disk.img               # list its contents
./abb_disk.py pull  disk.img backup/       # extract files (e.g. an image made by a Gotek/HxC SD or a USB floppy drive)
```

- The HxC emulates the floppy while `send`/`load` is running; type `q` + Enter to stop.
- Use 8.3 file names (`MAIN.MOD`, `PROG1.PRG`); the script warns otherwise.
- Files are put in the disk root. Subfolders are copied too, but the S4 expects a flat disk.
- Disks are always 1.44 MB (HD). The drive's select jumper must match the HxC (`--drive N`).
- The USB HxC is **read-only**: the library has no way to capture what the robot writes (`libusbhxcfe` only streams tracks to the emulator), so `send` cannot be used to save robot backups. Use a real USB floppy drive, or an emulator that writes to storage (HxC SD, Gotek with FlashFloppy), and then `pull` the resulting image.

## Troubleshooting

- **"USB HxC Floppy Emulator not detected!"**: check `lsusb | grep 0403` shows the device, that the udev rule is installed (`ls /etc/udev/rules.d/99-hxc-usb.rules`), and reconnect the HxC after installing it.
- **`libftdi.so not found`** in the log: `ls -l ~/.local/opt/hxcfloppyemulator/libftdi.so` must point to an existing `libftdi1.so.2` (`sudo apt install libftdi1-2`).

## Manual

The software manual is the official one from [hxc2001.com](https://hxc2001.com); it is not redistributed here.
