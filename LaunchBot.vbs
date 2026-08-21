Option Explicit

Dim WshShell, FSO
Dim ScriptPath, Choice, PromptText

Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

ScriptPath = FSO.GetParentFolderName(WScript.ScriptFullName)

PromptText = "==========================================" & vbCrLf & _
             "        DISCORD BOT MASTER LAUNCHER       " & vbCrLf & _
             "==========================================" & vbCrLf & vbCrLf & _
             "กรุณาพิมพ์หมายเลขบอทที่ต้องการเปิดทำงาน (Background):" & vbCrLf & vbCrLf & _
             " [1]  เช็คสถานะ  (Status & Activity History Logger)" & vbCrLf & _
             " [2]  copy discord  (Server Cloner & Backup)" & vbCrLf & _
             " [3]  บอทไว้ยืงดิส  (Fast Server Reset)" & vbCrLf & _
             " [4]  เปิดใช้งานทั้งหมดพร้อมกัน (Launch All Bots)" & vbCrLf & vbCrLf & _
             "กด Cancel หรือใส่ [0] เพื่อยกเลิก"

Choice = InputBox(PromptText, "Discord Bot Master Launcher", "1")

If Choice = "" Or Choice = "0" Then
    WScript.Quit 0
End If

Select Case Trim(Choice)
    Case "1"
        WshShell.Run "wscript.exe """ & ScriptPath & "\เช็คสถานะ\LaunchBot.vbs""", 0, False
    Case "2"
        WshShell.Run "wscript.exe """ & ScriptPath & "\copy discord\LaunchBot.vbs""", 0, False
    Case "3"
        WshShell.Run "wscript.exe """ & ScriptPath & "\บอทไว้ยืงดิส\LaunchBot.vbs""", 0, False
    Case "4"
        WshShell.Run "wscript.exe """ & ScriptPath & "\เช็คสถานะ\LaunchBot.vbs""", 0, False
        WScript.Sleep 1000
        WshShell.Run "wscript.exe """ & ScriptPath & "\copy discord\LaunchBot.vbs""", 0, False
        WScript.Sleep 1000
        WshShell.Run "wscript.exe """ & ScriptPath & "\บอทไว้ยืงดิส\LaunchBot.vbs""", 0, False
    Case Else
        MsgBox "หมายเลขไม่ถูกต้อง กรุณาระบุ 1, 2, 3 หรือ 4", vbExclamation, "Discord Bot Launcher"
End Select

Set WshShell = Nothing
Set FSO = Nothing
