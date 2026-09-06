---
name: swiftui-patterns
loop: dev
pdca: do
description: >
  SwiftUI architecture patterns and best practices for iOS 17+ apps.
  TRIGGER when: user builds SwiftUI views, designs MVVM architecture,
  writes @Observable models, handles navigation, or asks about SwiftUI patterns.
  DO NOT TRIGGER when: working on backend/server code, Android, or web frontend.
tags: [frontend, ios, swiftui]
version: 1
source: manual
user_invocable: false
---

# SwiftUI Patterns (iOS 17+)

## @Observable vs ObservableObject

### Decision Guide

| Criteria | @Observable (iOS 17+) | ObservableObject |
|----------|----------------------|------------------|
| Minimum target | iOS 17 | iOS 13 |
| Property tracking | Automatic (per-property) | Manual (`@Published`) |
| View injection | `@State`, `@Environment` | `@StateObject`, `@EnvironmentObject` |
| Performance | Better — only re-renders on accessed property change | Re-renders on any `@Published` change |
| Nesting | Works naturally | Requires manual `objectWillChange` forwarding |

**Default choice: Use `@Observable` for iOS 17+ projects.**

### @Observable Pattern

```swift
@Observable
final class UserViewModel {
    var name: String = ""
    var email: String = ""
    var isLoading: Bool = false

    // Properties not accessed in View body won't trigger re-render
    var lastFetchDate: Date?

    func load() async {
        isLoading = true
        defer { isLoading = false }
        // fetch data...
    }
}

struct UserView: View {
    @State private var viewModel = UserViewModel()

    var body: some View {
        // Only re-renders when name or isLoading changes
        // (not email or lastFetchDate, since they're not read here)
        VStack {
            Text(viewModel.name)
            if viewModel.isLoading {
                ProgressView()
            }
        }
        .task { await viewModel.load() }
    }
}
```

### When to Use ObservableObject

- Targeting iOS 15/16
- Library code that must support older OS versions
- Combine pipeline integration with `$property` publishers

## MVVM Architecture

### ViewModel Lifecycle

```swift
// ViewModel owned by the View that creates it
struct ParentView: View {
    @State private var viewModel = ParentViewModel()  // owns lifecycle

    var body: some View {
        ChildView(viewModel: viewModel)  // passes reference, no @State
    }
}

struct ChildView: View {
    var viewModel: ParentViewModel  // plain property — does NOT own lifecycle

    var body: some View {
        Text(viewModel.title)
    }
}
```

**Rules:**
- The **creating** view uses `@State private var viewModel`
- **Child** views receive it as a plain `var` (not `@State`, not `@Bindable`)
- Use `@Bindable` only when child needs two-way binding: `@Bindable var viewModel`
- Never create ViewModel in `init()` — use `@State` default value or `.task`

### Dependency Injection via Environment

```swift
// Define environment key
extension EnvironmentValues {
    @Entry var authService: AuthServiceProtocol = AuthService.shared
}

// Inject
ContentView()
    .environment(\.authService, mockAuthService)

// Consume
struct ProfileView: View {
    @Environment(\.authService) private var authService
}
```

## Strict Concurrency (Swift 6 Readiness)

### @MainActor

```swift
// ViewModel that updates UI state MUST be @MainActor
@MainActor
@Observable
final class SettingsViewModel {
    var settings: [Setting] = []

    func load() async {
        // This runs on MainActor — safe to update published state
        let fetched = await settingsService.fetchAll()
        settings = fetched  // safe: we're on @MainActor
    }
}
```

### Sendable

```swift
// Value types are implicitly Sendable
struct UserDTO: Sendable {
    let id: String
    let name: String
}

// For classes, use @unchecked Sendable only with internal synchronization
final class TokenStore: @unchecked Sendable {
    private let lock = NSLock()
    private var _token: String?

    var token: String? {
        lock.withLock { _token }
    }
}
```

### nonisolated

```swift
@MainActor
@Observable
final class MapViewModel {
    var annotations: [MapAnnotation] = []

    // Heavy computation — opt out of MainActor
    nonisolated func processCoordinates(_ coords: [CLLocationCoordinate2D]) -> [MapAnnotation] {
        // Runs on caller's executor, not MainActor
        coords.map { MapAnnotation(coordinate: $0) }
    }

    func updateAnnotations(_ coords: [CLLocationCoordinate2D]) async {
        let processed = processCoordinates(coords)
        annotations = processed  // back on MainActor
    }
}
```

