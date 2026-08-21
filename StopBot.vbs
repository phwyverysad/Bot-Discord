Option Explicit

Const HIDDEN_MODE = 0

Dim WshShell, FSO, objWMIService, colProcesses
Dim ScriptPath, Choice, PromptText

Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

ScriptPath = FSO.GetParentFolderName(WScript.ScriptFullName)

Sub ShowWindowsToast(Title, Message)
    Dim psCmd
    psCmd = "powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command " & _
            """Add-Type -AssemblyName System.Windows.Forms; " & _
            "$notify = New-Object System.Windows.Forms.NotifyIcon; " & _
            "$notify.Icon = [System.Drawing.SystemIcons]::Information; " & _
            "$notify.Visible = $True; " & _
            "$notify.ShowBalloonTip(3500, '" & Replace(Title, "'", "''") & "', '" & Replace(Message, "'", "''") & "', [System.Windows.Forms.ToolTipIcon]::Info); " & _
            "Start-Sleep -Seconds 4; " & _
            "$notify.Dispose()"""
    WshShell.Run psCmd, HIDDEN_MODE, False
End Sub

Function StopAllDiscordBots()
    Dim process, cmdLine, pids, pidArray, pid
    Dim killedCount, killCmd
    killedCount = 0
    pids = ""
    
    On Error Resume Next
    Set objWMIService = GetObject("winmgmts://./root/cimv2")
    Set colProcesses = objWMIService.ExecQuery("SELECT * FROM Win32_Process WHERE Name='python.exe' OR Name='pythonw.exe'")
    
    For Each process In colProcesses
        cmdLine = process.CommandLine
        If InStr(1, cmdLine, "bothistory.py", vbTextCompare) > 0 Or _
           InStr(1, cmdLine, "copy discord", vbTextCompare) > 0 Or _
           InStr(1, cmdLine, "บอทไว้ยืงดิส", vbTextCompare) > 0 Or _
           InStr(1, cmdLine, ScriptPath, vbTextCompare) > 0 Then
            If pids = "" Then
                pids = CStr(process.ProcessId)
            Else
                pids = pids & "," & CStr(process.ProcessId)
            End If
        End If
    Next
    On Error GoTo 0
    
    If pids = "" Then
        StopAllDiscordBots = 0
        Exit Function
    End If
    
    pidArray = Split(pids, ",")
    For Each pid In pidArray
        If Trim(pid) <> "" Then
            killCmd = "taskkill /PID " & Trim(pid) & " /F"
            On Error Resume Next
            WshShell.Run killCmd, HIDDEN_MODE, True
            If Err.Number = 0 Then
                killedCount = killedCount + 1
            End If
            On Error GoTo 0
        End If
    Next
    
    StopAllDiscordBots = killedCount
End Function

' === Main Execution ===
PromptText = "==========================================" & vbCrLf & _
             "        DISCORD BOT MASTER STOPPER        " & vbCrLf & _
             "==========================================" & vbCrLf & vbCrLf & _
             "เลือกการทำงานในการปิดบอท:" & vbCrLf & vbCrLf & _
             " [1]  ปิดบอททั้งหมดในระบบ (Stop All Discord Bots)" & vbCrLf & _
             " [2]  ปิดเฉพาะบอท เช็คสถานะ" & vbCrLf & _
             " [3]  ปิดเฉพาะบอท copy discord" & vbCrLf & _
             " [4]  ปิดเฉพาะบอท บอทไว้ยืงดิส" & vbCrLf & vbCrLf & _
             "กด Cancel หรือใส่ [0] เพื่อยกเลิก"

Choice = InputBox(PromptText, "Discord Bot Master Stopper", "1")

If Choice = "" Or Choice = "0" Then
    WScript.Quit 0
End If

Select Case Trim(Choice)
    Case "1"
        Dim totalKilled
        totalKilled = StopAllDiscordBots()
        If totalKilled > 0 Then
            ShowWindowsToast "Discord Bot Master", "ปิดบอททั้งหมดเรียบร้อยแล้ว (" & totalKilled & " processes stopped)"
        Else
            ShowWindowsToast "Discord Bot Master", "ไม่พบบอทที่กำลังทำงานอยู่ในระบบ"
        End If
    Case "2"
        WshShell.Run "wscript.exe """ & ScriptPath & "\เช็คสถานะ\StopBot.vbs""", 0, False
    Case "3"
        WshShell.Run "wscript.exe """ & ScriptPath & "\copy discord\StopBot.vbs""", 0, False
    Case "4"
        WshShell.Run "wscript.exe """ & ScriptPath & "\บอทไว้ยืงดิส\StopBot.vbs""", 0, False
    Case Else
        MsgBox "หมายเลขไม่ถูกต้อง กรุณาระบุ 1, 2, 3 หรือ 4", vbExclamation, "Discord Bot Stopper"
End Select

Set WshShell = Nothing
Set FSO = Nothing
Set objWMIService = Nothing
