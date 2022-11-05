all: build/Release/5G-Check.app

icons := 5G-Check/Assets.xcassets/AppIcon.appiconset/icon_128x128.png \
	5G-Check/Assets.xcassets/AppIcon.appiconset/icon_128x128@2x.png \
	5G-Check/Assets.xcassets/AppIcon.appiconset/icon_16x16.png \
	5G-Check/Assets.xcassets/AppIcon.appiconset/icon_16x16@2x.png \
	5G-Check/Assets.xcassets/AppIcon.appiconset/icon_256x256.png \
	5G-Check/Assets.xcassets/AppIcon.appiconset/icon_256x256@2x.png \
	5G-Check/Assets.xcassets/AppIcon.appiconset/icon_32x32.png \
	5G-Check/Assets.xcassets/AppIcon.appiconset/icon_32x32@2x.png \
	5G-Check/Assets.xcassets/AppIcon.appiconset/icon_512x512.png \
	5G-Check/Assets.xcassets/AppIcon.appiconset/icon_512x512@2x.png

src := 5G-Check/CheckApp.swift \
	   5G-Check/ChartData.swift \
	   5G-Check/ContentView.swift \
	   5G-Check/GatewayState.swift

$(icons): 5G-Check/Assets.xcassets/5g-check.svg 5G-Check/Assets.xcassets/makeall.sh
	cd 5G-Check/Assets.xcassets && ./makeall.sh

build/Release/5G-Check.app: $(icons) $(src) 5G-Check-Info.plist
	xcodebuild build

