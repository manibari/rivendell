# User Flow: Port Map Page

**Feature:** `port-map`
**Route:** `/ports` in `dashboard-next`
**Source:** `docs/requirements/port-map.md`

---

## Happy Path

```mermaid
flowchart TD
    A([User navigates to /ports]) --> B[Page loads]
    B --> C{docker-compose.yml\naccessible via API?}

    C -->|Yes| D[Parse port mappings\nfrom docker-compose.yml]
    C -->|No| ERR1[Show error banner:\ncannot read config]

    D --> E[Render declared ports\nwith pending status]
    E --> F[Scan local TCP listeners\nvia dashboard API]

    F --> G{Declared port has\nlocal listener?}
    G -->|Yes| H[Badge: 🟢 live]
    G -->|No| I[Badge: 🔴 declared-only]
    F --> W{Listener is not\ndeclared in compose?}
    W -->|Yes| Z[Add row:\n🟡 wild]
    F -->|Scan error| J[Badge: ❓ unknown]

    H --> K[Table fully rendered]
    I --> K
    Z --> K
    J --> K

    K --> L{User action?}

    L -->|Click web port row| M[Open localhost:PORT\nin new tab]
    L -->|Click DB/Cache row| N[No action\nrow is non-clickable]
    L -->|Click Refresh| O[Re-run listener scan\nspinners shown briefly]
    O --> F

    M --> P((Service opens in browser))
    ERR1 --> Q((Error state shown,\nno crash))
```

---

## Error & Edge Branches

```mermaid
flowchart TD
    subgraph Edge Cases
        E1[docker-compose.yml\nnot found] --> X1[Show banner:\nConfig not found]
        E2[API server down] --> X2[Show banner:\nDashboard API unreachable]
        E3[Listener scan fails] --> X3[Show compose rows as unknown\nnot blank/crash]
        E4[Service was declared-only,\nuser clicks Refresh,\nservice now live] --> X4[Badge updates\ndeclared-only → live]
    end
```

---

## Screen Inventory

| # | Screen / State | Purpose | Key Elements |
|---|---|---|---|
| 1 | Port Map — loading | Page skeleton while fetching | Table rows with spinner in status column |
| 2 | Port Map — populated | Main view | Port col, Service col, Container col, Status badge, Link icon |
| 3 | Port Map — error (config missing) | Config not accessible | Error banner at top, empty table body |
| 4 | Port Map — error (API down) | Dashboard API unreachable | Full-page error state |
| 5 | Status badge: live | Service reachable | Green dot + "live" text |
| 6 | Status badge: declared-only | Declared port is not listening | Red dot + "declared-only" text |
| 7 | Status badge: wild | Listener not declared in compose | Yellow dot + "wild" text |
| 8 | Status badge: unknown | Listener scan failed | Yellow dot + "unknown" text |
| 9 | Row — web service | Clickable, opens localhost:PORT | Entire row or ExternalLink icon is clickable |
| 10 | Row — DB/Cache service | Non-clickable | Link icon absent or visually disabled |
| 11 | Refresh button — active | Re-check all statuses | Spinner animation while checking |

---

## Notes

- **Status check mechanism**: the dashboard-api backend compares compose declarations with local TCP listeners (avoids CORS issues and stale compose false positives)
- **Grouping**: rows grouped by service (news-stock: 3 ports together) with visual separator
- **Port type inference**: ports ≤ 5999 that are 5432/6379 → no-link; ports 3000–3999 → frontend; 8000–8999 → API/backend
