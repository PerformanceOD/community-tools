# Community Tools

Practice automation tools built and proven at IVA, packaged for independent practices.

> **This project is known by several names as it evolves:**
> - **PerformanceOD** — the practice automation company
> - **Open Source OD** / **OSOD** — the open-source community vision
> - Same mission regardless of name: give independent practitioners the automation tools that corporate chains keep locked away.

## How These Tools Work

Each tool is a self-contained folder with:
- `README.md` — what it does, who it's for, how to install
- `install.sh` — one-command setup (adapts to your environment)
- All source files needed to run
- Fully reversible — delete the folder to undo

## Available Tools

See [registry.yaml](registry.yaml) for the full list with requirements and compatibility.

## Principles

1. **Built at IVA first** — every tool here was tested in a live practice before sharing
2. **Reversible** — you can always undo. No tool modifies your existing systems permanently
3. **Self-contained** — no hidden dependencies. What's in the folder is what you need
4. **Practitioner-built** — by a practicing O.D., not a dev shop. These solve real practice problems
5. **No vendor lock-in** — works with your stack. Adapts to your paths, your repos, your agents

## For Contributors

If you've built something useful for your practice and want to share:
1. Package it as a self-contained folder
2. Include a README with install/uninstall instructions
3. Add an entry to `registry.yaml`
4. Submit a PR or post in the community

## License

Tools are shared under the same license as the parent project. See root LICENSE for details.
