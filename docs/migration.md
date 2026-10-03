# Mac application to Coolify
Preparation is allowed; production cutover requires owner approval after the
relevant foundation and workload gates pass.

1. Inventory repository/SHA, runtimes, ports, database, workers/schedules, Redis,
   uploads/volumes, integrations/webhooks, and secret references. Do not assume a
   database type or copy .env into Git.
2. Add reproducible Dockerfile/Compose, health/readiness checks, persistent storage,
   restart policy, non-root runtime where supported, and CPU/RAM limits. Reserve
   resources for Coolify and avoid simultaneous heavy builds.
3. Back up the Mac database and files; keep an independent encrypted copy and test
   restoring it into isolated staging. Platform backups do not cover app data.
4. Deploy staging through a reviewed app-scoped path. Enter secrets privately.
   Disable live schedules/customer notifications/payments until approved. Verify
   login, writes, uploads, jobs, integrations, resource use, HTTPS, and restored data.
5. Record exact SHA, maintenance window, quiescing writers, final backup, restore
   evidence, DNS/webhooks, health checks, approval, and rollback. Resolve scheduled
   independent backups, external monitoring, and foundation gates before client launch.
6. Switch only after approval; keep Mac rollback available. Avoid both copies
   processing queues/schedules. Define how post-cutover writes survive rollback;
   changing DNS back alone cannot preserve them. Retire Mac hosting after acceptance.

Keep changes/evidence in a private log. App deployment remains separate from
privileged server maintenance.
