
Troubleshooting

Container exits with signal 9

Possible causes: out of memory on the VPS, Docker daemon killing the container.
What to do: run docker stats, inspect dmesg for OOM killer activity, reduce worker concurrency.

Port conflicts

What to do: run ss -tulpn | grep -E ':80|:443|:3000|:5432|:9000|:9001', stop conflicting services.

API health fails after deploy

What to do: inspect docker compose logs api, test connectivity to postgres and redis.
