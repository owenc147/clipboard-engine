from pathlib import Path
import hashlib,json,shutil
root=Path(__file__).resolve().parent
project=root/'Binocular.xcodeproj';project.mkdir(exist_ok=True)
def ident(s):return hashlib.sha256(s.encode()).hexdigest()[:24].upper()
objects={}
def add(object_name,isa,**kw):objects[ident(object_name)]={'isa':isa,**kw};return ident(object_name)
refs=[];src=[];resources=[]
for path,kind in [('Sources/Binocular/Service.swift','sourcecode.swift'),('Sources/Binocular/BinocularApp.swift','sourcecode.swift'),('Sources/Binocular/ServiceConfig.plist','text.plist.xml'),('Assets.xcassets','folder.assetcatalog')]:
 ref=add(path,'PBXFileReference',lastKnownFileType=kind,path=path,sourceTree='<group>');refs.append(ref)
 build=add('build'+path,'PBXBuildFile',fileRef=ref)
 (src if path.endswith('.swift') else resources).append(build)
product=add('product','PBXFileReference',explicitFileType='wrapper.application',path='Binocular.app',sourceTree='BUILT_PRODUCTS_DIR')
products=add('products','PBXGroup',children=[product],name='Products',sourceTree='<group>')
group=add('group','PBXGroup',children=refs+[products],sourceTree='<group>')
sources=add('sources','PBXSourcesBuildPhase',buildActionMask=2147483647,files=src,runOnlyForDeploymentPostprocessing=0)
res=add('resources','PBXResourcesBuildPhase',buildActionMask=2147483647,files=resources,runOnlyForDeploymentPostprocessing=0)
frameworks=add('frameworks','PBXFrameworksBuildPhase',buildActionMask=2147483647,files=[],runOnlyForDeploymentPostprocessing=0)
base={'PRODUCT_BUNDLE_IDENTIFIER':'app.binocular.preview','PRODUCT_NAME':'$(TARGET_NAME)','SWIFT_VERSION':'5.0','MACOSX_DEPLOYMENT_TARGET':'14.0','IPHONEOS_DEPLOYMENT_TARGET':'17.0','SUPPORTED_PLATFORMS':'iphoneos iphonesimulator macosx','SDKROOT':'auto','TARGETED_DEVICE_FAMILY':'1,2','GENERATE_INFOPLIST_FILE':'YES','INFOPLIST_KEY_CFBundleDisplayName':'Binocular','INFOPLIST_KEY_LSApplicationCategoryType':'public.app-category.sports','INFOPLIST_KEY_UILaunchScreen_Generation':'YES','INFOPLIST_KEY_UIApplicationSceneManifest_Generation':'YES','CODE_SIGN_STYLE':'Automatic','CODE_SIGN_ENTITLEMENTS[sdk=macosx*]':'Config/Binocular.entitlements','CODE_SIGN_ENTITLEMENTS[sdk=iphone*]':'Config/iOS.entitlements','ENABLE_HARDENED_RUNTIME':'YES','ASSETCATALOG_COMPILER_APPICON_NAME':'AppIcon','CURRENT_PROJECT_VERSION':'1','MARKETING_VERSION':'0.1.0','SWIFT_EMIT_LOC_STRINGS':'YES'}
configs=[];pconfigs=[]
for name in ['Debug','Release']:
 settings=dict(base,SWIFT_OPTIMIZATION_LEVEL='-Onone' if name=='Debug' else '-O')
 configs.append(add(name,'XCBuildConfiguration',name=name,buildSettings=settings))
 pconfigs.append(add('project'+name,'XCBuildConfiguration',name=name,buildSettings={'CLANG_ENABLE_MODULES':'YES','SWIFT_VERSION':'5.0'}))
cl=add('configs','XCConfigurationList',buildConfigurations=configs,defaultConfigurationIsVisible=0,defaultConfigurationName='Release')
pcl=add('pconfigs','XCConfigurationList',buildConfigurations=pconfigs,defaultConfigurationIsVisible=0,defaultConfigurationName='Release')
target=add('target','PBXNativeTarget',buildConfigurationList=cl,buildPhases=[sources,frameworks,res],buildRules=[],dependencies=[],name='Binocular',productName='Binocular',productReference=product,productType='com.apple.product-type.application')
pr=add('project','PBXProject',attributes={'BuildIndependentTargetsInParallel':'YES','LastUpgradeCheck':'1600'},buildConfigurationList=pcl,compatibilityVersion='Xcode 14.0',developmentRegion='en',hasScannedForEncodings=0,knownRegions=['en','Base'],mainGroup=group,productRefGroup=products,projectDirPath='',projectRoot='',targets=[target])
def fmt(x):
 if isinstance(x,dict):return '{\n'+''.join(json.dumps(k)+' = '+fmt(v)+';\n' for k,v in x.items())+'}'
 if isinstance(x,list):return '('+','.join(fmt(v) for v in x)+')'
 return str(x) if isinstance(x,int) else json.dumps(x)
(project/'project.pbxproj').write_text('// !$*UTF8*$!\n'+fmt({'archiveVersion':1,'classes':{},'objectVersion':56,'objects':objects,'rootObject':pr}))
assets=root/'Assets.xcassets';icons=assets/'AppIcon.appiconset';icons.mkdir(parents=True,exist_ok=True)
(assets/'Contents.json').write_text(json.dumps({'info':{'author':'xcode','version':1}}))
images=[]
for size in [16,32,128,256,512]:
 for scale in [1,2]:
  file=f'icon_{size}x{size}'+('@2x' if scale==2 else '')+'.png'
  shutil.copy2(root.parent/'work/Binocular.iconset'/file,icons/file)
  images.append(dict(idiom='mac',size=f'{size}x{size}',scale=f'{scale}x',filename=file))
images.append(dict(idiom='universal',platform='ios',size='1024x1024',filename='icon_512x512@2x.png'))
(icons/'Contents.json').write_text(json.dumps({'images':images,'info':{'author':'xcode','version':1}},indent=2))
print(project)
