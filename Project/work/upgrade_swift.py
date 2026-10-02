from pathlib import Path
p=Path('work/App.swift');s=p.read_text()
s=s.replace('var report = ""','var report = ""\n    var context: [String: Any] = [:]')
s=s.replace('Quit Sleeper Brief','Quit Binocular').replace('window.title = "Sleeper Brief"','window.title = "Binocular"')
s=s.replace('        NSApp.mainMenu = menu','''        let view = NSMenuItem(); menu.addItem(view); view.submenu = NSMenu(title: "View")
        for (title, action, key) in [("Refresh League Data", #selector(refreshData), "r"), ("Show Game Plan", #selector(showPlan), "1"), ("Show Scouting Report", #selector(showResearch), "2"), ("Toggle Sidebar", #selector(toggleSidebar), "s"), ("Zoom In", #selector(zoomIn), "+"), ("Zoom Out", #selector(zoomOut), "-"), ("Actual Size", #selector(resetZoom), "0")] {
            let entry = view.submenu!.addItem(withTitle: title, action: action, keyEquivalent: key)
            entry.target = self
            if title == "Toggle Sidebar" { entry.keyEquivalentModifierMask = [.command, .control] }
        }
        NSApp.mainMenu = menu''')
a='''        let saved = support.appendingPathComponent("latest.md")
        report = (try? String(contentsOf: saved, encoding: .utf8)) ?? (try? String(contentsOf: Bundle.main.url(forResource: "initial", withExtension: "md")!, encoding: .utf8)) ?? ""'''
b='''        let saved = support.appendingPathComponent("snapshot.json")
        let snapshotURL = FileManager.default.fileExists(atPath: saved.path) ? saved : Bundle.main.url(forResource: "initial-snapshot", withExtension: "json")!
        if let data = try? Data(contentsOf: snapshotURL), let snapshot = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any] {
            report = snapshot["text"] as? String ?? ""
            context = snapshot["context"] as? [String: Any] ?? [:]
        }'''
assert a in s;s=s.replace(a,b)
s=s.replace('send("receive", ["text":report, "status":"Saved brief · refresh to get current data"])','send("receive", ["text":report, "context":context, "status":"Saved league data · refresh for the latest roster"])')
s=s.replace('''                    try text.write(to: self.support.appendingPathComponent("latest.md"), atomically: true, encoding: .utf8)
                    DispatchQueue.main.async { self.report = text; self.busy = false; self.send("receive", ["text":text,"status":"Updated \\(DateFormatter.localizedString(from: Date(), dateStyle: .short, timeStyle: .short))", "busy":false]) }''','''                    let snapshotData = try Data(contentsOf: job.appendingPathComponent("snapshot.json"))
                    let snapshot = try JSONSerialization.jsonObject(with: snapshotData) as? [String: Any]
                    let latestContext = snapshot?["context"] as? [String: Any] ?? [:]
                    try snapshotData.write(to: self.support.appendingPathComponent("snapshot.json"), options: .atomic)
                    DispatchQueue.main.async { self.report = text; self.context = latestContext; self.busy = false; self.send("receive", ["text":text,"context":latestContext,"status":"League data updated \\(DateFormatter.localizedString(from: Date(), dateStyle: .short, timeStyle: .short))", "busy":false]) }''')
s=s.replace('''    func applicationShouldTerminateAfterLastWindowClosed''','''    @objc func refreshData() { web.evaluateJavaScript("send('refresh')", completionHandler: nil) }
    @objc func showPlan() { web.evaluateJavaScript("setView('overview')", completionHandler: nil) }
    @objc func showResearch() { web.evaluateJavaScript("setView('research')", completionHandler: nil) }
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
    func applicationShouldTerminateAfterLastWindowClosed''')
p.write_text(s)
