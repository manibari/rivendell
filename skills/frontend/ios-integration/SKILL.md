---
name: ios-integration
loop: dev
pdca: do
description: >
  iOS system integration: App Extensions (Share, Widget), Deep Links,
  Universal Links, App Groups, permissions, and map SDK integration.
  TRIGGER when: user implements share extension, deep links, universal links,
  app groups, requests system permissions, or integrates maps.
  DO NOT TRIGGER when: pure SwiftUI UI layout, backend code, or Android.
tags: [frontend, ios, integration]
version: 1
source: manual
user_invocable: false
---

# iOS System Integration

## App Extensions

### Share Extension

**Architecture:**
- Separate target in Xcode with its own `Info.plist` and entitlements
- Memory limit: ~120 MB (much lower than host app)
- Cannot access host app's data directly — use App Groups

```swift
// ShareViewController.swift
import UIKit
import UniformTypeIdentifiers

class ShareViewController: UIViewController {
    override func viewDidLoad() {
        super.viewDidLoad()
        handleSharedItems()
    }

    private func handleSharedItems() {
        guard let extensionItems = extensionContext?.inputItems as? [NSExtensionItem] else {
            close()
            return
        }
        for item in extensionItems {
            for provider in item.attachments ?? [] {
                if provider.hasItemConformingToTypeIdentifier(UTType.url.identifier) {
                    provider.loadItem(forTypeIdentifier: UTType.url.identifier) { [weak self] item, error in
                        guard let url = item as? URL else { return }
                        self?.saveToSharedContainer(url: url)
                        self?.close()
                    }
                }
            }
        }
    }

    private func close() {
        extensionContext?.completeRequest(returningItems: nil)
    }
}
```

**Info.plist activation rules:**
```xml
<key>NSExtension</key>
<dict>
    <key>NSExtensionAttributes</key>
    <dict>
        <key>NSExtensionActivationRule</key>
        <dict>
            <key>NSExtensionActivationSupportsWebURLWithMaxCount</key>
            <integer>1</integer>
        </dict>
    </dict>
    <key>NSExtensionPointIdentifier</key>
    <string>com.apple.share-services</string>
    <key>NSExtensionPrincipalClass</key>
    <string>$(PRODUCT_MODULE_NAME).ShareViewController</string>
</dict>
```

### Widget Extension (WidgetKit)

```swift
struct MyWidget: Widget {
    let kind = "MyWidget"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: MyTimelineProvider()) { entry in
            MyWidgetView(entry: entry)
                .containerBackground(.fill.tertiary, for: .widget)
        }
        .configurationDisplayName("My Widget")
        .supportedFamilies([.systemSmall, .systemMedium])
    }
}

struct MyTimelineProvider: TimelineProvider {
    func placeholder(in context: Context) -> MyEntry {
        MyEntry(date: .now, data: .placeholder)
    }

    func getSnapshot(in context: Context, completion: @escaping (MyEntry) -> Void) {
        completion(MyEntry(date: .now, data: loadFromSharedContainer()))
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<MyEntry>) -> Void) {
        let entry = MyEntry(date: .now, data: loadFromSharedContainer())
        let nextUpdate = Calendar.current.date(byAdding: .minute, value: 15, to: .now)!
        completion(Timeline(entries: [entry], policy: .after(nextUpdate)))
    }
}
```

**Key constraints:**
- Widgets cannot run arbitrary code — timeline-based updates only
- Use `WidgetCenter.shared.reloadTimelines(ofKind:)` from host app to force refresh
- Tap targets use `widgetURL(_:)` (whole widget) or `Link` (per-element)

## Deep Links

### URL Scheme

```swift
// Register in Info.plist or target settings
// URL Types → URL Schemes: "myapp"
// Result: myapp://path/to/content

// Handle in SwiftUI
@main
struct MyApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .onOpenURL { url in
                    DeepLinkRouter.shared.handle(url)
                }
        }
    }
}
```

### Universal Links (AASA)

**Apple App Site Association file** — host at `https://yourdomain.com/.well-known/apple-app-site-association`:

```json
{
  "applinks": {
    "apps": [],
    "details": [
      {
        "appID": "TEAMID.com.example.myapp",
        "paths": ["/share/*", "/invite/*"],
        "components": [
          { "/": "/share/*", "comment": "Shared content" },
          { "/": "/invite/*", "comment": "Invite links" }
        ]
      }
    ]
  }
}
```

**Requirements:**
- HTTPS only (no HTTP)
- Content-Type: `application/json`
- No redirects on the AASA file itself
- Add Associated Domains entitlement: `applinks:yourdomain.com`

### Deep Link Router Pattern

```swift
@MainActor
@Observable
final class DeepLinkRouter {
    static let shared = DeepLinkRouter()

    var pendingRoute: Route?

    func handle(_ url: URL) {
        guard let components = URLComponents(url: url, resolvingAgainstBaseURL: true) else { return }

        switch components.host ?? components.path {
        case "share":
            if let id = components.queryItems?.first(where: { $0.name == "id" })?.value {
                pendingRoute = .sharedContent(id: id)
            }
        case "invite":
            if let code = components.queryItems?.first(where: { $0.name == "code" })?.value {
                pendingRoute = .invite(code: code)
            }
        default:
            break
        }
    }
}
```

## App Groups

### Setup

1. Enable App Groups capability in both host app and extension targets
2. Use same group identifier: `group.com.example.myapp`

### Shared UserDefaults

```swift
// Write (from host app or extension)
let shared = UserDefaults(suiteName: "group.com.example.myapp")
shared?.set(value, forKey: "sharedKey")

// Read (from either target)
let value = shared?.string(forKey: "sharedKey")
```

