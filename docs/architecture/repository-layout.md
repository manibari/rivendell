# Repository layout

The physical folders follow the owner of each rule or piece of data. Web, API, and CLI code call these modules through stable entry points.

```text
rivendell/
├── apps/
│   ├── dashboard-web/         Next.js UI
│   ├── dashboard-api/         FastAPI backend
│   │   ├── server.py          App assembly and startup
│   │   └── routes/            Agent, project, skill, workflow, monitoring APIs
│   ├── avatar-gateway/        Assistant channel adapter
│   └── dashboard-legacy/      Streamlit UI and shared dashboard library
├── platform/
│   ├── agent_fleet/           Agent registry, parser, management, runner source
│   ├── deployment/            Compose Dockerfiles, profiles, ports, service commands
│   │   └── cli.sh             Profile, up/down, environment, update commands
│   ├── monitoring/            Health, disk, usage, and service status
│   │   └── cli.sh             Cross-service status command
│   ├── projects/              Project data and synchronization
│   ├── release/               Release policy; canonical files still at root
│   ├── skill_catalog/         Hook, routing, and catalog rules and metadata
│   └── workflows/             Workflow map and role view
├── assistant/
│   ├── conversation/          Chat log
│   ├── dispatch/              Proposal and decision state machine
│   ├── personas/              Persona configuration and prompts
│   └── channels/              Mail and calendar adapters
├── knowledge/
│   ├── content/videos/        Notes, transcripts, index, subscriptions
│   └── entities/kg.py        Entity knowledge API; store in ~/.claude/knowledge/
├── skills/                   Canonical ability packages
├── bin/                      Stable CLI and scheduler commands
├── scripts/                  Compatibility entry points and remaining adapters
├── docs/                     Design, mockups, and archived plans
├── data/                     Compatibility paths for moved configuration
├── dispatch/                 Live proposal data, owned by sk dispatch
├── reports/                  Generated reports, owned by scheduled agents
└── VERSION, CHANGELOG.md, ROADMAP.md, docker-compose.yml
```

`dashboard-next`, `dashboard`, `gateway`, `agents`, and `dockerfiles` at the root are compatibility links. `profiles/` and `data/` contain links for old consumers. `apps/dashboard-web/api` points to the separate `apps/dashboard-api` folder for the existing API start script. The old `scripts/` paths for knowledge, dispatch, mail, and calendar, plus `bin/sk-projects-sync` and `bin/sk-disk-snapshot`, remain stable entry paths that point to their owners.

The API keeps its route modules in `apps/dashboard-api/routes/`; `server.py` assembles the app. Monitoring has health, disk, errors, Git, issues, and token usage subroutes. Agent, project, skill catalog, deployment, workflow, collaboration, and harvest routes have their own modules. The workflow map lives in `platform/workflows/` and is mounted into the API container for edits. The API still imports through `apps/dashboard-legacy/lib`. Agent, project, skill catalog, workflow role, and token usage implementations now live in their platform modules; the old library import paths link to them. Some agent and harvest behavior remains in the route modules and can move into domain services separately. Shared SQLite access still lives in the legacy library. `bin/sk` sources deployment and service status commands from their owning modules; other commands still share the main file. Release files, dispatch data, and generated reports retain their existing storage paths until their producers and consumers can move together.

`platform/` is a filesystem boundary, not a Python package name: importing it as `platform` would collide with Python's standard library module. Extracted Python implementations need a distinct import package name.

Ability packages stay under `skills/<category>/<name>/SKILL.md`. A script used only by one package stays with that package. Shared tools go to their owning module. External tools such as Playwright and Whisper are dependencies of the packages that use them.