### Common Concurrency Patterns

```swift
// Task cancellation
struct SearchView: View {
    @State private var searchTask: Task<Void, Never>?

    var body: some View {
        TextField("Search", text: $query)
            .onChange(of: query) { _, newValue in
                searchTask?.cancel()
                searchTask = Task {
                    try? await Task.sleep(for: .milliseconds(300))
                    guard !Task.isCancelled else { return }
                    await viewModel.search(newValue)
                }
            }
    }
}
```

## Navigation

### NavigationStack + Path-Based Routing

```swift
enum Route: Hashable {
    case detail(itemId: String)
    case settings
    case profile(userId: String)
}

struct RootView: View {
    @State private var path = NavigationPath()

    var body: some View {
        NavigationStack(path: $path) {
            HomeView(path: $path)
                .navigationDestination(for: Route.self) { route in
                    switch route {
                    case .detail(let id):
                        DetailView(itemId: id)
                    case .settings:
                        SettingsView()
                    case .profile(let userId):
                        ProfileView(userId: userId)
                    }
                }
        }
    }
}

// Navigate programmatically
path.append(Route.detail(itemId: "abc"))

// Pop to root
path.removeLast(path.count)
```

### Tab + Navigation Composition

```swift
struct MainTabView: View {
    @State private var selectedTab = 0
    @State private var homePath = NavigationPath()
    @State private var profilePath = NavigationPath()

    var body: some View {
        TabView(selection: $selectedTab) {
            NavigationStack(path: $homePath) {
                HomeView()
            }
            .tag(0)

            NavigationStack(path: $profilePath) {
                ProfileView()
            }
            .tag(1)
        }
    }
}
```

## View Composition

### Extract Small Views

```swift
// Prefer: small, focused views
struct UserRow: View {
    let user: User

    var body: some View {
        HStack {
            AvatarView(url: user.avatarURL)
            VStack(alignment: .leading) {
                Text(user.name).font(.headline)
                Text(user.email).font(.caption).foregroundStyle(.secondary)
            }
        }
    }
}
```

### ViewModifier for Reusable Styling

```swift
struct CardModifier: ViewModifier {
    func body(content: Content) -> some View {
        content
            .padding()
            .background(.regularMaterial)
            .clipShape(RoundedRectangle(cornerRadius: 12))
            .shadow(radius: 2)
    }
}

extension View {
    func cardStyle() -> some View {
        modifier(CardModifier())
    }
}
```

### PreferenceKey for Child-to-Parent Communication

```swift
struct SizePreferenceKey: PreferenceKey {
    static var defaultValue: CGSize = .zero
    static func reduce(value: inout CGSize, nextValue: () -> CGSize) {
        value = nextValue()
    }
}

// Child reports its size
Text("Measure me")
    .background(GeometryReader { geo in
        Color.clear.preference(key: SizePreferenceKey.self, value: geo.size)
    })

// Parent reads it
.onPreferenceChange(SizePreferenceKey.self) { size in
    childSize = size
}
```

## Anti-Patterns

### Do NOT:

1. **Create ViewModel in `var body`** — causes recreation every render
   ```swift
   // BAD
   var body: some View {
       let vm = MyViewModel()  // recreated every render!
   }
   // GOOD: use @State private var vm = MyViewModel()
   ```

2. **Use `@ObservedObject` for owned state** — doesn't own lifecycle, resets on parent re-render
   ```swift
   // BAD: @ObservedObject private var vm = MyViewModel()
   // GOOD: @StateObject private var vm = MyViewModel()   (pre-iOS 17)
   // GOOD: @State private var vm = MyViewModel()          (iOS 17+)
   ```

3. **Force-unwrap optionals in View body** — crashes are unrecoverable in SwiftUI

4. **Mutate @State from background thread** — use `@MainActor` or `await MainActor.run {}`

5. **Deep view hierarchy without extraction** — if body exceeds ~30 lines, extract subviews

6. **Use AnyView for type erasure** — kills diffing performance. Prefer `@ViewBuilder` or `Group`
