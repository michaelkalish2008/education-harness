# Environments

Every project has its own Python environment, so a recommender project's torch never lands in a statistics project and a lesson's numbers come out the same next month. The harness writes `projects/<project>/pyproject.toml` (numpy and ipykernel to start) and a `.gitignore` for `.venv/` when a project is created, and adds them to older projects. Managing it is the tutor's job, done quietly: never ask the learner to create, activate or install anything, and don't narrate it beyond one line when something new is installed.

## Running code

- Run everything from the project folder with `uv run` (`uv run python examples/s1/example.py`). The first run builds `.venv/` from `pyproject.toml`; later runs reuse it.
- A package the code needs: `uv add <package>` in the project folder (it updates `pyproject.toml` and `uv.lock`). Never `pip install`, never a global or shared environment, never another project's environment.
- Notebooks: `uv run --with jupyter jupyter lab` from the project folder, or give the project its own kernel once with `uv run python -m ipykernel install --user --name <project>` and pick that kernel in VS Code or Jupyter.
- Keep `uv.lock` with the project: it pins versions so a saved example re-runs to the same `expected.json`.

## When uv is missing

Check with `command -v uv` (Windows: `where uv`). Assume a Mac unless the device says otherwise.

| Machine | Install |
| --- | --- |
| macOS (default) | `brew install uv` (Homebrew). If `brew` is missing, use the standalone installer below rather than installing Homebrew, which asks for the learner's password. |
| Linux | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Windows | `winget install --id=astral-sh.uv -e`, or `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` |

The standalone installer (`curl -LsSf https://astral.sh/uv/install.sh | sh`) also works on macOS and needs no password. If nothing can run commands on the learner's machine, give the one install line for their system and carry on with the lesson.

## Where the environment lives

`.venv/` is built on the machine that runs the code. An environment built in a cloud workspace or a Linux VM can't run on the learner's Mac, so files that travel to the learner are `pyproject.toml`, `uv.lock`, the scripts and notebooks; `.venv/` never does.
