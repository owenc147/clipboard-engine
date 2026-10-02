import XCTest
@testable import Binocular
final class ProfileTests: XCTestCase {
 func testUsernameNormalizationAndPathInjection() throws {
  XCTAssertEqual(try normalizedUsername(" Coffero \n"),"coffero")
  for bad in ["../someone", "a/b", "a?x=1", "", "\"", String(repeating:"a",count:65)] { XCTAssertThrowsError(try normalizedUsername(bad)) }
 }
 func testServerProfileDecoding() throws {
  let data = Data("""
  {"user_id":"82CBA612-4D10-4C20-91DF-1BEC93F354E7","sleeper_username":"someone","favorite_leagues":["123"],"revision":7,"updated_at":"2026-09-17T12:00:00Z"}
  """.utf8)
  let profile=try JSONDecoder().decode(AccountProfile.self,from:data)
  XCTAssertEqual(profile.revision,7);XCTAssertEqual(profile.favorite_leagues,["123"])
 }
 func testExpiredSessionMustRefresh() throws {
  let user=AuthUser(id:UUID(),email:nil)
  let expired=Session(access_token:"test",refresh_token:"test",expires_in:3600,user:user,savedAt:Date(timeIntervalSinceNow:-4000))
  let live=Session(access_token:"test",refresh_token:"test",expires_in:3600,user:user,savedAt:Date())
  XCTAssertTrue(expired.expiresSoon);XCTAssertFalse(live.expiresSoon)
 }
}
