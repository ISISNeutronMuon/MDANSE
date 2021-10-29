#!/bin/bash
echo $GITHUB_WORKSPACE
echo "-------------------------------------"
ls /Users/runner/work/MDANSE/MDANSE/temp/dist/MDANSE.app/Contents/Frameworks/libwx*.dylib
echo "-------------------------------------"
files=("$GITHUB_WORKSPACE/temp/dist/MDANSE.app/Contents/Frameworks/libwx*.dylib")
echo "${files[@]}"
echo "-------------------------------------"
echo "${files[*]}"
echo "-------------------------------------"

libs="osx_cocoau_xrc osx_cocoau_webview osx_cocoau_html osx_cocoau_qa osx_cocoau_adv osx_cocoau_core baseu_xml baseu_net baseu"

for f in ${files[*]}
do
    echo $f
    sudo chmod 777 $f
    for l in $libs
    do
        echo $l
        sudo install_name_tool -change /usr/local/lib/libwx_$l-3.0.dylib @executable_path/../Frameworks/libwx_$l-3.0.dylib $f
    done
done