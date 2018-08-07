@echo off

cd "%MDANSE_SOURCE_DIR%"

rem To understand this syntax "set cmd=...... for /F %%ii ......", see https://stackoverflow.com/questions/2323292/assign-output-of-a-program-to-a-variable

rem Update the __pkginfo__ file with the current commit
echo "Commit id %MDANSE_GIT_CURRENT_COMMIT%"
echo "Branch name %MDANSE_GIT_BRANCH_NAME%"
sed -i "s/.*__commit__.*/__commit__ = \"%MDANSE_GIT_CURRENT_COMMIT%\"/" Src/__pkginfo__.py

rem Get MDANSE version
set cmd="sed -n "s/__version__.*=.*\"\(.*\)\"/\1/p" Src/__pkginfo__.py"
for /F %%i in (' %cmd% ') do set MDANSE_VERSION=%%i

rem Check if branch is master, tag as draft otherwise
if "%MDANSE_GIT_BRANCH_NAME%" == "master" (
    set VERSION_NAME=%MDANSE_VERSION%
    sed -i "s/.*__beta__.*/__beta__ = None/" Src/__pkginfo__.py
) else (
    rem Check if branch is release*
    if "%MDANSE_GIT_BRANCH_NAME:~0,7%" == "release" (
        set VERSION_NAME=%MDANSE_VERSION%-rc-%MDANSE_GIT_CURRENT_COMMIT%
        sed -i "s/.*__beta__.*/__beta__ = \"rc\"/" Src/__pkginfo__.py
    ) else (
        set VERSION_NAME=%MDANSE_VERSION%-beta-%MDANSE_GIT_CURRENT_COMMIT%
        sed -i "s/.*__beta__.*/__beta__ = \"beta\"/" Src/__pkginfo__.py
    )
)
