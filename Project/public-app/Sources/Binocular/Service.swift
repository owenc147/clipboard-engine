import Foundation
import Security

struct ServiceConfig {
    let url: URL
    let key: String
    static func load() -> ServiceConfig? {
        #if SWIFT_PACKAGE
        let bundle = Bundle.module
        #else
        let bundle = Bundle.main
        #endif
        guard let path = bundle.url(forResource: "ServiceConfig", withExtension: "plist"),
              let data = try? Data(contentsOf: path),
              let info = try? PropertyListSerialization.propertyList(from: data, format: nil) as? [String: String],
              let raw = info["SupabaseURL"], let url = URL(string: raw), url.scheme == "https", url.host != nil,
              let key = info["SupabasePublishableKey"], !key.isEmpty, !key.hasPrefix("sb_secret_") else { return nil }
        // Legacy JWT keys are deliberately unsupported: client builds accept publishable keys only.
        guard key.hasPrefix("sb_publishable_") else { return nil }
        return ServiceConfig(url: url, key: key)
    }
}
struct AuthUser: Codable, Equatable { let id: UUID; let email: String? }
struct Session: Codable {
    let access_token: String
    let refresh_token: String
    let expires_in: Double
    let user: AuthUser
    var savedAt: Date? = nil
    var expiresSoon: Bool { Date().timeIntervalSince(savedAt ?? .distantPast) > expires_in - 90 }
}
struct AccountProfile: Codable, Equatable {
    let user_id: UUID
    var sleeper_username: String?
    var favorite_leagues: [String]
    var revision: Int
}
struct League: Codable, Identifiable {
    let league_id: String
    let name: String
    let total_rosters: Int?
    let status: String?
    var id: String { league_id }
}
struct SleeperUser: Decodable { let user_id: String; let username: String? }
struct NFLState: Decodable { let league_season: String?; let season: String }
enum ServiceError: LocalizedError {
    case notConfigured, signedOut, conflict, invalidUsername, emailDelivery, invalidCode, http(Int), keychain
    var errorDescription: String? {
        switch self {
        case .notConfigured: return "Accounts are not connected in this preview yet."
        case .signedOut: return "Your session expired. Please sign in again."
        case .conflict: return "Your other device saved a change. Reload the latest profile, then try again."
        case .invalidUsername: return "Enter a valid Sleeper username."
        case .http(let code): return code == 429 ? "Too many attempts. Please wait before trying again." : "The service could not complete this request (\(code)). Try again."
        case .emailDelivery: return "The sign-in email could not be sent. Binocular’s email service needs attention. No code was sent; please try again after the service is fixed."
        case .invalidCode: return "That code is invalid or expired. Request a new code and enter the most recent one."
        case .keychain: return "Your session could not be saved securely on this device."
        }
    }
}
func normalizedUsername(_ raw: String) throws -> String {
    let value = raw.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
    guard value.range(of: "^[a-z0-9_-]{1,64}$", options: .regularExpression) != nil else { throw ServiceError.invalidUsername }
    return value
}
struct SessionVault {
    let account: String
    var query: [String: Any] { [kSecClass as String: kSecClassGenericPassword, kSecAttrService as String: "app.binocular.preview.auth", kSecAttrAccount as String: account] }
    func read() -> Session? {
        var q = query; q[kSecReturnData as String] = true; q[kSecMatchLimit as String] = kSecMatchLimitOne
        var value: CFTypeRef?
        guard SecItemCopyMatching(q as CFDictionary, &value) == errSecSuccess, let data = value as? Data else { return nil }
        return try? JSONDecoder().decode(Session.self, from: data)
    }
    func save(_ session: Session) throws {
        let data = try JSONEncoder().encode(session)
        let update = [kSecValueData as String: data]
        let result = SecItemUpdate(query as CFDictionary, update as CFDictionary)
        if result == errSecItemNotFound {
            var add = query; add[kSecValueData as String] = data
            add[kSecAttrAccessible as String] = kSecAttrAccessibleWhenUnlockedThisDeviceOnly
            guard SecItemAdd(add as CFDictionary, nil) == errSecSuccess else { throw ServiceError.keychain }
        } else if result != errSecSuccess { throw ServiceError.keychain }
    }
    func clear() { SecItemDelete(query as CFDictionary) }
}
actor AccountService {
    let config: ServiceConfig
    let vault: SessionVault
    let transport: URLSession
    var session: Session?
    private var refreshing: Task<Session, Error>?
    init(config: ServiceConfig, transport: URLSession = .shared) {
        self.transport = transport
        self.config = config; self.vault = SessionVault(account: config.url.absoluteString)
        session = vault.read()
    }
    func clearDeviceSession() { session=nil; refreshing?.cancel(); refreshing=nil; vault.clear() }
    func currentUser() -> AuthUser? { session?.user }
    private func request(_ path: String, method: String = "GET", body: [String: Any]? = nil, token: String? = nil) async throws -> Data {
        let url = URL(string: path, relativeTo: config.url)!.absoluteURL
        var req = URLRequest(url: url); req.httpMethod = method; req.timeoutInterval = 30
        req.setValue(config.key, forHTTPHeaderField: "apikey")
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let token { req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization") }
        if let body { req.httpBody = try JSONSerialization.data(withJSONObject: body) }
        let (data, response) = try await transport.data(for: req)
        guard let response = response as? HTTPURLResponse else { throw ServiceError.http(0) }
        guard (200..<300).contains(response.statusCode) else {
            if path == "/auth/v1/otp", response.statusCode >= 500 { throw ServiceError.emailDelivery }
            if path == "/auth/v1/verify", [400, 401, 403, 422].contains(response.statusCode) { throw ServiceError.invalidCode }
            if response.statusCode == 401 { throw ServiceError.signedOut }
            if let info = try? JSONSerialization.jsonObject(with: data) as? [String: Any], info["message"] as? String == "sync_conflict" { throw ServiceError.conflict }
            throw ServiceError.http(response.statusCode)
        }
        return data
    }
    func sendCode(email: String) async throws {
        _ = try await request("/auth/v1/otp", method: "POST", body: ["email": email, "create_user": true])
    }
    func verify(email: String, code: String) async throws -> AuthUser {
        let data = try await request("/auth/v1/verify", method: "POST", body: ["email": email, "token": code, "type": "email"])
        var value = try JSONDecoder().decode(Session.self, from: data); value.savedAt = Date()
        try vault.save(value); session = value; return value.user
    }
    private func token() async throws -> String {
        guard let old = session else { throw ServiceError.signedOut }
        if !old.expiresSoon { return old.access_token }
        if let refreshing { return try await refreshing.value.access_token }
        let task = Task { () throws -> Session in
            let data = try await self.request("/auth/v1/token?grant_type=refresh_token", method: "POST", body: ["refresh_token": old.refresh_token])
            var value = try JSONDecoder().decode(Session.self, from: data); value.savedAt = Date(); return value
        }
        refreshing = task
        do {
            let value = try await task.value
            guard session?.user.id == old.user.id else { throw ServiceError.signedOut }
            try vault.save(value); session = value; refreshing = nil; return value.access_token
        } catch { refreshing = nil; throw error }
    }
    func profile() async throws -> AccountProfile {
        let access = try await token()
        let data = try await request("/rest/v1/rpc/get_profile", method: "POST", body: [:], token: access)
        return try JSONDecoder().decode(AccountProfile.self, from: data)
    }
    func save(_ profile: AccountProfile) async throws -> AccountProfile {
        let access = try await token()
        guard profile.user_id == session?.user.id else { throw ServiceError.signedOut }
        let data = try await request("/rest/v1/rpc/save_profile", method: "POST", body: ["expected_revision": profile.revision, "new_username": profile.sleeper_username as Any? ?? NSNull(), "new_favorites": profile.favorite_leagues], token: access)
        return try JSONDecoder().decode(AccountProfile.self, from: data)
    }
    func deleteAccount() async throws {
        let access = try await token()
        _ = try await request("/functions/v1/delete-account", method: "POST", body: [:], token: access)
        session = nil; vault.clear()
    }
    func signOut() async throws {
        let access = try await token()
        _ = try await request("/auth/v1/logout?scope=local", method: "POST", token: access)
        session = nil; refreshing?.cancel(); refreshing = nil; vault.clear()
    }
}
struct SleeperService {
    func get<T: Decodable>(_ path: String, as: T.Type) async throws -> T {
        let url = URL(string: "https://api.sleeper.app/v1" + path)!
        var request = URLRequest(url: url); request.timeoutInterval = 30
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let response = response as? HTTPURLResponse, response.statusCode == 200 else { throw ServiceError.http((response as? HTTPURLResponse)?.statusCode ?? 0) }
        return try JSONDecoder().decode(T.self, from: data)
    }
    func leagues(username: String) async throws -> [League] {
        let username = try normalizedUsername(username)
        let user = try await get("/user/\(username)", as: SleeperUser.self)
        let state = try await get("/state/nfl", as: NFLState.self)
        return try await get("/user/\(user.user_id)/leagues/nfl/\(state.league_season ?? state.season)", as: [League].self)
    }
}

struct FootballPlayer: Decodable {
    let full_name: String?
    let position: String?
    let team: String?
    let injury_status: String?
}
struct FootballRoster: Decodable, Identifiable {
    let roster_id: Int
    let owner_id: String?
    let players: [String]?
    let starters: [String]?
    let reserve: [String]?
    let taxi: [String]?
    let settings: [String: Double]?
    var id: Int { roster_id }
    var record: String { "\(Int(settings?["wins"] ?? 0))–\(Int(settings?["losses"] ?? 0))–\(Int(settings?["ties"] ?? 0))" }
    var points: Double { (settings?["fpts"] ?? 0) + (settings?["fpts_decimal"] ?? 0) / 100 }
    var bench: [String] { (players ?? []).filter { !(starters ?? []).contains($0) && !(reserve ?? []).contains($0) && !(taxi ?? []).contains($0) } }
}
struct FootballMember: Decodable {
    let user_id: String
    let display_name: String?
    let metadata: [String: String]?
    var name: String { metadata?["team_name"] ?? display_name ?? "League member" }
}
struct FootballTransaction: Decodable, Identifiable {
    let transaction_id: String
    let type: String
    let status: String
    let status_updated: Double?
    let adds: [String: Int]?
    let drops: [String: Int]?
    var id: String { transaction_id }
}
struct FootballRules: Decodable {
    let roster_positions: [String]?
    let scoring_settings: [String: Double]?
}
struct FootballWeek: Decodable { let week: Int? }
struct FootballSnapshot {
    let rosters: [FootballRoster]
    let members: [FootballMember]
    let transactions: [FootballTransaction]
    let rules: FootballRules
    let players: [String: FootballPlayer]
    let week: Int
    let fetchedAt: Date
    func teamName(_ id: Int) -> String {
        let owner = rosters.first { $0.id == id }?.owner_id
        return members.first { $0.user_id == owner }?.name ?? "Team \(id)"
    }
    func playerName(_ id: String) -> String { id == "0" ? "Empty slot" : players[id]?.full_name ?? (id.count <= 3 ? "\(id) defense" : "Player \(id)") }
}
actor FootballPlayerCache {
    static let shared = FootballPlayerCache()
    private var saved: (Date, [String: FootballPlayer])?
    private var pending: Task<[String: FootballPlayer], Error>?
    func load() async throws -> [String: FootballPlayer] {
        if let saved, Date().timeIntervalSince(saved.0) < 86400 { return saved.1 }
        if let pending { return try await pending.value }
        let task = Task { try await SleeperService().get("/players/nfl", as: [String: FootballPlayer].self) }
        pending = task
        do { let result = try await task.value; saved = (Date(), result); pending = nil; return result }
        catch { pending = nil; throw error }
    }
}
extension SleeperService {
    func football(leagueID: String) async throws -> FootballSnapshot {
        guard leagueID.range(of: "^[0-9]+$", options: .regularExpression) != nil else { throw ServiceError.http(400) }
        async let rosters = get("/league/\(leagueID)/rosters", as: [FootballRoster].self)
        async let members = get("/league/\(leagueID)/users", as: [FootballMember].self)
        async let rules = get("/league/\(leagueID)", as: FootballRules.self)
        async let players = FootballPlayerCache.shared.load()
        let state = try await get("/state/nfl", as: FootballWeek.self)
        let week = max(1, state.week ?? 1)
        async let transactions = get("/league/\(leagueID)/transactions/\(week)", as: [FootballTransaction].self)
        return try await FootballSnapshot(rosters: rosters, members: members, transactions: transactions, rules: rules, players: players, week: week, fetchedAt: Date())
    }
}
