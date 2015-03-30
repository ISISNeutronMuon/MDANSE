#!/bin/sh

cd ../Tests/
coverage run --source=../MDANSE/ ../Tests/AllTests.py
coverage html --omit=../MDANSE/Externals/*,../MDANSE/GUI/*,../MDANSE/Framework/Plugins/*,../MDANSE/Framework/ConfiguratorWidgets/*
