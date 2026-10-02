import Cocoa
import Foundation
let folder = URL(fileURLWithPath: CommandLine.arguments[1])
try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
func color(_ r:CGFloat,_ g:CGFloat,_ b:CGFloat)->NSColor{NSColor(calibratedRed:r,green:g,blue:b,alpha:1)}
for size in [16,32,128,256,512] { for scale in [1,2] {
 let pixels=size*scale
 let rep=NSBitmapImageRep(bitmapDataPlanes:nil,pixelsWide:pixels,pixelsHigh:pixels,bitsPerSample:8,samplesPerPixel:4,hasAlpha:true,isPlanar:false,colorSpaceName:.deviceRGB,bytesPerRow:0,bitsPerPixel:0)!
 NSGraphicsContext.saveGraphicsState();NSGraphicsContext.current=NSGraphicsContext(bitmapImageRep:rep)!
 let c=NSGraphicsContext.current!.cgContext;c.scaleBy(x:CGFloat(pixels)/512,y:CGFloat(pixels)/512)
 let tile=NSBezierPath(roundedRect:NSRect(x:16,y:16,width:480,height:480),xRadius:108,yRadius:108)
 NSGradient(starting:color(0.22,0.28,0.37),ending:color(0.035,0.055,0.09))!.draw(in:tile,angle:-90)
 color(0.4,0.48,0.59).setStroke();tile.lineWidth=2;tile.stroke()
 // Red stadium ribbon, with a strong silhouette at Dock size.
 let ring=NSBezierPath(ovalIn:NSRect(x:53,y:69,width:406,height:355));color(0.95,0.16,0.28).setStroke();ring.lineWidth=9;ring.stroke()
 if pixels>=128 { color(0.37,0.45,0.57).withAlphaComponent(0.35).setStroke();for inset in [0,8,16] { let p=NSBezierPath(ovalIn:NSRect(x:70+inset,y:85+inset,width:372-inset*2,height:322-inset*2));p.lineWidth=1;p.stroke() } }
 let white=color(0.93,0.96,1);white.setFill()
 NSBezierPath(roundedRect:NSRect(x:175,y:232,width:162,height:62),xRadius:22,yRadius:22).fill()
 for x in [CGFloat(78),CGFloat(278)] {
  let arm=NSBezierPath();arm.move(to:NSPoint(x:x+3,y:217));arm.line(to:NSPoint(x:x+37,y:354));arm.curve(to:NSPoint(x:x+113,y:354),controlPoint1:NSPoint(x:x+48,y:384),controlPoint2:NSPoint(x:x+100,y:384));arm.line(to:NSPoint(x:x+151,y:217));arm.close();white.setFill();arm.fill()
  let lens=NSBezierPath(ovalIn:NSRect(x:x,y:128,width:156,height:156));white.setFill();lens.fill()
  let glass=NSBezierPath(ovalIn:NSRect(x:x+18,y:146,width:120,height:120));NSGradient(starting:color(0.26,0.45,0.62),ending:color(0.035,0.09,0.15))!.draw(in:glass,angle:-70)
  color(0.6,0.82,0.99).setStroke();let glint=NSBezierPath();glint.move(to:NSPoint(x:x+40,y:236));glint.curve(to:NSPoint(x:x+80,y:249),controlPoint1:NSPoint(x:x+45,y:249),controlPoint2:NSPoint(x:x+64,y:253));glint.lineWidth=5;glint.lineCapStyle = .round;glint.stroke()
 }
 // Football laces on the central bridge.
 color(0.84,0.14,0.24).setStroke();let lace=NSBezierPath();lace.move(to:NSPoint(x:238,y:262));lace.line(to:NSPoint(x:274,y:262));for x in [244,256,268]{lace.move(to:NSPoint(x:x,y:255));lace.line(to:NSPoint(x:x,y:269))};lace.lineWidth=4;lace.lineCapStyle = .round;lace.stroke()
 NSGraphicsContext.restoreGraphicsState()
 try rep.representation(using:.png,properties:[:])!.write(to:folder.appendingPathComponent("icon_\(size)x\(size)"+(scale==2 ? "@2x":"")+".png"))
} }
