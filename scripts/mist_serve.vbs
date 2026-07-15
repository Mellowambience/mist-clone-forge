' Fully detached MIST mesh server (survives terminal close)
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
' 0 = hidden window, False = do not wait
sh.CurrentDirectory = dir
' Prefer pythonw so no console is required; fall back to python
cmd = "pythonw -u mist_serve.py"
sh.Run cmd, 0, False
