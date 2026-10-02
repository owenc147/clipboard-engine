import SwiftUI

@MainActor final class AccountModel: ObservableObject {
    @Published var user: AuthUser?
    @Published var profile: AccountProfile?
    @Published var leagues: [League] = []
    @Published var busy = false
    @Published var message = ""
    @Published var codeSent = false
    @Published var resendAfter = Date.distantPast
    @Published var lastSync: Date?
    @Published var draftUsername = ""
    @Published var editing = false
    let service: AccountService?
    init() { service = ServiceConfig.load().map { AccountService(config: $0) } }
    func perform(_ job: () async throws -> Void) async {
        guard !busy else { return }; busy = true; message = ""
        defer { busy = false }
        do { try await job() } catch {
            if case ServiceError.signedOut = error { await service?.clearDeviceSession(); clear() }
            message = error.localizedDescription
        }
    }
    func restore() async {
        guard let service else { return }
        await perform { self.user = await service.currentUser(); if self.user != nil { try await self.load() } }
    }
    func load() async throws {
        guard let service else { throw ServiceError.notConfigured }
        let value = try await service.profile()
        guard value.user_id == user?.id else { throw ServiceError.signedOut }
        let changed = value.sleeper_username != profile?.sleeper_username
        profile = value; draftUsername = value.sleeper_username ?? ""; lastSync = Date()
        if changed || leagues.isEmpty {
            leagues = []
            if let username = value.sleeper_username { leagues = try await SleeperService().leagues(username: username) }
        }
    }
    func sync() async { guard user != nil, !editing else { return }; await perform { try await self.load() } }
    func send(email: String) async {
        await perform { guard let service else { throw ServiceError.notConfigured }; guard Date() >= resendAfter else { return }; try await service.sendCode(email: email); resendAfter = Date().addingTimeInterval(60); codeSent = true; message = "Check your email for the sign-in code." }
    }
    func verify(email: String, code: String) async {
        await perform { guard let service else { throw ServiceError.notConfigured }; user = try await service.verify(email: email, code: code); try await load() }
    }
    func link() async {
        await perform {
            guard let service, var value = profile else { throw ServiceError.signedOut }
            let username = try normalizedUsername(draftUsername)
            let fresh = try await SleeperService().leagues(username: username)
            if value.sleeper_username != username { value.favorite_leagues = [] }
            value.sleeper_username = username
            let saved = try await service.save(value)
            profile = saved; draftUsername = username; leagues = fresh; editing = false; lastSync = Date(); message = "Sleeper profile saved to your Binocular account."
        }
    }
    func favorite(_ league: League) async {
        await perform {
            guard let service, var value = profile else { throw ServiceError.signedOut }
            if value.favorite_leagues.contains(league.id) { value.favorite_leagues.removeAll { $0 == league.id } } else { value.favorite_leagues.append(league.id) }
            profile = try await service.save(value); lastSync = Date()
        }
    }
    func signOut() async {
        await perform { guard let service else { return }; try await service.signOut(); clear() }
    }
    func delete() async {
        await perform { guard let service else { return }; try await service.deleteAccount(); clear() }
    }
    func clear() { user = nil; profile = nil; leagues = []; draftUsername = ""; lastSync = nil; editing = false; codeSent = false }
}

