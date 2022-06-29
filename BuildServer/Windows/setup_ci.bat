@echo off

rem Set the source directory
set MDANSE_SOURCE_DIR=%GITHUB_WORKSPACE%

rem Get revision number from Git
rem To understand this syntax "set cmd=...... for /F %%ii ......", see https://stackoverflow.com/questions/2323292/assign-output-of-a-program-to-a-variable
rem set cmd="git rev-parse --short HEAD"
rem for /F %%i in (' %cmd% ') do set MDANSE_GIT_CURRENT_COMMIT=%%i
set MDANSE_GIT_CURRENT_COMMIT=%GITHUB_SHA:~0,8%

rem Get commit branch from Gitlab
set MDANSE_GIT_BRANCH_NAME=%GITHUB_REF%

cd "%MDANSE_SOURCE_DIR%"

rem Update the __pkginfo__ file with the current commit
echo "Commit id %MDANSE_GIT_CURRENT_COMMIT%"
echo "Branch name %MDANSE_GIT_BRANCH_NAME%"
rem sed -i unfortunately creates backup file, see https://stackoverflow.com/questions/1823591/sed-creates-un-deleteable-files-in-windows
rem so we do not use the -i option
sed "s/.*__commit__.*/__commit__ = \"%MDANSE_GIT_CURRENT_COMMIT%\"/" Src\\__pkginfo__.py >> Src\\__pkginfo__.pybak
move /Y Src\\__pkginfo__.pybak Src\\__pkginfo__.py

rem Get MDANSE version
set cmd="sed -n "s/__version__.*=.*\"\(.*\)\"/\1/p" Src/__pkginfo__.py"
for /F %%i in (' %cmd% ') do set MDANSE_VERSION=%%i

rem Check if branch is main, tag as draft otherwise
if "%MDANSE_GIT_BRANCH_NAME%" == refs/heads/hotfix-windows-installer-version (
    set VERSION_NAME=%MDANSE_VERSION%
    sed "s/.*__beta__.*/__beta__ = None/" Src\\__pkginfo__.py >> Src\\__pkginfo__.pybak
    move /Y Src\\__pkginfo__.pybak Src\\__pkginfo__.py
) else (
    rem Check if branch is release*
    if "%MDANSE_GIT_BRANCH_NAME" == refs/heads/release-next (
        set VERSION_NAME=%MDANSE_VERSION%-rc-%MDANSE_GIT_CURRENT_COMMIT%
        sed "s/.*__beta__.*/__beta__ = \"rc\"/" Src\\__pkginfo__.py >> Src\\__pkginfo__.pybak
        move /Y Src\\__pkginfo__.pybak Src\\__pkginfo__.py
    ) else (
        set VERSION_NAME=%MDANSE_VERSION%-beta-%MDANSE_GIT_CURRENT_COMMIT%
        sed "s/.*__beta__.*/__beta__ = \"beta\"/" Src\\__pkginfo__.py >> Src\\__pkginfo__.pybak
        move /Y Src\\__pkginfo__.pybak Src\\__pkginfo__.py
    )
)
echo %VERSION_NAME%
