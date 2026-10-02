import Cocoa
import Security

extension AppDelegate {
    var suggestionRecipient: String { "ofc14700@gmail.com" }
    var keychainQuery: [String: Any] { [kSecClass as String:kSecClassGenericPassword,kSecAttrService as String:"local.coffero.binocular.gmail",kSecAttrAccount as String:suggestionRecipient] }
    func gmailPassword() -> String? {
        var q=keychainQuery;q[kSecReturnData as String]=true;q[kSecMatchLimit as String]=kSecMatchLimitOne
        var result:CFTypeRef?;guard SecItemCopyMatching(q as CFDictionary,&result)==errSecSuccess,let data=result as? Data else{return nil}
        return String(data:data,encoding:.utf8)
    }
    func hasGmail() -> Bool { UserDefaults.standard.bool(forKey:"gmailConnected") }
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
        let alert=NSAlert();alert.messageText="Connect Gmail for suggestions"
        alert.informativeText="Send from and to ofc14700@gmail.com. Every subject will be BINOCULAR SUGGESTION. Enter a Gmail app password, not your regular password. Connect verifies it and stores it in this Mac’s Keychain. New suggestions will then send automatically. Existing saved suggestions can be sent individually."
        let field=NSSecureTextField(frame:NSRect(x:0,y:0,width:360,height:28));field.placeholderString="16-character Gmail app password";alert.accessoryView=field
        alert.addButton(withTitle:"Connect & save in Keychain");alert.addButton(withTitle:"Cancel");alert.addButton(withTitle:"Setup instructions")
        alert.beginSheetModal(for:window){ response in
            if response == .alertThirdButtonReturn {NSWorkspace.shared.open(URL(string:"https://support.google.com/accounts/answer/185833")!);return}
            guard response == .alertFirstButtonReturn else{return}
            let secret=field.stringValue.filter{ !$0.isWhitespace };field.stringValue=""
            guard secret.count==16 else{self.loadSuggestions(status:"Enter the 16-character app password from Google.");return}
            self.send("suggestionProgress",["status":"Checking Gmail connection…"])
            DispatchQueue.global(qos:.userInitiated).async {
                let result=self.emailRequest(["mode":"verify","password":secret])
                DispatchQueue.main.async {
                    if result["ok"] as? Bool == true {
                        if self.storeGmailPassword(secret){UserDefaults.standard.set(true,forKey:"gmailConnected");self.loadSuggestions(status:"Gmail connected. New suggestions will email automatically.")}
                        else{self.loadSuggestions(status:"Gmail verified, but the password could not be saved in Keychain.")}
                    }else{self.loadSuggestions(status:result["status"] as? String ?? "Connection failed.")}
                }
            }
        }
    }
    func sendSavedSuggestion(id:String) {
        guard !mailBusy,let item=suggestionItems().first(where:{$0["id"]==id}),!(item["status"] ?? "").hasPrefix("Sent") else{return}
        guard let password=gmailPassword() else{loadSuggestions(status:"Connect Gmail to send this saved suggestion.");return}
        mailBusy=true;send("suggestionProgress",["status":"Sending suggestion…"])
        var payload=item;payload["password"]=password
        DispatchQueue.global(qos:.userInitiated).async {
            let result=self.emailRequest(payload)
            DispatchQueue.main.async {
                self.mailBusy=false
                var items=self.suggestionItems()
                if let index=items.firstIndex(where:{$0["id"]==id}){items[index]["status"]=result["status"] as? String ?? "Delivery not confirmed."}
                do{try JSONEncoder().encode(items).write(to:self.support.appendingPathComponent("suggestions.json"),options:.atomic);self.loadSuggestions(status:result["status"] as? String ?? "Delivery not confirmed.")}
                catch{self.loadSuggestions(status:"Email attempt finished, but its status could not be saved. Check your inbox before retrying.")}
            }
        }
    }
}
