#!/bin/sh

cd ../Tests/
coverage run --source=../Src/ ../Tests/AllTests.py
coverage html --omit=../Src/Externals/*,../Src/GUI/*,../Src/Framework/Plugins/*,../Src/Framework/ConfiguratorWidgets/*