@main struct BinocularApp: App {
    @StateObject private var model = AccountModel()
    var body: some Scene {
        WindowGroup { RootView().environmentObject(model).preferredColorScheme(.dark) }
    }
}
struct RootView: View {
    @EnvironmentObject var model: AccountModel
    @Environment(\.scenePhase) var phase
    var body: some View {
        ZStack {
            Color(red: 0.035, green: 0.055, blue: 0.09).ignoresSafeArea()
            if model.user == nil { LoginView() } else { HomeView() }
        }
        .tint(Color(red: 0.98, green: 0.22, blue: 0.34))
        .task { await model.restore() }
        .task(id: phase) {
            guard phase == .active else { return }
            while !Task.isCancelled {
                try? await Task.sleep(nanoseconds: 60_000_000_000)
                if Task.isCancelled { return }
                await model.sync()
            }
        }
        .onChange(of: phase) { _, value in if value == .active { Task { await model.sync() } } }
    }
}
struct BrandHeader: View {
    var title: String
    var subtitle: String
    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            Label("BINOCULAR", systemImage: "binoculars.fill").font(.headline).tracking(3).foregroundStyle(.pink)
            Text(title).font(.system(size: 40, weight: .black, design: .rounded)).textCase(.uppercase).fixedSize(horizontal: false, vertical: true)
            Text(subtitle).foregroundStyle(.secondary)
        }.frame(maxWidth: .infinity, alignment: .leading).padding(26)
        .background(LinearGradient(colors: [Color(red: 0.14, green: 0.20, blue: 0.29), .black.opacity(0.4)], startPoint: .topLeading, endPoint: .bottomTrailing))
        .clipShape(RoundedRectangle(cornerRadius: 22))
        .overlay(alignment: .top) { Capsule().fill(.pink).frame(height: 3).padding(.horizontal, 20) }
    }
}
struct LoginView: View {
    @EnvironmentObject var model: AccountModel
    @State private var email = ""
    @State private var code = ""
    @State private var browsing = false
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                BrandHeader(title: "Your leagues.\nEverywhere.", subtitle: "One Binocular account for Mac and iPhone.")
                if model.service == nil {
                    Label("PRIVATE PREVIEW", systemImage: "hammer.fill").font(.caption.bold()).foregroundStyle(.pink)
                    Text("Accounts are coming online.").font(.title2.bold())
                    Text("This preview is ready for account setup. Sign-in will be available once the Binocular service is connected.").foregroundStyle(.secondary)
                } else {
                    Text(model.codeSent ? "Enter your sign-in code" : "Create an account or sign in").font(.title2.bold())
                    TextField("Email address", text: $email).textContentType(.emailAddress).textFieldStyle(.roundedBorder).disabled(model.codeSent || model.busy)
                    if model.codeSent {
                        TextField("Code from your email", text: $code).textContentType(.oneTimeCode).textFieldStyle(.roundedBorder)
                        Button("Sign in") { Task { await model.verify(email: email.trimmingCharacters(in: .whitespacesAndNewlines), code: code.trimmingCharacters(in: .whitespacesAndNewlines)) } }.buttonStyle(.borderedProminent).disabled(code.count < 6 || model.busy)
                        TimelineView(.periodic(from: .now, by: 1)) { context in
                            Button(context.date < model.resendAfter ? "Resend available shortly" : "Send a new code") { Task { await model.send(email: email.trimmingCharacters(in: .whitespacesAndNewlines)) } }.disabled(model.busy || context.date < model.resendAfter)
                        }
                        Button("Use a different email") { model.codeSent = false; model.message = ""; code = "" }.disabled(model.busy)
                    } else {
                        TimelineView(.periodic(from: .now, by: 1)) { context in
                            Button(context.date < model.resendAfter ? "Please wait before sending another code" : "Email me a sign-in code") { Task { await model.send(email: email.trimmingCharacters(in: .whitespacesAndNewlines)) } }.buttonStyle(.borderedProminent).disabled(!email.contains("@") || model.busy || context.date < model.resendAfter)
                        }
                    }
                    Text("Your first sign-in creates your Binocular account. Connect a Sleeper username afterward—no Sleeper password needed.").font(.footnote).foregroundStyle(.secondary)
                }
                Divider()
                Button("Explore public Sleeper leagues") { browsing = true }.buttonStyle(.bordered)
                Text("Browse with a Sleeper username while sign-in is being set up. Sign in to sync favorites across devices.").font(.footnote).foregroundStyle(.secondary)
                StatusView()
            }.padding(24).frame(maxWidth: 620)
        }.sheet(isPresented: $browsing) { NavigationStack { PublicLeagueBrowser() }.frame(minWidth: 320, minHeight: 480) }
    }
}
struct StatusView: View {
    @EnvironmentObject var model: AccountModel
    var body: some View {
        VStack(alignment: .leading) {
            if model.busy { ProgressView("Working…") }
            if !model.message.isEmpty { Text(model.message).font(.callout).foregroundStyle(.secondary).accessibilityLabel(model.message) }
        }
    }
}
struct HomeView: View {
    @EnvironmentObject var model: AccountModel
    var body: some View {
        TabView {
            NavigationStack { LeagueView() }.tabItem { Label("Leagues", systemImage: "sportscourt.fill") }
            NavigationStack { AccountView() }.tabItem { Label("Account", systemImage: "person.crop.circle") }
        }
    }
}
struct LeagueView: View {
    @EnvironmentObject var model: AccountModel
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                BrandHeader(title: "See the\nwhole field.", subtitle: model.profile?.sleeper_username.map { "@" + $0 } ?? "Connect Sleeper in Account to find your leagues.")
                if model.leagues.isEmpty { Text("Your current-season leagues will appear here after connecting Sleeper.").foregroundStyle(.secondary) }
                ForEach(model.leagues) { league in
                    HStack(spacing: 16) {
                        Image(systemName: "football.fill").foregroundStyle(.pink).font(.title2)
                        VStack(alignment: .leading, spacing: 6) {
                            NavigationLink { FootballDetailView(league: league) } label: { Text(league.name).font(.headline) }
                            Text("\(league.total_rosters ?? 0) teams · \(league.status?.replacingOccurrences(of: "_", with: " ") ?? "League")").font(.caption).foregroundStyle(.secondary)
                        }
                        Spacer()
                        Button { Task { await model.favorite(league) } } label: { Image(systemName: model.profile?.favorite_leagues.contains(league.id) == true ? "star.fill" : "star") }.buttonStyle(.borderless).disabled(model.busy).accessibilityLabel("Favorite \(league.name)")
                    }.padding(20).background(.white.opacity(0.06), in: RoundedRectangle(cornerRadius: 16))
                }
                Text("Favorites sync with your Binocular account. Player research and trade analysis are being prepared for this shared version.").font(.footnote).foregroundStyle(.secondary)
                Button("Refresh leagues & account") { Task { model.leagues = []; await model.sync() } }.disabled(model.busy || model.editing)
                StatusView()
            }.padding(24).frame(maxWidth: 900)
        }.navigationTitle("Football desk")
    }
}
struct AccountView: View {
    @EnvironmentObject var model: AccountModel
    @State private var deleting = false
    var body: some View {
        Form {
            Section("Binocular account") {
                Text(model.user?.email ?? "Signed in")
                if let date = model.lastSync { Text("Last synced \(date.formatted(date: .abbreviated, time: .shortened))").foregroundStyle(.secondary) }
                Button("Reload synced profile") { Task { model.editing = false; await model.sync() } }.disabled(model.busy)
            }
            Section("Sleeper profile") {
                TextField("Sleeper username", text: $model.draftUsername).onChange(of: model.draftUsername) { _, _ in model.editing = model.draftUsername != (model.profile?.sleeper_username ?? "") }
                Text("This links public league information. It does not sign in to Sleeper or verify ownership of that username.").font(.footnote).foregroundStyle(.secondary)
                Button("Save & sync Sleeper profile") { Task { await model.link() } }.disabled(model.busy || model.draftUsername.isEmpty)
            }
            Section { StatusView() }
            Section {
                Button("Sign out") { Task { await model.signOut() } }.disabled(model.busy)
                Button("Delete Binocular account", role: .destructive) { deleting = true }.disabled(model.busy)
            }
        }.formStyle(.grouped).navigationTitle("Account")
        .confirmationDialog("Delete your Binocular account?", isPresented: $deleting, titleVisibility: .visible) {
            Button("Delete account permanently", role: .destructive) { Task { await model.delete() } }
        } message: { Text("Your Binocular profile and synced favorites will be deleted. Your Sleeper account and leagues remain intact.") }
    }
}

