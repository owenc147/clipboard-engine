import Cocoa
import WebKit
import Security

class AppDelegate: NSObject, NSApplicationDelegate, WKScriptMessageHandler, WKNavigationDelegate {
    var window: NSWindow!
    var web: WKWebView!
    var report = ""
    var context: [String: Any] = [:]
    var busy = false
    var deskTimer: Timer?
    var deskBusy=false
    var deskProcess:Process?
    var deskExportURL:URL?
    var editionTimer: Timer?
    var lastEditionData: Data?
    var activeUser = UserDefaults.standard.string(forKey:"activeSleeperUser") ?? "coffero"
    var mailBusy = false
    var process: Process?
    let support = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0].appendingPathComponent("Sleeper Brief")
    func applicationDidFinishLaunching(_ notification: Notification) {
        let menu = NSMenu()
        let item = NSMenuItem()
        menu.addItem(item)
        let appMenu = NSMenu()
        appMenu.addItem(withTitle: "Quit Clipboard", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        item.submenu = appMenu
        let edit = NSMenuItem(); menu.addItem(edit); edit.submenu = NSMenu(title: "Edit")
        edit.submenu?.addItem(withTitle: "Copy", action: #selector(NSText.copy(_:)), keyEquivalent: "c")
        edit.submenu?.addItem(withTitle: "Paste", action: #selector(NSText.paste(_:)), keyEquivalent: "v")
        edit.submenu?.addItem(withTitle: "Select All", action: #selector(NSText.selectAll(_:)), keyEquivalent: "a")
        let view = NSMenuItem(); menu.addItem(view); view.submenu = NSMenu(title: "View")
        for (title, action, key) in [("Refresh League Data", #selector(refreshData), "r"), ("Show Game Plan", #selector(showPlan), "1"), ("Show Scouting Report", #selector(showResearch), "2"), ("Show Lineup Suggestions", #selector(showLineup), "3"), ("Show League Radar", #selector(showRadar), "4"), ("Show Suggestions", #selector(showSuggestions), "5"), ("Show Player Moves", #selector(showMoves), "6"), ("Show Manager Desk", #selector(showDesk), "7"), ("Toggle Sidebar", #selector(toggleSidebar), "s"), ("Zoom In", #selector(zoomIn), "+"), ("Zoom Out", #selector(zoomOut), "-"), ("Actual Size", #selector(resetZoom), "0")] {
            let entry = view.submenu!.addItem(withTitle: title, action: action, keyEquivalent: key)
            entry.target = self
            if title == "Toggle Sidebar" { entry.keyEquivalentModifierMask = [.command, .control] }
        }
        NSApp.mainMenu = menu
        if let iconURL = Bundle.main.url(forResource: "BinocularStadium", withExtension: "icns") { NSApp.applicationIconImage = NSImage(contentsOf: iconURL) }
        try? FileManager.default.createDirectory(at: support, withIntermediateDirectories: true)
        if activeUser.range(of:"^[A-Za-z0-9_-]+$",options:.regularExpression)==nil { activeUser="coffero" }
        let saved=profileFolder(activeUser).appendingPathComponent("snapshot.json")
        var snapshotURL=saved
        if !FileManager.default.fileExists(atPath:saved.path), activeUser=="coffero" {
            let legacy=support.appendingPathComponent("snapshot.json")
            snapshotURL=FileManager.default.fileExists(atPath:legacy.path) ? legacy : Bundle.main.url(forResource:"initial-snapshot",withExtension:"json")!
        }
        if let data=try? Data(contentsOf:snapshotURL),let snapshot=(try? JSONSerialization.jsonObject(with:data)) as? [String:Any],let savedContext=snapshot["context"] as? [String:Any],(savedContext["user"] as? String)?.lowercased()==activeUser.lowercased() {
            report=snapshot["text"] as? String ?? "";context=savedContext
        }
        let config = WKWebViewConfiguration()
        config.userContentController.add(self, name: "app")
        web = WKWebView(frame: .zero, configuration: config)
        web.navigationDelegate = self
        window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 1180, height: 820), styleMask: [.titled, .closable, .miniaturizable, .resizable], backing: .buffered, defer: false)
        window.title = "Clipboard"
        window.minSize = NSSize(width: 780, height: 550)
        window.contentView = web
        window.center()
        web.loadFileURL(Bundle.main.url(forResource: "index", withExtension: "html")!, allowingReadAccessTo: Bundle.main.resourceURL!)
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }
    @objc func refreshData() { web.evaluateJavaScript("send('refresh')", completionHandler: nil) }
    @objc func showPlan() { web.evaluateJavaScript("setView('overview')", completionHandler: nil) }
    @objc func showResearch() { web.evaluateJavaScript("setView('research')", completionHandler: nil) }
    @objc func showLineup() { web.evaluateJavaScript("setView('lineup')", completionHandler: nil) }
    @objc func showRadar() { web.evaluateJavaScript("setView('radar')", completionHandler: nil) }
    @objc func showMoves() { web.evaluateJavaScript("setView('moves')", completionHandler: nil) }
    @objc func showSuggestions() { web.evaluateJavaScript("setView('suggestions')", completionHandler: nil) }
    @objc func toggleSidebar() { web.evaluateJavaScript("toggleSidebar()", completionHandler: nil) }
    @objc func zoomIn() { web.pageZoom = min(1.6, web.pageZoom + 0.1) }
    @objc func zoomOut() { web.pageZoom = max(0.8, web.pageZoom - 0.1) }
    @objc func resetZoom() { web.pageZoom = 1 }
    func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        guard let url = navigationAction.request.url else { decisionHandler(.cancel); return }
        if url.isFileURL, url.standardizedFileURL.path.hasPrefix(Bundle.main.resourceURL!.standardizedFileURL.path + "/") { decisionHandler(.allow); return }
        if navigationAction.navigationType == .linkActivated, url.scheme == "https" { NSWorkspace.shared.open(url) }
        decisionHandler(.cancel)
    }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
    func applicationWillTerminate(_ notification: Notification) { process?.terminate(); deskProcess?.terminate(); deskTimer?.invalidate() }
    func send(_ name: String, _ object: [String: Any]) {
        guard let data = try? JSONSerialization.data(withJSONObject: object), let json = String(data: data, encoding: .utf8) else { return }
        web.evaluateJavaScript("window.\(name)(\(json))", completionHandler: nil)
    }
    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        send("receive", ["text":report, "context":context, "status":"Saved league data · refresh for the latest roster"])
        lastEditionData=nil; loadDailyEdition()
        runDesk(["op":"load"])
        deskTimer?.invalidate()
        deskTimer=Timer.scheduledTimer(withTimeInterval:300,repeats:true){[weak self] _ in self?.runDesk(["op":"refresh"])}
        NSWorkspace.shared.notificationCenter.addObserver(self,selector:#selector(deskWake(_:)),name:NSWorkspace.didWakeNotification,object:nil)
        editionTimer?.invalidate()
        editionTimer=Timer.scheduledTimer(withTimeInterval:60,repeats:true){ [weak self] _ in self?.loadDailyEdition() }
    }
    func profileFolder(_ user:String) -> URL {
        let folder=support.appendingPathComponent("profiles").appendingPathComponent(user.lowercased())
        try? FileManager.default.createDirectory(at:folder,withIntermediateDirectories:true)
        return folder
    }
    func loadDailyEdition() {
        guard !busy else { return }
        let url=Bundle.main.bundleURL.deletingLastPathComponent().appendingPathComponent("daily-edition.json")
        guard let data=try? Data(contentsOf:url), data != lastEditionData,
              let edition=(try? JSONSerialization.jsonObject(with:data)) as? [String:Any],
              let research=edition["research"] as? [String:Any], research["leagues"] != nil,
              let snapshot=edition["snapshot"] as? [String:Any],
              let latest=snapshot["context"] as? [String:Any], let text=snapshot["text"] as? String,
              (research["user"] as? String)?.lowercased()==activeUser.lowercased(),
              (latest["user"] as? String)?.lowercased()==activeUser.lowercased() else { return }
        lastEditionData=data
        if (latest["fetched_at"] as? String ?? "") > (context["fetched_at"] as? String ?? "") {
            context=latest; report=text
        }
        send("receiveEdition",edition)
    }
    var suggestionFile: URL { activeUser=="coffero" ? support.appendingPathComponent("suggestions.json") : profileFolder(activeUser).appendingPathComponent("suggestions.json") }
    func suggestionItems() -> [[String: String]] {
        guard let data = try? Data(contentsOf: suggestionFile), let items = try? JSONDecoder().decode([[String:String]].self, from: data) else { return [] }
        return items
    }
    func loadSuggestions(status: String = "", saved: Bool = false) {
        send("receiveSuggestions", ["items":suggestionItems(), "email":suggestionRecipient, "mode":activeUser != "coffero" ? "local" : hasGmail() ? "automatic" : "unconfigured", "status":status, "saved":saved])
    }
    func saveSuggestion(_ body: [String:String]) {
        guard !mailBusy else { return }
        let text = (body["text"] ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty, text.count <= 4000 else { loadSuggestions(status:"Enter a suggestion of up to 4,000 characters."); return }
        let category = ["Idea","Bug","Football research","Design"].contains(body["category"] ?? "") ? body["category"]! : "Idea"
        let item = ["id":UUID().uuidString, "text":text, "category":category, "created":ISO8601DateFormatter().string(from:Date()), "status":"Saved locally · email setup pending"]
        var items = suggestionItems(); items.insert(item,at:0)
        do { try JSONEncoder().encode(items).write(to:suggestionFile,options:.atomic); loadSuggestions(status:hasGmail() ? "Saved. Sending…" : (activeUser=="coffero" ? "Saved locally. Connect Gmail to enable automatic email." : "Saved to this Sleeper profile on this Mac. Email delivery is not configured for this profile."),saved:true); if hasGmail() { sendSavedSuggestion(id:item["id"]!) } }
        catch { loadSuggestions(status:"Could not save the suggestion. Your draft has been kept.") }
    }
    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        guard let body = message.body as? [String: String], let action = body["action"] else { return }
        if action == "desk", let raw=body["payload"],let data=raw.data(using:.utf8),let request=(try? JSONSerialization.jsonObject(with:data)) as? [String:Any] {
            runDesk(request)
        } else if action == "deskExport" {
            exportDesk()
        } else if action == "suggestionConfigure" {
            configureGmail()
        } else if action == "suggestionRetry" {
            sendSavedSuggestion(id:body["id"] ?? "")
        } else if action == "suggestionLoad" {
            loadSuggestions()
        } else if action == "suggestionSubmit" {
            saveSuggestion(body)
        } else if action == "copy" {
            NSPasteboard.general.clearContents(); NSPasteboard.general.setString(report, forType: .string)
            send("notice", ["status":"Brief copied to clipboard"])
        } else if action == "save" {
            let panel = NSSavePanel(); panel.nameFieldStringValue = "sleeper_brief.md"
            panel.beginSheetModal(for: window) { result in
                if result == .OK, let url = panel.url {
                    do { try self.report.write(to: url, atomically: true, encoding: .utf8); self.send("notice", ["status":"Brief saved"]) }
                    catch { self.send("notice", ["status":"Could not save: \(error.localizedDescription)"]) }
                }
            }
        } else if action == "refresh" && !busy && !mailBusy {
            let user = (body["user"] ?? "coffero").trimmingCharacters(in: .whitespacesAndNewlines)
            guard !user.isEmpty, user.range(of: "^[A-Za-z0-9_-]+$", options: .regularExpression) != nil else { send("notice", ["status":"Enter a valid Sleeper username"]); return }
            var args = [Bundle.main.path(forResource: "sleeper_assistant", ofType: "py")!, "--user", user]
            if let week = body["week"], !week.isEmpty {
                guard let n = Int(week), (1...18).contains(n) else { send("notice", ["status":"Week must be between 1 and 18"]); return }
                args += ["--week", week]
            }
            busy = true; send("notice", ["status":"Fetching leagues and player data…", "busy":true])
            DispatchQueue.global(qos: .userInitiated).async {
                let job = self.support.appendingPathComponent(UUID().uuidString)
                do {
                    try FileManager.default.createDirectory(at: job, withIntermediateDirectories: true)
                    defer { try? FileManager.default.removeItem(at: job) }
                    let task = Process(); task.executableURL = URL(fileURLWithPath: "/usr/bin/python3"); task.arguments = args; task.currentDirectoryURL = job
                    var env = ProcessInfo.processInfo.environment; env["SLEEPER_CACHE"] = self.support.appendingPathComponent("cache").path; env["PYTHONDONTWRITEBYTECODE"] = "1"; task.environment = env
                    let pipe = Pipe(); task.standardOutput = pipe; task.standardError = pipe
                    self.process = task
                    try task.run()
                    let output = pipe.fileHandleForReading.readDataToEndOfFile(); task.waitUntilExit()
                    guard task.terminationStatus == 0 else { throw NSError(domain: "Sleeper", code: 1, userInfo: [NSLocalizedDescriptionKey: String(data: output, encoding: .utf8)?.components(separatedBy: "\n").filter { !$0.isEmpty }.last ?? "Refresh failed"]) }
                    let files = try FileManager.default.contentsOfDirectory(at: job, includingPropertiesForKeys: nil)
                    guard let file = files.first(where: { $0.pathExtension == "md" }) else { throw NSError(domain: "Sleeper", code: 2, userInfo: [NSLocalizedDescriptionKey:"No brief was generated"]) }
                    let text = try String(contentsOf: file, encoding: .utf8)
                    let snapshotData = try Data(contentsOf: job.appendingPathComponent("snapshot.json"))
                    let snapshot = try JSONSerialization.jsonObject(with: snapshotData) as? [String: Any]
                    let latestContext = snapshot?["context"] as? [String: Any] ?? [:]
                    try snapshotData.write(to: self.profileFolder(user).appendingPathComponent("snapshot.json"), options: .atomic)
                    DispatchQueue.main.async { self.activeUser=user.lowercased(); UserDefaults.standard.set(self.activeUser,forKey:"activeSleeperUser"); self.lastEditionData=nil; self.report = text; self.context = latestContext; self.busy = false; self.deskExportURL=nil; self.runDesk(["op":"load"]); self.loadSuggestions(); self.send("receive", ["text":text,"context":latestContext,"status":"League data updated \(DateFormatter.localizedString(from: Date(), dateStyle: .short, timeStyle: .short))", "busy":false]) }
                } catch { DispatchQueue.main.async { self.busy = false; self.send("notice", ["status":"Refresh failed. \(error.localizedDescription). Your saved brief is still available.","busy":false]) } }
            }
        }
    }
}

extension AppDelegate {
    var suggestionRecipient: String { "ofc14700@gmail.com" }
    var keychainQuery: [String: Any] { [kSecClass as String:kSecClassGenericPassword,kSecAttrService as String:"local.coffero.binocular.gmail",kSecAttrAccount as String:suggestionRecipient] }
    func gmailPassword() -> String? {
        var q=keychainQuery;q[kSecReturnData as String]=true;q[kSecMatchLimit as String]=kSecMatchLimitOne
        var result:CFTypeRef?;guard SecItemCopyMatching(q as CFDictionary,&result)==errSecSuccess,let data=result as? Data else{return nil}
        return String(data:data,encoding:.utf8)
    }
    func hasGmail() -> Bool { activeUser=="coffero" && UserDefaults.standard.bool(forKey:"gmailConnected") }
    func storeGmailPassword(_ password:String) -> Bool {
        let q=keychainQuery;let values=[kSecValueData as String:Data(password.utf8)]
        let status=SecItemUpdate(q as CFDictionary,values as CFDictionary)
        if status==errSecItemNotFound {var add=q;add[kSecValueData as String]=Data(password.utf8);add[kSecAttrAccessible as String]=kSecAttrAccessibleWhenUnlockedThisDeviceOnly;return SecItemAdd(add as CFDictionary,nil)==errSecSuccess}
        return status==errSecSuccess
    }
    func emailRequest(_ payload:[String:String]) -> [String:Any] {
        do {
            let task=Process();task.executableURL=URL(fileURLWithPath:"/usr/bin/python3");task.arguments=[Bundle.main.path(forResource:"send_suggestion",ofType:"py")!]
            let input=Pipe(),output=Pipe();task.standardInput=input;task.standardOutput=output;task.standardError=FileHandle.nullDevice
            try task.run();try input.fileHandleForWriting.write(contentsOf:JSONEncoder().encode(payload));try input.fileHandleForWriting.close()
            let data=output.fileHandleForReading.readDataToEndOfFile();task.waitUntilExit()
            return (try? JSONSerialization.jsonObject(with:data)) as? [String:Any] ?? ["ok":false,"status":"Email process stopped. Check your inbox before retrying."]
        } catch {return ["ok":false,"status":"Could not start email sending. Saved locally."]}
    }
    func configureGmail() {
        guard activeUser=="coffero" else { loadSuggestions(status:"Email delivery for additional profiles is not configured."); return }
        guard !mailBusy else { return }
        let alert=NSAlert();alert.messageText="Connect Gmail for suggestions"
        alert.informativeText="Send from and to ofc14700@gmail.com. Every subject will be BINOCULAR SUGGESTION. Enter a Gmail app password, not your regular password. Connect verifies it and stores it in this Mac’s Keychain. New suggestions will then send automatically. Existing saved suggestions can be sent individually."
        let field=NSSecureTextField(frame:NSRect(x:0,y:0,width:360,height:28));field.placeholderString="16-character Gmail app password";alert.accessoryView=field
        alert.addButton(withTitle:"Connect & save in Keychain");alert.addButton(withTitle:"Cancel");alert.addButton(withTitle:"Setup instructions")
        alert.beginSheetModal(for:window){ response in
            if response == .alertThirdButtonReturn {NSWorkspace.shared.open(URL(string:"https://support.google.com/accounts/answer/185833")!);return}
            guard response == .alertFirstButtonReturn else{return}
            let secret=field.stringValue.filter{ !$0.isWhitespace };field.stringValue=""
            guard secret.count==16 else{self.loadSuggestions(status:"Enter the 16-character app password from Google.");return}
            self.mailBusy=true
            self.send("suggestionProgress",["status":"Checking Gmail connection…"])
            DispatchQueue.global(qos:.userInitiated).async {
                let result=self.emailRequest(["mode":"verify","password":secret])
                DispatchQueue.main.async {
                    self.mailBusy=false
                    if result["ok"] as? Bool == true {
                        if self.storeGmailPassword(secret){UserDefaults.standard.set(true,forKey:"gmailConnected");self.loadSuggestions(status:"Gmail connected. New suggestions will email automatically.")}
                        else{self.loadSuggestions(status:"Gmail verified, but the password could not be saved in Keychain.")}
                    }else{self.loadSuggestions(status:result["status"] as? String ?? "Connection failed.")}
                }
            }
        }
    }
    func sendSavedSuggestion(id:String) {
        guard activeUser=="coffero",!mailBusy,let item=suggestionItems().first(where:{$0["id"]==id}),!(item["status"] ?? "").hasPrefix("Sent") else{return}
        guard let password=gmailPassword() else{loadSuggestions(status:"Connect Gmail to send this saved suggestion.");return}
        mailBusy=true;send("suggestionProgress",["status":"Sending suggestion…"])
        var payload=item;payload["password"]=password
        DispatchQueue.global(qos:.userInitiated).async {
            let result=self.emailRequest(payload)
            DispatchQueue.main.async {
                self.mailBusy=false
                var items=self.suggestionItems()
                if let index=items.firstIndex(where:{$0["id"]==id}){items[index]["status"]=result["status"] as? String ?? "Delivery not confirmed."}
                do{try JSONEncoder().encode(items).write(to:self.suggestionFile,options:.atomic);self.loadSuggestions(status:result["status"] as? String ?? "Delivery not confirmed.")}
                catch{self.loadSuggestions(status:"Email attempt finished, but its status could not be saved. Check your inbox before retrying.")}
            }
        }
    }
}

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

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.setActivationPolicy(.regular)
app.run()
