For running the python alarm clock application on windows, you have to install Gtk for windows which needs "msys2" and some other dependencies. 
The Gtk webpage describes the installation procedure for Gtk: https://www.gtk.org/download/windows.php

1. The installation package can be found on the page http://www.msys2.org/ . For a 64 bit windows installation:

http://repo.msys2.org/distrib/x86_64/msys2-x86_64-20161025.exe

2. After msys2 is installed you have to install the following packages with pacman:

pacman -S mingw-w64-x86_64-gtk3
pacman -S mingw-w64-x86_64-python2-gobject

3. Copy the files from the "usr" directory in the msys2 root directory (the standard is C:\msys64).

4. Add the binary directory "C:\msys64\usr\bin" and "C:\msys64\mingw64\bin" to the PATH environment variable.

5. Now you can start pytalarm by clicking on the shortcut pytalarm.lnk