struct FootballDetailView: View {
    let league: League
    @State private var snapshot: FootballSnapshot?
    @State private var loading = false
    @State private var error = ""
    @State private var section = "Teams"
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                BrandHeader(title: league.name, subtitle: "Every roster. Every angle.")
                if let snapshot {
                    Text("Week \(snapshot.week) · Updated \(snapshot.fetchedAt.formatted(date: .omitted, time: .shortened))").font(.caption).foregroundStyle(.secondary)
                    Picker("League view", selection: $section) {
                        Text("Teams").tag("Teams")
                        Text("Activity").tag("Activity")
                        Text("Scoring").tag("Scoring")
                    }.pickerStyle(.segmented)
                    if section == "Teams" {
                        Text("Standings by wins, ties, then points for").font(.caption).foregroundStyle(.secondary)
                        ForEach(snapshot.rosters.sorted(by: standingOrder)) { roster in
                            DisclosureGroup {
                                rosterSection("Starters", ids: roster.starters ?? [], snapshot: snapshot, slots: (snapshot.rules.roster_positions ?? []).filter { $0 != "BN" })
                                rosterSection("Bench", ids: roster.bench, snapshot: snapshot)
                                rosterSection("Reserve", ids: roster.reserve ?? [], snapshot: snapshot)
                                rosterSection("Taxi", ids: roster.taxi ?? [], snapshot: snapshot)
                            } label: {
                                VStack(alignment: .leading, spacing: 5) {
                                    Text(snapshot.teamName(roster.id)).font(.headline)
                                    Text("\(roster.record) · \(roster.points, specifier: "%.2f") PF").font(.caption).foregroundStyle(.secondary)
                                }
                            }.padding(18).background(.white.opacity(0.06), in: RoundedRectangle(cornerRadius: 16))
                        }
                    } else if section == "Activity" {
                        Text("Reported transactions for Week \(snapshot.week). Failed claims are labeled; lineup edits are not transactions.").font(.caption).foregroundStyle(.secondary)
                        if snapshot.transactions.isEmpty { Text("No transactions reported this week.") }
                        ForEach(snapshot.transactions.sorted { ($0.status_updated ?? 0) > ($1.status_updated ?? 0) }) { transaction in
                            VStack(alignment: .leading, spacing: 8) {
                                Text("\(transaction.type.replacingOccurrences(of: "_", with: " ").capitalized) · \(transaction.status)").font(.headline)
                                if let date = transaction.status_updated { Text(Date(timeIntervalSince1970: date / 1000).formatted()).font(.caption).foregroundStyle(.secondary) }
                                ForEach((transaction.adds ?? [:]).keys.sorted(), id: \.self) { id in
                                    Text("\(transaction.status == "complete" ? "Added" : "Requested add") \(snapshot.playerName(id)) → \(snapshot.teamName(transaction.adds![id]!))")
                                }
                                ForEach((transaction.drops ?? [:]).keys.sorted(), id: \.self) { id in
                                    Text("\(transaction.status == "complete" ? "Removed" : "Requested removal") \(snapshot.playerName(id)) · \(snapshot.teamName(transaction.drops![id]!))")
                                }
                                if (transaction.adds ?? [:]).isEmpty && (transaction.drops ?? [:]).isEmpty { Text("No player changes reported. This transaction may involve draft picks.").foregroundStyle(.secondary) }
                            }.padding(18).frame(maxWidth: .infinity, alignment: .leading).background(.white.opacity(0.06), in: RoundedRectangle(cornerRadius: 16))
                        }
                    } else {
                        ForEach((snapshot.rules.scoring_settings ?? [:]).keys.sorted(), id: \.self) { key in
                            HStack { Text(key.replacingOccurrences(of: "_", with: " ")); Spacer(); Text(snapshot.rules.scoring_settings![key]!, format: .number).monospacedDigit() }
                        }
                    }
                    Text("Sleeper injury labels are informational. Confirm official game status before setting your lineup.").font(.footnote).foregroundStyle(.secondary)
                }
                if loading { ProgressView("Loading the league…") }
                if !error.isEmpty { Text(error).foregroundStyle(.orange) }
                Button("Refresh league") { Task { await refresh() } }.disabled(loading)
            }.padding(24).frame(maxWidth: 900)
        }.navigationTitle("League center").task { await refresh() }.refreshable { await refresh() }
    }
    private func standingOrder(_ a: FootballRoster, _ b: FootballRoster) -> Bool {
        if a.settings?["wins"] != b.settings?["wins"] { return (a.settings?["wins"] ?? 0) > (b.settings?["wins"] ?? 0) }
        if a.settings?["ties"] != b.settings?["ties"] { return (a.settings?["ties"] ?? 0) > (b.settings?["ties"] ?? 0) }
        return a.points == b.points ? a.id < b.id : a.points > b.points
    }
    private func rosterSection(_ title: String, ids: [String], snapshot: FootballSnapshot, slots: [String] = []) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            if !ids.isEmpty {
                Text(title.uppercased()).font(.caption.bold()).tracking(2).foregroundStyle(.pink).padding(.top, 12)
                ForEach(ids.indices, id: \.self) { index in
                    let id = ids[index]
                    HStack(alignment: .top) {
                        Text(index < slots.count ? slots[index] : snapshot.players[id]?.position ?? "—").font(.caption.bold()).frame(width: 65, alignment: .leading)
                        VStack(alignment: .leading, spacing: 3) {
                            Text(snapshot.playerName(id)).font(.body.weight(.semibold))
                            if let player = snapshot.players[id] {
                                Text([player.team, player.injury_status].compactMap { $0 }.joined(separator: " · ")).font(.caption).foregroundStyle(player.injury_status == nil ? Color.secondary : Color.orange)
                            }
                        }
                        Spacer(minLength: 0)
                    }
                }
            }
        }.frame(maxWidth: .infinity, alignment: .leading)
    }
    @MainActor private func refresh() async {
        guard !loading else { return }; loading = true; error = ""
        defer { loading = false }
        do { let fresh = try await SleeperService().football(leagueID: league.id); try Task.checkCancellation(); snapshot = fresh }
        catch is CancellationError { }
        catch { self.error = "Couldn’t refresh this league. \(error.localizedDescription)" }
    }
}

