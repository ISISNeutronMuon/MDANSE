#!/bin/bash
echo $GITHUB_WORKSPACE
echo "-------------------------------------"
files=("${MDANSE_APP_DIR}/Contents/Frameworks/libwx*.dylib")

echo "${files[@]}"
libs="osx_cocoau_xrc osx_cocoau_webview osx_cocoau_html osx_cocoau_qa osx_cocoau_adv osx_cocoau_core baseu_xml baseu_net baseu"

for f in "${files[@]}"
do
    sudo chmod 777 $f
    for l in $libs
    do
        sudo install_name_tool -change /usr/local/lib/libwx_$l-3.0.dylib @executable_path/../Frameworks/libwx_$l-3.0.dylib $f
    done
done