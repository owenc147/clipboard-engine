import Foundation
final class Stub: URLProtocol {
 static var status = 200
 static var seen: URLRequest?
 override class func canInit(with request: URLRequest) -> Bool { true }
 override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }
 override func startLoading() {
  Self.seen=request
  client?.urlProtocol(self,didReceive:HTTPURLResponse(url:request.url!,statusCode:Self.status,httpVersion:nil,headerFields:nil)!,cacheStoragePolicy:.notAllowed)
  client?.urlProtocol(self,didLoad:Data("{}".utf8));client?.urlProtocolDidFinishLoading(self)
 }
 override func stopLoading() {}
}
@main struct Checks {
 static func main() async throws {
  let normalized=try normalizedUsername(" Coffero \n");assert(normalized=="coffero")
  for bad in ["../x","a/b","a?x=1","",String(repeating:"a",count:65)] {
   do { _=try normalizedUsername(bad);fatalError("Accepted invalid username") } catch ServiceError.invalidUsername {}
  }
  let user=AuthUser(id:UUID(),email:nil)
  assert(Session(access_token:"test",refresh_token:"test",expires_in:3600,user:user,savedAt:.distantPast).expiresSoon)
  assert(!Session(access_token:"test",refresh_token:"test",expires_in:3600,user:user,savedAt:Date()).expiresSoon)
  let config=URLSessionConfiguration.ephemeral;config.protocolClasses=[Stub.self]
  let service=AccountService(config:ServiceConfig(url:URL(string:"https://binocular-test.invalid")!,key:"sb_publishable_test"),transport:URLSession(configuration:config))
  try await service.sendCode(email:"test@example.invalid")
  assert(Stub.seen?.url?.path=="/auth/v1/otp")
  assert(Stub.seen?.httpMethod=="POST")
  assert(Stub.seen?.value(forHTTPHeaderField:"apikey")=="sb_publishable_test")
  assert(Stub.seen?.value(forHTTPHeaderField:"Authorization")==nil)
  Stub.status=500
  do { try await service.sendCode(email:"test@example.invalid"); fatalError("Delivery failure ignored") } catch ServiceError.emailDelivery {}
  Stub.status=400
  do { _ = try await service.verify(email:"test@example.invalid",code:"000000"); fatalError("Invalid code accepted") } catch ServiceError.invalidCode {}
  Stub.status=429
  do {try await service.sendCode(email:"test@example.invalid");fatalError("Rate limit ignored")} catch ServiceError.http(let status) {assert(status==429)}
  do {_=try await service.profile();fatalError("Unauthenticated profile request allowed")} catch ServiceError.signedOut {}
  let data=Data("{\"user_id\":\"82CBA612-4D10-4C20-91DF-1BEC93F354E7\",\"sleeper_username\":\"test\",\"favorite_leagues\":[\"123\"],\"revision\":7}".utf8)
  let profile=try JSONDecoder().decode(AccountProfile.self,from:data);assert(profile.revision==7&&profile.favorite_leagues==["123"])
  let rosterJSON = Data(#"{"roster_id":1,"owner_id":null,"players":["1","2","3","4"],"starters":["1","0"],"reserve":["3"],"taxi":["4"],"settings":{"wins":2,"losses":1,"ties":0,"fpts":300,"fpts_decimal":75}}"#.utf8)
  let roster = try JSONDecoder().decode(FootballRoster.self, from: rosterJSON)
  assert(roster.bench == ["2"] && roster.points == 300.75 && roster.record == "2–1–0")
  let transaction = try JSONDecoder().decode(FootballTransaction.self, from: Data(#"{"transaction_id":"123","type":"waiver","status":"failed","adds":null,"drops":null,"status_updated":null}"#.utf8))
  assert(transaction.adds == nil && transaction.status == "failed")
  print("PASS: roster starter/reserve/taxi separation, standings decimals, null transaction fields.")
  print("PASS: username injection rejection, session expiry, OTP request headers, rate limits, unauthenticated sync rejection, profile revision decoding. No real network or emails.")
 }
}
