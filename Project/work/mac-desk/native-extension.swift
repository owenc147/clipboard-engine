extension AppDelegate {
    @objc func showDesk() { web.evaluateJavaScript("setView('desk')", completionHandler:nil) }
    @objc func deskWake(_ notification: Notification) { runDesk(["op":"refresh"]) }
    func runDesk(_ request:[String:Any]) {
        guard !deskBusy,!context.isEmpty else { return }
        deskBusy=true
        let user=activeUser
        var payload=request;payload["context"]=context
        send("receiveDesk",["busy":true,"status":request["op"] as? String == "refresh" ? "Refreshing roster, status and market feeds…" : "Opening your saved desk…"])
        DispatchQueue.global(qos:.utility).async {
            var result:[String:Any]
            do {
                let task=Process();task.executableURL=URL(fileURLWithPath:"/usr/bin/python3");task.arguments=[Bundle.main.path(forResource:"desk",ofType:"py")!,self.support.path]
                var env=ProcessInfo.processInfo.environment;env["PYTHONDONTWRITEBYTECODE"]="1";task.environment=env
                let input=Pipe(),output=Pipe();task.standardInput=input;task.standardOutput=output;task.standardError=FileHandle.nullDevice
                self.deskProcess=task;try task.run()
                try input.fileHandleForWriting.write(contentsOf:JSONSerialization.data(withJSONObject:payload));try input.fileHandleForWriting.close()
                let data=output.fileHandleForReading.readDataToEndOfFile();task.waitUntilExit()
                result=(try JSONSerialization.jsonObject(with:data)) as? [String:Any] ?? ["ok":false,"status":"Could not read desk data."]
            } catch { result=["ok":false,"status":"Desk unavailable: \(error.localizedDescription). Saved data retained."] }
            DispatchQueue.main.async {
                self.deskBusy=false;self.deskProcess=nil
                guard self.activeUser==user else {self.runDesk(["op":"load"]);return}
                result["busy"]=false
                result["saved"]=(request["op"] as? String == "offer" && result["ok"] as? Bool == true)
                if let path=result["export_path"] as? String {self.deskExportURL=URL(fileURLWithPath:path)}
                if let alerts=result["new_alerts"] as? [[String:Any]], !alerts.isEmpty {NSApp.dockTile.badgeLabel=String(alerts.count)}
                self.send("receiveDesk",result)
                if request["op"] as? String == "load" {self.runDesk(["op":"refresh"])}
            }
        }
    }
    func exportDesk() {
        guard let source=deskExportURL else {send("receiveDesk",["status":"Open Manager desk and refresh before exporting."]);return}
        let panel=NSSavePanel();panel.nameFieldStringValue="binocular-export.json"
        panel.beginSheetModal(for:window){ response in
            guard response == .OK,let target=panel.url else{return}
            do {try Data(contentsOf:source).write(to:target,options:.atomic);self.send("receiveDesk",["status":"JSON snapshot exported."])}
            catch {self.send("receiveDesk",["status":"Export failed: \(error.localizedDescription)"])}
        }
    }
}
