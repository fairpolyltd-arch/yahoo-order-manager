' Yahoo Mail Order Manager - Silent Launcher (No Command Prompt Window)
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = currentDir

' Run desktop control GUI with pythonw (completely invisible command prompt)
WshShell.Run "pythonw.exe desktop_app.py", 0, False
