# CLAUDE.md

Este proyecto usa **AGENTS.md** como guía canónica. Léela e impórtala:

@AGENTS.md

## Notas específicas para Claude Code
- Antes de planificar trabajo grande, revisa **[`docs/ROADMAP.md`](docs/ROADMAP.md)** (plan por fases).
- **Reglas de Git no negociables** (detalle en AGENTS.md → "Reglas de Git"):
  - Nada se commitea/sube a `master`.
  - Cada tarea va en **su propio worktree + rama**; al terminar, **PR** hacia `master`.
  - **El merge lo hace el usuario.** El agente nunca hace merge/push a `master`.
  - CI con tests debe pasar antes del merge.
- **Dinero siempre en entero CLP.** Secretos solo en `.env`.
- Redes sociales: **solo APIs oficiales de Meta** (Instagram Graph / WhatsApp Cloud), nunca scraping.