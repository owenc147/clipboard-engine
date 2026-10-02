// swift-tools-version: 6.0
import PackageDescription
let package = Package(name: "Binocular", platforms: [.macOS(.v14), .iOS(.v17)], products: [.executable(name: "Binocular", targets: ["Binocular"])], targets: [.executableTarget(name: "Binocular", resources: [.copy("ServiceConfig.plist")]), .testTarget(name: "BinocularTests", dependencies: ["Binocular"])], swiftLanguageModes: [.v5])
