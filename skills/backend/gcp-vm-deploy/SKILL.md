---
name: gcp-vm-deploy
loop: dev
pdca: do
description: >
  Put a dockerized app (FastAPI + Next.js + PostgreSQL, compose) on its own Google Cloud VM inside
  a GCP project that other production systems already share: project checks, a separate VPC and
  firewall, reserved IP, SSH access when the operator has only the Editor role, the scripts the
  owner must run because Claude may not create cloud resources, production containers, Caddy
  HTTPS, backups to Cloud Storage, the one-time data move from a local stack, DNS hand-off to a
  network admin, and go-live. Learned on ChimesERP ERP-316 (2026-10-28).
  TRIGGER when: "部署到 GCP", "上雲端主機", "開一台 VM", "搬到雲端", "erp.xxx 上線", "給同事一個網址",
  deploying a compose app to a GCP VM, moving a local stack's data to a cloud VM, or a GCP SSH /
  IAP / firewall / static IP problem during such a deploy.
  DO NOT TRIGGER when: choosing a hosting platform (deploy), writing Dockerfiles or compose for
  local use only (docker-compose-setup), Cloudflare Tunnel exposure (cloudflare-tunnel-provision,
  tunnel-proxy-deploy), Cloud Run or GKE.
---

# gcp-vm-deploy

One VM, one compose stack, Caddy in front, backups to a bucket. The operator decides; Claude
prepares scripts, checks, and runs what it is allowed to run.

## 0. Rules that come first

- **Claude cannot create shared cloud resources.** The auto mode classifier refuses network,
  firewall, VM, service-account, bucket, and IAM changes in a shared project ("Modify Shared
  Resources"). Do not try another route. Write an idempotent script (`create-infra.sh`, each step
  `describe || create`), show what it creates, and let the owner run it with `! bash <path>`.
  Read-only `gcloud ... list/describe` is fine for Claude.
- **Never touch the other systems in the project.** List every VM, IP, and firewall rule first
  and name them in the plan as "not touched".
- **Confirm the money and exposure decisions in one question set:** region, machine type, disk,
  database on the VM versus a managed one, domain, and what data moves.
- **Secrets never reach the screen.** Build the VM `.env` with a script that reads the source
  `.env`, generates new database and JWT secrets, writes a mode 600 temp file, copies it, and
  deletes the temp file. Print only counts.

## 1. Read the project before the plan (read-only)

```bash
gcloud projects describe <project> --format='value(projectId,lifecycleState)'
gcloud billing projects describe <project> --format='value(billingEnabled)'
gcloud services list --enabled --format='value(config.name)'
gcloud compute instances list; gcloud compute addresses list; gcloud compute firewall-rules list
gcloud projects get-iam-policy <project> --flatten='bindings[].members' \
  --filter='bindings.members:user:<operator>' --format='value(bindings.role)'
dig +short NS <domain>; dig +short CAA <domain>
```

What these found on ChimesERP and what to do about each:

| Finding | Action |
|---|---|
| The `default` network allows 22 and 3389 from 0.0.0.0/0 with no target tags (every VM in it) | Make a separate VPC with only the rules you need. Do not edit the default rules (other VMs may depend on them). |
| A reserved, unused static IP named for the app | Use it. A reserved IP has a network tier; pass the same `--network-tier` (STANDARD here) or `instances create` fails: "has a different network tier STANDARD from ... PREMIUM". |
| The operator has `roles/editor` only | IAP SSH fails with `4033 'not authorized'`. IAP needs `roles/iap.tunnelResourceAccessor`, OS Login needs `roles/compute.osAdminLogin`, and a VM with a service account needs `roles/iam.serviceAccountUser`. An Editor cannot grant them; the project Owner can. |
| DNS at another registrar (Gandi) and the owner is not the admin | Give a ready-to-forward message (section 6). |

## 2. Infrastructure script (the owner runs it)

Contents of the ChimesERP version (`~/.claude/session-logs/ChimesERP/cloud/create-infra.sh`):

1. Enable `iap.googleapis.com` and `iam.googleapis.com`.
2. VPC `<app>-net` (custom subnet mode) and one subnet in the region.
3. Firewall: `tcp:80,443` from 0.0.0.0/0; `tcp:22` only from `35.235.240.0/20` (IAP); both with a
   target tag.
4. A VM service account with no project roles.
5. A backup bucket in the region, uniform access, lifecycle delete after N days, and
   `roles/storage.objectAdmin` for the VM service account on that bucket only.
6. The VM: Ubuntu LTS amd64, machine type, `pd-balanced` disk, `--address <reserved-ip>
   --network-tier <tier>`, the tag, Shielded VM flags, `enable-oslogin=TRUE`, the service account
   with the `devstorage.read_write` scope, a label.
7. A check that prints the VM state and the firewall rules of the new network.

The "disk larger than image" warning is harmless on Ubuntu (it grows the root at boot).

## 3. SSH when IAP is not ready

Ask the owner to choose. The fast path, used on ChimesERP until the Owner grants the IAP roles:

- Claude makes a dedicated key on the operator's Mac: `ssh-keygen -t ed25519 -N '' -f ~/.ssh/<app>_ed25519`.
- A second owner script adds a firewall rule `tcp:22` from the current public IP `/32` only
  (`curl -s https://api.ipify.org`), and puts the key in the VM metadata
  (`enable-oslogin=FALSE,ssh-keys="deploy:<pub>"`). Rerun it when the IP changes.