struct PublicLeagueBrowser: View {
    @AppStorage("lastPublicSleeperUsername") private var lastUsername = ""
    @Environment(\.dismiss) var dismiss
    @State private var username = ""
    @State private var leagues: [League] = []
    @State private var busy = false
    @State private var message = ""
    @State private var searched = false
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                BrandHeader(title: "Scout the league.", subtitle: "Public Sleeper data. No password required.")
                TextField("Sleeper username", text: $username).textFieldStyle(.roundedBorder).disabled(busy)
                Button("Find leagues") { Task { await search() } }.buttonStyle(.borderedProminent).disabled(busy || username.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                if busy { ProgressView("Finding current-season leagues…") }
                if !message.isEmpty { Text(message).foregroundStyle(.orange) }
                if searched && leagues.isEmpty && message.isEmpty { Text("No current-season leagues found for this username.") }
                ForEach(leagues) { league in
                    NavigationLink { FootballDetailView(league: league) } label: {
                        HStack {
                            Image(systemName: "football.fill").foregroundStyle(.pink)
                            VStack(alignment: .leading, spacing: 6) {
                                Text(league.name).font(.headline)
                                Text("\(league.total_rosters ?? 0) teams").font(.caption).foregroundStyle(.secondary)
                            }
                            Spacer()
                            Image(systemName: "chevron.right")
                        }.padding(18).background(.white.opacity(0.06), in: RoundedRectangle(cornerRadius: 16))
                    }.buttonStyle(.plain)
                }
            }.padding(24).frame(maxWidth: 900)
        }.task { if username.isEmpty && !lastUsername.isEmpty { username = lastUsername; await search() } }.navigationTitle("Explore").toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done") { dismiss() } } }
    }
    @MainActor private func search() async {
        guard !busy else { return }; busy = true; message = ""; leagues = []; searched = false
        defer { busy = false }
        do { let normalized = try normalizedUsername(username); let result = try await SleeperService().leagues(username: normalized); leagues = result; lastUsername = normalized; searched = true }
        catch { message = error.localizedDescription }
    }
}