### Shared File Container

```swift
let containerURL = FileManager.default
    .containerURL(forSecurityApplicationGroupIdentifier: "group.com.example.myapp")!

let fileURL = containerURL.appendingPathComponent("shared_data.json")

// Write
try data.write(to: fileURL)

// Read
let data = try Data(contentsOf: fileURL)
```

### Shared Core Data / SwiftData

```swift
// Point the persistent store to the shared container
let containerURL = FileManager.default
    .containerURL(forSecurityApplicationGroupIdentifier: "group.com.example.myapp")!
let storeURL = containerURL.appendingPathComponent("Model.sqlite")

// For SwiftData
let config = ModelConfiguration(url: storeURL)
let container = try ModelContainer(for: MyModel.self, configurations: config)
```

## Permissions

### Request UX Best Practices

1. **Ask at the moment of need** — not at app launch
2. **Pre-prompt with explanation** — show a custom UI explaining why before the system dialog
3. **Handle denial gracefully** — always provide a fallback UI
4. **Never ask twice without value** — if denied, show "Go to Settings" guidance

### Location Permission Pattern

```swift
import CoreLocation

@MainActor
@Observable
final class LocationManager: NSObject, CLLocationManagerDelegate {
    private let manager = CLLocationManager()
    var authorizationStatus: CLAuthorizationStatus = .notDetermined
    var lastLocation: CLLocation?

    override init() {
        super.init()
        manager.delegate = self
    }

    func requestWhenInUse() {
        manager.requestWhenInUseAuthorization()
    }

    func requestAlways() {
        // Must request WhenInUse first, then upgrade to Always
        manager.requestAlwaysAuthorization()
    }

    nonisolated func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        Task { @MainActor in
            authorizationStatus = manager.authorizationStatus
        }
    }

    nonisolated func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        Task { @MainActor in
            lastLocation = locations.last
        }
    }
}
```

### Info.plist Description Strings

Always provide clear, user-facing descriptions:

```xml
<key>NSLocationWhenInUseUsageDescription</key>
<string>We use your location to show you on the shared map.</string>

<key>NSLocationAlwaysAndWhenInUseUsageDescription</key>
<string>Background location lets your partner see your real-time position.</string>

<key>NSCameraUsageDescription</key>
<string>Camera access is needed to take profile photos.</string>

<key>NSPhotoLibraryUsageDescription</key>
<string>Photo library access lets you choose a profile picture.</string>
```

### Fallback UI When Permission Denied

```swift
struct LocationDeniedView: View {
    var body: some View {
        ContentUnavailableView {
            Label("Location Access Required", systemImage: "location.slash")
        } description: {
            Text("Enable location access in Settings to use the shared map.")
        } actions: {
            Button("Open Settings") {
                if let url = URL(string: UIApplication.openSettingsURLString) {
                    UIApplication.shared.open(url)
                }
            }
        }
    }
}
```

## Maps

### MapKit (iOS 17+)

```swift
import MapKit

struct MapView: View {
    @State private var position: MapCameraPosition = .userLocation(fallback: .automatic)
    let annotations: [MyAnnotation]

    var body: some View {
        Map(position: $position) {
            UserAnnotation()  // blue dot

            ForEach(annotations) { annotation in
                Annotation(annotation.title, coordinate: annotation.coordinate) {
                    Image(systemName: "mappin.circle.fill")
                        .foregroundStyle(.red)
                }
            }
        }
        .mapControls {
            MapUserLocationButton()
            MapCompass()
            MapScaleView()
        }
    }
}
```

### MapKit vs Google Maps SDK

| Criteria | MapKit | Google Maps SDK |
|----------|--------|----------------|
| Cost | Free | Free tier + pay per use |
| Setup | Built-in, no API key | Requires SDK + API key |
| Styling | Limited (iOS 16+ MapStyle) | Full custom styling |
| Street View | No | Yes |
| Offline maps | No | Limited |
| Cross-platform | Apple only | iOS + Android |
| SwiftUI support | Native (iOS 17+) | UIViewRepresentable wrapper |

**Default choice: Use MapKit unless you need cross-platform parity or Google-specific features.**

### Annotation Clustering

```swift
// For MKMapView (UIKit) — use MKClusterAnnotation
// For SwiftUI Map (iOS 17+) — clustering is automatic with Annotation
// For custom clustering logic, use MKMapView via UIViewRepresentable

struct ClusterableMapView: UIViewRepresentable {
    let annotations: [MKAnnotation]

    func makeUIView(context: Context) -> MKMapView {
        let map = MKMapView()
        map.register(MKMarkerAnnotationView.self,
                     forAnnotationViewWithReuseIdentifier: MKMapViewDefaultAnnotationViewReuseIdentifier)
        map.register(MKMarkerAnnotationView.self,
                     forAnnotationViewWithReuseIdentifier: MKMapViewDefaultClusterAnnotationViewReuseIdentifier)
        return map
    }

    func updateUIView(_ map: MKMapView, context: Context) {
        map.removeAnnotations(map.annotations)
        map.addAnnotations(annotations)
    }
}
```

## Integration Checklist

Before shipping any system integration, verify:

- [ ] App Group identifier matches across all targets
- [ ] Extension Info.plist has correct activation rules
- [ ] Universal Links AASA file is accessible via HTTPS with no redirects
- [ ] All permission description strings are clear and specific
- [ ] Fallback UI exists for every denied permission
- [ ] Deep link router handles unknown/malformed URLs gracefully
- [ ] Widget timeline updates are not too frequent (battery impact)
- [ ] Extension memory usage stays under limits (~120 MB for Share, ~30 MB for Widget)