- Later: the Owner grants the three IAP roles, then delete the `/32` rule and turn OS Login on.

## 4. Production containers

The local stack often runs the frontend with `npm run dev`; the cloud needs images:

- `frontend/Dockerfile`: multi-stage `npm ci` → `npm run build` → `next start` as user `node`;
  the API address from the environment at run time.
- `deploy/cloud/compose.cloud.yml`, used with the base file: `ports: !reset []` on `db` and `api`
  (nothing but Caddy publishes), `restart: unless-stopped`, named volumes for uploads and data,
  `web`, and `caddy` (pinned image, 80 and 443, `caddy_data`, `caddy_config`).
- `deploy/cloud/Caddyfile`: the domain from the environment, HSTS, nosniff, frame deny,
  zstd/gzip, the request body limit the uploads need, `reverse_proxy web:3000`. Send `/api/*` to the
  frontend when the frontend checks the session and forwards to the API; sending it straight to
  the API skips that check.
- `scripts/ops/deploy-cloud.sh <sha>`: refuse `HEAD`; `git archive` the commit; copy to
  `/srv/<app>/releases/<sha>`; switch `current`; back up the database; build; `up -d`; wait for the
  health check; compare `alembic current` with the head file; keep the previous release for
  `--rollback`. The private `.env` stays in `/srv/<app>/shared/.env` (mode 600).
- `scripts/ops/backup-cloud.sh` plus a systemd timer: `pg_dump -Fc`, a tar of the file volumes,
  `gcloud storage cp` to the bucket, keep 7 local copies. Read the volumes with a one-off
  container (`compose run --rm --no-deps --entrypoint tar api ...`), not `exec` into the running
  api: a deploy calls the backup first, and an api that a failed run left stopped must not block it.
- Install on the VM: Docker CE from the Docker apt repository, the compose plugin,
  `unattended-upgrades`, the deploy user in the `docker` group.

## 5. Before DNS works

- Caddy asks Let's Encrypt for a certificate as soon as it starts. Without DNS every attempt fails
  and Let's Encrypt limits failed validations. **Stop `caddy` after every deploy until the name
  resolves to the VM.** `deploy-cloud.sh` starts it again (`up -d`), so every deploy before DNS is
  `deploy-cloud.sh <sha>` followed by `compose stop caddy`.
- Test inside the VM: from the `api` container, `urllib` GET `http://web:3000/login` (expect 200);
  an API path through the frontend without a session returns 401, which is correct.
- Internet scanners hit the IP within seconds of Caddy starting. Do not load real data before the
  site is on HTTPS with the real name.

## 6. DNS hand-off message (for a network admin)

Give the owner a message to forward: the domain and registrar, the record (`A`, name, value, TTL
300), why ports 80 and 443 must be reachable (automatic HTTPS), the CAA note (none now; allow
`letsencrypt.org` if one is added), and the Microsoft Entra redirect URI to add when the app uses
Microsoft sign-in.

## 7. Data move and go-live

1. Merge, then deploy the merged commit SHA (never a branch head).
2. Rehearse first, move for real at go-live: data written on the old stack after the move is lost.
   Run `scripts/ops/move-data-to-cloud.sh` from the machine that runs the source stack: it counts
   rows and files at the source, dumps, copies, backs up the target, refuses a target that already
   has users (unless `--force`), restores, starts (migrations run), and compares counts.
   - Restore into an EMPTY database (`dropdb --force` + `createdb`, then `pg_restore` without
     `--clean`). The target was migrated to a newer head than the dump; `pg_restore --clean` then
     fails with "cannot drop constraint users_pkey ... other objects depend on it" because the new
     tables reference it. After the restore, the `migrate` service upgrades the old schema to head.
   - The restore half runs the copy of the script that is deployed on the VM. A fix to the script
     needs a deploy before the rerun.
   - Start only `db migrate api scheduler web` after the restore; leave Caddy to go-live.
3. When `dig +short <name>` returns the VM IP: start `caddy`, check the certificate, sign in, and
   walk the main pages.
4. Point the other tools at the cloud (tracker CLI URL, agent credentials) and tell the team.

## Gotchas (ChimesERP, 2026-10-28)

- `gcloud` was not installed: `brew install --cask google-cloud-sdk`, then the owner runs
  `! gcloud auth login` and `! gcloud config set project <project>` (interactive).
- pip backtracking on the VM made the first backend build slow; it finished. Pin hard
  dependencies when it becomes a problem.
- Ubuntu GCP images install `gcloud` as a snap. A systemd service has no `/snap/bin` in its PATH,
  so the backup timer could not upload while a manual run could. Set
  `Environment=PATH=...:/snap/bin` in the unit and prove it with `systemctl start <unit>` plus
  `gcloud storage ls <bucket>`.
- Rehearsal results on ChimesERP: 3 tries. (1) `pg_restore --clean` into a newer schema failed;
  (2) the failed run left `api` stopped and the deploy's backup step needed it; (3) passed:
  row counts and the 41 upload files matched.
- Scripts that live on the owner's machine (`deploy-dev.sh`, rules files) block colleagues. Move
  them into `scripts/ops/` in the same ticket.
