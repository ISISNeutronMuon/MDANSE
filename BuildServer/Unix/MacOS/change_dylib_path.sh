#!/bin/bash

echo -e "${BLUE}" "Changing Frameworks/ wx dylibs""${NORMAL}"
cd ${MDANSE_APP_DIR}/Contents/Frameworks || exit
files=(libwx*.dylib)
libs="osx_cocoau_xrc osx_cocoau_webview osx_cocoau_html osx_cocoau_qa osx_cocoau_adv osx_cocoau_core baseu_xml baseu_net baseu"

echo ${files[*]}
for f in ${files[*]}
do
    sudo chmod 777 $f
    sudo install_name_tool -add_rpath @executable_path/../Frameworks $f
    for l in $libs
    do
        sudo install_name_tool -change /usr/local/lib/libwx_$l-3.0.dylib @executable_path/../Frameworks/libwx_$l-3.0.dylib $f
    done
done

echo -e "${BLUE}" "Changing site-packages/wx so files""${NORMAL}"
cd ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/site-packages/wx-3.0-osx_cocoa/wx || exit
files=(*.so)
echo ${files[*]}
for f in ${files[*]}
do
  sudo install_name_tool -add_rpath @executable_path/../Frameworks $f
done

echo -e "${BLUE}" "Changing lib-dynload/wx so files""${NORMAL}"
cd ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/lib-dynload/wx || exit
files=(*.so)
echo ${files[*]}
for f in ${files[*]}
do
  sudo install_name_tool -add_rpath @executable_path/../Frameworks $f
done

echo -e "${BLUE}" "Changing lib-dynload/wx dylib files""${NORMAL}"
files=(libwx*.dylib)
echo ${files[*]}
for f in ${files[*]}
do
  sudo install_name_tool -add_rpath @executable_path/../Frameworks $f
done

echo -e "${BLUE}" "Changing zlib paths""${NORMAL}"
cd "$GITHUB_WORKSPACE/temp/dist/MDANSE.app/Contents/Frameworks/" || exit
files=(libz*.dylib)
echo ${files[*]}
for f in ${files[*]}
do
  sudo install_name_tool -change /usr/lib/$f @executable_path/../Frameworks/$f $f
done

echo -e "${BLUE}" "Changing lib-dynload/vtk so files""${NORMAL}"
cd ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/lib-dynload/vtk || exit
files=(vtk*.so)
echo ${files[*]}
for f in ${files[*]}
do
  sudo install_name_tool -add_rpath @executable_path/../Frameworks $f
  sudo install_name_tool -change /usr/local/opt/gettext/lib/libintl.8.dylib @executable_path/../Frameworks/libintl.8.dylib $f
done

echo -e "${BLUE}" "Changing site-packages/vtk so files""${NORMAL}"
cd ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/site-packages/vtk || exit
files=(vtk*.so)
echo ${files[*]}
for f in ${files[*]}
do
  sudo install_name_tool -add_rpath @executable_path/../Frameworks $f
  sudo install_name_tool -change /usr/local/opt/gettext/lib/libintl.8.dylib @executable_path/../Frameworks/libintl.8.dylib $f
done

cd $GITHUB_WORKSPACE || exit