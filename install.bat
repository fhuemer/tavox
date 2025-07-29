@echo off
setlocal

set "LATEX_DIR=%CD%\latex"

:: -----------------------------
:: Check for MiKTeX (initexmf)
:: -----------------------------
where initexmf >nul 2>&1
if %ERRORLEVEL% equ 0 (
	echo MiKTeX installation found.
	echo Registering root directory with MiKTeX: %LATEX_DIR%
	initexmf --register-root="%LATEX_DIR%"
	if %ERRORLEVEL% equ 0 (
		echo MiKTeX registration successful.
	) else (
		echo MiKTeX failed to register the root directory.
	)
)

:: -----------------------------
:: Check for TeX Live (tlmgr)
:: -----------------------------
where tlmgr >nul 2>&1
if %ERRORLEVEL% equ 0 (
	echo TeX Live installation found.

	setlocal enabledelayedexpansion

	:: Get TEXMFHOME path using kpsewhich
	for /f "delims=" %%T in ('kpsewhich --var-value=TEXMFHOME') do set "TEXMFHOME=%%T"

	:: Sanitize path (remove quotes)
	set "TEXMFHOME=!TEXMFHOME:"=!"

	echo TEXMFHOME resolves to: !TEXMFHOME!

	set "TARGET_DIR=!TEXMFHOME!/tex/latex"

	if not exist "!TARGET_DIR!" (
		echo Directory does not exits. Creating it.
		mkdir "!TARGET_DIR!"
	)

	echo Copying tavox.sty
	copy "%LATEX_DIR%\tavox.sty" "!TARGET_DIR!/tavox.sty" >nul

	if %ERRORLEVEL% equ 0 (
		echo File copied successfully.
	) else (
		echo Failed to copy file.
	)

)

endlocal