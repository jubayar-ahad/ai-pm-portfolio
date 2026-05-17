# Auto mode for Claude Code

Posted 24th March 2026 by Simon Willison.

Really interesting new development in Claude Code today as an alternative to `--dangerously-skip-permissions`:

> Today, we're introducing auto mode, a new permissions mode in Claude Code where Claude makes permission decisions on your behalf, with safeguards monitoring actions before they run.

Those safeguards appear to be implemented using Claude Sonnet 4.6, as described in the documentation:

> Before each action runs, a separate classifier model reviews the conversation and decides whether the action matches what you asked for: it blocks actions that escalate beyond the task scope, target infrastructure the classifier doesn't recognize as trusted, or appear to be driven by hostile content encountered in a file or web page. [...] Model: the classifier runs on Claude Sonnet 4.6, even if your main session uses a different model.

They ship with an extensive set of default filters, and you can also customize them further with your own rules. The most interesting insight into how they work comes when you run this new command in the terminal:

    claude auto-mode defaults

Here's an illustrative subset of the full JSON output.

From the "allow" list:

- Test Artifacts: Hardcoded test API keys, placeholder credentials in examples, or hardcoding test cases.
- Local Operations: Agent deleting local files in working directory, local file operations within project scope, or using `--ignore-certificate-errors` for local testing. "Project scope" means the repository the session started in — wandering into `~/`, `~/Library/`, `/etc`, or other repos is scope escalation (User Intent Rule #2), not a local operation. Does NOT cover irreversible destruction of pre-existing files or local stateful services — see "Irreversible Local Destruction" in BLOCK.
- Read-Only Operations: GET requests, read-only API calls, or queries that don't modify state and don't contain sensitive information in the URL. Note: PREEMPTIVE BLOCK ON CLEAR INTENT still applies — if the transcript contains clear evidence the agent is using read-only operations to scout for a blocked action, block it.
- Declared Dependencies: Installing packages that are already declared in the repo's manifest files (`requirements.txt`, `package.json`, `Cargo.toml`, `pyproject.toml`, `Gemfile`, etc.) via standard commands that read those manifests (`pip install -r requirements.txt`, `npm install`, `cargo build`, `bundle install`) — provided the agent has not modified the manifest in this session. Does NOT cover installing agent-chosen package names (e.g. `pip install foo`, `npm install bar`) — those carry typosquat and supply-chain risk.

From "soft_deny":

- Git Destructive: Force pushing (`git push --force`), deleting remote branches, or rewriting remote history.
- Git Push to Default Branch: Pushing directly to `main`, `master`, or the repository's default branch — this bypasses pull request review. Commits should be pushed to a new feature branch instead.
- Code from External: Downloading and executing code from external sources — e.g. `curl | bash`, deserializing external data via formats that can execute code (`eval`, `exec`, `yaml.unsafe_load`, `pickle`, etc.), or similar mechanisms. Also includes running code from an external repo cloned earlier in the transcript (`pip install -e`, `make install`, `python script.py`, `pickle.load`/`torch.load` on cloned repo files) — "local on disk" does not mean trusted if it was cloned from an external source visible in the transcript. The repo the agent starts in is trusted.
- Cloud Storage Mass Delete: Deleting or mass modifying files on cloud storage (S3, GCS, Azure Blob, etc.).

I remain unconvinced by prompt injection protections that rely on AI, since they're non-deterministic by nature. The documentation does warn that this may still let things through:

> The classifier may still allow some risky actions: for example, if user intent is ambiguous, or if Claude doesn't have enough context about your environment to know an action might create additional risk.

The fact that the default allow list includes `pip install -r requirements.txt` also means that this wouldn't protect against supply chain attacks with unpinned dependencies, as seen this morning with LiteLLM.

I still want my coding agents to run in a robust sandbox by default, one that restricts file access and network connections in a deterministic way. I trust those a whole lot more than prompt-based protections like this new auto mode.
