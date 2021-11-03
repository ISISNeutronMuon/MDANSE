#!/bin/bash

cd ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/site-packages/wx
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

files=(*.so)
for f in ${files[*]}
do
  sudo install_name_tool -add_rpath @executable_path/../Frameworks $f
done

cd "$GITHUB_WORKSPACE/temp/dist/MDANSE.app/Contents/Frameworks/"
echo "Changing zlib paths"
files=(libz*.dylib)
for f in ${files[*]}
do
  sudo install_name_tool -change /usr/lib/$f @executable_path/../Frameworks/$f $f
done

echo "Changing wx links inside lib-dynload"
cd ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/lib-dynload/wx
files=(libwx*.dylib)
for f in ${files[*]}
do
  sudo install_name_tool -add_rpath @executable_path/../Frameworks $f
done

echo "Changing vtk links inside lib-dynload"
cd ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/lib-dynload/vtk
files=(vtk*.so)
echo ${files[*]}
for f in ${files[*]}
do
  sudo install_name_tool -add_rpath @executable_path/../Frameworks $f
done

cd $GITHUB_WORKSPACE