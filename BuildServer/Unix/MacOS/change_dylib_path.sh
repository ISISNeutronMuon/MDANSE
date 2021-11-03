#!/bin/bash

cd "$GITHUB_WORKSPACE/temp/dist/MDANSE.app/Contents/Frameworks/"
files=(libwx*.dylib)

libs="osx_cocoau_xrc osx_cocoau_webview osx_cocoau_html osx_cocoau_qa osx_cocoau_adv osx_cocoau_core baseu_xml baseu_net baseu"
echo "Changing links inside Frameworks"
for f in ${files[*]}
do
    sudo chmod 777 $f
    sudo install_name_tool -change /usr/lib/liconv.2.dylib @executable_path/../Frameworks/liconv.2.dylib $f
    for l in $libs
    do
        sudo install_name_tool -change /usr/local/lib/libwx_$l-3.0.dylib @executable_path/../Frameworks/libwx_$l-3.0.dylib $f
    done
done

echo "Changing wx links inside lib-dynload"
cd ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/lib-dynload/wx
files=(libwx*.dylib)
for f in ${files[*]}
do
  sudo install_name_tool -change @rpath/libz.1.dylib @executable_path/../Frameworks/libz.1.dylib $f
  sudo install_name_tool -change @rpath/libiconv.2.dylib @executable_path/../Frameworks/libiconv.2.dylib $f
  sudo install_name_tool -change @rpath/libc++.1.dylib @executable_path/../Frameworks/libc++.1.dylib $f
done

echo "Changing vtk links inside lib-dynload"
cd ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/lib-dynload/vtk
sos=(vtk*.so)
dylibs=($GITHUB_WORKSPACE/temp/dist/MDANSE.app/Contents/Frameworks/libvtk*.dylib)
for s in ${sos[*]}
do
  for d in ${dylibs[*]}
  do
    sudo install_name_tool -change @rpath/$d @executable_path/../Frameworks/$d $s
    # sudo install_name_tool -change /usr/lib/libstdc++.6.dylib @executable_path/../Frameworks/libiconv.2.dylib $s
  done
done


cd $GITHUB_WORKSPACE