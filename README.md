# RCA-Sentinel

Autonomous, knowledge-graph-driven Root Cause Analysis (RCA) and remediation platform for high-precision manufacturing.

The full codebase, documentation, setup guides, and architecture references are located in [`rca-sentinel/`](./rca-sentinel/):

- **Main Documentation**: [rca-sentinel/README.md](./rca-sentinel/README.md)
- **Engineering Rules & Constraints**: [rules.md](./rules.md)
- **Backend Application**: [rca-sentinel/backend/](./rca-sentinel/backend/)
- **Frontend Console**: [rca-sentinel/frontend/](./rca-sentinel/frontend/)
- **Docker Orchestration**: [rca-sentinel/docker-compose.yml](./rca-sentinel/docker-compose.yml)
- **Developer Makefile**: [rca-sentinel/Makefile](./rca-sentinel/Makefile)

To get started:
```bash
cd rca-sentinel
cp .env.example .env
make up
make seed
```
