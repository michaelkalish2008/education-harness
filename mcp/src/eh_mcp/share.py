"""Share-out and retrospectives: where the work meets other people, and looking back on it.

- Every project names an audience at the start ("who would you show this to?"): one
  person, a group, or the public. Preparing to teach helps learning; actually teaching
  helps it last. The audience lives in ``.private/share/<project>/audience.yaml``.
- The share-out is the project's last step (format ``share-out``): a five-minute
  walkthrough, a post, a one-page explainer or a show-and-tell. Drafts are built from the
  learner's own words and kept as versions; the harness never posts anything.
- ``mark_shared`` records that it happened, closes the share-out step and adds the moment to
  the learner's shared moments. ``heard_back`` keeps how it landed: reactions and questions.
- A retrospective is the learner's own look back on a project or a period, in their words.
  It feeds the retrospective report.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import re
import shutil

import yaml

if TYPE_CHECKING:
    from .core import Workspace

AUDIENCE_KINDS = ("person", "group", "public")
FORMATS = ("walkthrough", "post", "explainer", "show-and-tell", "portfolio")
# A portfolio piece is optional for any lesson: a package of the learner's work, in their words,
# written to projects/<project>/portfolio/<target>/. The learner publishes it; the harness never does.
PORTFOLIO_TARGETS = {
    "github": {"needs": "README.md", "does": "a folder ready to become a GitHub repository"},
    "web": {"needs": "index.html", "does": "a self-contained web page for any site or host"},
    "post": {"needs": ("post.md", "post.txt"), "does": "a post for a blog, Substack, LinkedIn or similar"},
    "other": {"needs": None, "does": "any other format the learner asks for (slides, notebook, PDF source)"},
}
PORTFOLIO_EXTS = {".md", ".txt", ".html", ".css", ".js", ".svg", ".py", ".ipynb", ".csv", ".json", ".yaml",
                  ".yml", ".toml", ".r", ".sql", ".tex", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf"}
PORTFOLIO_MAX_BYTES = 5_000_000
GITHUB_GITIGNORE = ".DS_Store\n__pycache__/\n.venv/\n.ipynb_checkpoints/\n"
RETRO_QUESTIONS = ("went_well", "was_hard", "surprised", "differently", "how_i_learn", "sharing", "next")


def _read(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return yaml.safe_load(path.read_text(encoding="utf-8")) or default


def _write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    tmp.replace(path)


class Share:
    def __init__(self, ws: "Workspace"):
        self.ws = ws

    def _dir(self, project: str) -> Path:
        from .core import _check_name
        return self.ws.private / "share" / _check_name(project, "project")

    # ------------------------------------------------------------------ audience
    def set_audience(self, project: str, audience: str, kind: str = "person", format: str = "walkthrough",
                     where: str = "") -> dict:
        """Who the learner would show this project to, as they put it ('my team', 'my sister',
        'LinkedIn'), never a name; the kind of audience; the share-out format; where, for a post."""
        from .core import HarnessError, _now
        self.ws._require_project(project)
        if not (audience or "").strip():
            raise HarnessError("Ask who they'd show it to: one person, a group, or a public post.")
        if kind not in AUDIENCE_KINDS:
            raise HarnessError(f"kind must be one of {AUDIENCE_KINDS}.")
        if format not in FORMATS:
            raise HarnessError(f"format must be one of {FORMATS}.")
        f = self._dir(project) / "audience.yaml"
        old = _read(f, {}) or {}
        data = {"schema": 1, "audience": audience.strip(), "kind": kind, "format": format,
                "where": (where or "").strip(), "set": old.get("set") or _now().isoformat(timespec="minutes")}
        _write(f, data)
        return {"saved": str(f.relative_to(self.ws.root)), **data}

    def get_share(self, project: str) -> dict:
        """The project's audience, drafts, whether it has been shared, and how it landed."""
        d = self._dir(project)
        drafts = sorted(d.glob("draft-*.md")) if d.exists() else []
        return {"audience": _read(d / "audience.yaml"),
                "drafts": [str(p.relative_to(self.ws.root)) for p in drafts],
                "latest_draft": drafts[-1].read_text(encoding="utf-8") if drafts else "",
                "shared": _read(d / "shared.yaml", {}).get("events", []) if d.exists() else [],
                "heard_back": _read(d / "heard_back.yaml", {}).get("items", []) if d.exists() else []}

    # -------------------------------------------------------------------- drafts
    def save_share_draft(self, project: str, text: str, format: str = "") -> dict:
        """Save a version of the share-out. Built from the learner's own words; each save is
        a new version, so nothing they wrote is overwritten."""
        from .core import HarnessError
        self.ws._require_project(project)
        if not (text or "").strip():
            raise HarnessError("The draft is empty.")
        d = self._dir(project)
        n = len(list(d.glob("draft-*.md"))) + 1 if d.exists() else 1
        f = d / f"draft-{n:02d}.md"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text.strip() + "\n", encoding="utf-8")
        step = self._share_step(project)
        if step:
            self.ws.record_attempt(project, step, f"[share-out draft {n}]\n{text.strip()}")
        return {"saved": str(f.relative_to(self.ws.root)), "version": n,
                "format": format or (_read(d / "audience.yaml", {}) or {}).get("format", "")}

    def _share_step(self, project: str) -> str:
        for s in self.ws.get_plan(project).get("steps", []):
            if s.get("format") == "share-out":
                return s["id"]
        return ""

    # -------------------------------------------------------------------- shared
    def mark_shared(self, project: str, how: str, where: str = "", who: str = "", link: str = "",
                    note: str = "") -> dict:
        """The learner shared it (they did, not the harness). Records the moment, closes the
        share-out step as drafted, and adds it to their shared moments."""
        from .core import HarnessError, _now
        self.ws._require_project(project)
        if how not in ("explained", "showed", "posted", "presented", "sent"):
            raise HarnessError("how must be explained, showed, posted, presented or sent.")
        d = self._dir(project)
        f = d / "shared.yaml"
        data = _read(f, {}) or {"schema": 1, "events": []}
        ev = {"at": _now().isoformat(timespec="minutes"), "how": how}
        for k, v in (("where", where), ("who", who), ("link", link), ("note", note)):
            if v.strip():
                ev[k] = v.strip()
        data["events"].append(ev)
        _write(f, data)
        step = self._share_step(project)
        text = note.strip() or f"{how.capitalize()} the project" + (f" to {who}" if who else "") + \
            (f" on {where}" if where else "")
        self.ws.reports.record_shared({"posted": "showed", "presented": "showed", "sent": "showed"}.get(how, how),
                                      text, who=who, project=project, step=step)
        out: dict[str, Any] = {"shared": ev}
        if step:
            prog = self.ws.get_progress(project)["steps"].get(step, {})
            if not prog.get("attempts"):
                self.ws.record_attempt(project, step, f"[shared] {text}")
            if prog.get("status") not in ("drafted", "defended"):
                self.ws.set_status(project, step, "drafted", "tutor")
                out["step"] = {step: "drafted"}
        return out

    def heard_back(self, project: str, text: str, from_whom: str = "") -> dict:
        """How it landed: a reaction, a question, a comment, in the learner's words (or pasted,
        with names removed). Questions people asked often suggest the next project."""
        from .core import HarnessError, _now
        if not (text or "").strip():
            raise HarnessError("What did they say?")
        d = self._dir(project)
        f = d / "heard_back.yaml"
        data = _read(f, {}) or {"schema": 1, "items": []}
        item = {"at": _now().isoformat(timespec="minutes"), "text": text.strip()}
        if from_whom.strip():
            item["from"] = from_whom.strip()
        data["items"].append(item)
        _write(f, data)
        self.ws.reports.record_shared("heard-back", text, who=from_whom, project=project)
        return {"saved": str(f.relative_to(self.ws.root)), "items": len(data["items"])}

    # ----------------------------------------------------------------- portfolio
    def build_portfolio(self, project: str, target: str, files: dict | None = None,
                        include: list[str] | None = None, title: str = "") -> dict:
        """Write an optional portfolio piece for any lesson: files ({relative path: text}) composed
        from the learner's own words, plus include (project-relative paths of their work to copy in).
        Never publishes; returns how the learner can publish it themselves, and privacy flags."""
        from .core import HarnessError, _now
        d = self.ws._require_project(project)
        if target not in PORTFOLIO_TARGETS:
            raise HarnessError(f"target must be one of {tuple(PORTFOLIO_TARGETS)}.")
        dest = d / "portfolio" / target
        written: list[str] = []
        flags: list[str] = []

        def safe(rel: str) -> Path:
            rel = str(rel).strip().lstrip("/")
            pr = Path(rel)
            if not rel or ".." in pr.parts or pr.is_absolute():
                raise HarnessError(f"{rel!r} must be a plain path inside the portfolio folder.")
            if pr.suffix.lower() not in PORTFOLIO_EXTS and pr.name != ".gitignore":
                raise HarnessError(f"{rel!r}: file type not supported for a portfolio piece.")
            return dest / pr

        planned: dict[Path, Any] = {}
        for rel, text in (files or {}).items():
            body = str(text)
            if len(body.encode("utf-8")) > PORTFOLIO_MAX_BYTES:
                raise HarnessError(f"{rel!r} is too large for a portfolio file.")
            planned[safe(rel)] = body
            flags += [f"{rel}: {f}" for f in _privacy_flags(body)]
        for rel in include or []:
            src = (d / str(rel)).resolve()
            if d.resolve() not in src.parents or not src.is_file():
                raise HarnessError(f"{rel!r} isn't a file in this project.")
            if "solutions" in src.relative_to(d.resolve()).parts:
                raise HarnessError("Worked solutions aren't the learner's work; include their own files.")
            if src.stat().st_size > PORTFOLIO_MAX_BYTES:
                raise HarnessError(f"{rel!r} is too large for a portfolio file.")
            planned[safe(Path(rel).name if Path(rel).parts[0] in ("work", "data") else rel)] = src
            if src.suffix.lower() in {".md", ".txt", ".py", ".ipynb", ".csv", ".json", ".html"}:
                flags += [f"{rel}: {f}" for f in _privacy_flags(src.read_text(encoding="utf-8", errors="ignore"))]
        need = PORTFOLIO_TARGETS[target]["needs"]
        names = {p.relative_to(dest).as_posix() for p in planned} | (
            {p.relative_to(dest).as_posix() for p in dest.rglob("*") if p.is_file()} if dest.exists() else set())
        if need and not (set([need] if isinstance(need, str) else need) & names):
            raise HarnessError(f"A {target} piece needs {need if isinstance(need, str) else ' or '.join(need)}.")
        for path, body in planned.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(body, Path):
                shutil.copyfile(body, path)
            else:
                path.write_text(body if body.endswith("\n") else body + "\n", encoding="utf-8")
            written.append(str(path.relative_to(self.ws.root)))
        if target == "github" and not (dest / ".gitignore").exists():
            (dest / ".gitignore").write_text(GITHUB_GITIGNORE, encoding="utf-8")
            written.append(str((dest / ".gitignore").relative_to(self.ws.root)))
        mf = d / "portfolio" / "portfolio.yaml"
        man = _read(mf, {}) or {"schema": 1, "pieces": {}}
        piece = man["pieces"].setdefault(target, {"created": _now().isoformat(timespec="minutes"), "builds": 0})
        piece.update({"title": title.strip() or piece.get("title", ""), "updated": _now().isoformat(timespec="minutes"),
                      "builds": piece.get("builds", 0) + 1,
                      "files": sorted(p.relative_to(dest).as_posix() for p in dest.rglob("*") if p.is_file())})
        _write(mf, man)
        step = self._share_step(project)
        if step:
            self.ws.record_attempt(project, step, f"[portfolio {target}] {', '.join(piece['files'])}")
        return {"folder": str(dest.relative_to(self.ws.root)), "absolute_folder": str(dest),
                "written": written, "privacy_flags": flags, "publish": _publish_hint(target, dest),
                "next": "Show the learner the piece and every privacy flag. They publish it themselves; "
                        "afterwards note(kind='shared', how='posted', link=...)."}

    def portfolio(self, project: str) -> dict:
        d = self.ws._require_project(project)
        return _read(d / "portfolio" / "portfolio.yaml", {}) or {"pieces": {}}

    # ------------------------------------------------------------ retrospective
    def save_retrospective(self, answers: dict, project: str = "", period: str = "") -> dict:
        """The learner's look back, in their words. answers: any of went_well, was_hard,
        surprised, differently, how_i_learn, sharing, next. Every question can be skipped."""
        from .core import HarnessError, _now, _slug
        clean = {k: str(v).strip() for k, v in (answers or {}).items() if k in RETRO_QUESTIONS and str(v).strip()}
        if not clean:
            raise HarnessError("A retrospective needs at least one answer in the learner's words.")
        if project:
            self.ws._require_project(project)
        t = _now()
        f = self.ws.private / "reflection" / "retros" / f"{t.date().isoformat()}-{_slug(project or period or 'period')}.yaml"
        n = 2
        while f.exists():
            f = f.with_name(f"{f.stem}-{n}.yaml")
            n += 1
        data = {"schema": 1, "at": t.isoformat(timespec="minutes"), "project": project, "period": period,
                "answers": clean}
        _write(f, data)
        self._index_retro(data, f)
        return {"saved": str(f.relative_to(self.ws.root)), "answered": list(clean)}

    def _index_retro(self, data: dict, f: Path) -> None:
        self.ws.index.upsert(f"retro:{f.stem}", "retro", " ".join(data["answers"].values()),
                             {"scope": "reflection", "author": "learner", "project": data.get("project", ""),
                              "date": data["at"][:10]}, str(f.relative_to(self.ws.root)))

    def retrospectives(self, since: str = "", until: str = "", project: str = "") -> list[dict]:
        d = self.ws.private / "reflection" / "retros"
        out = []
        for f in sorted(d.glob("*.yaml"), reverse=True) if d.exists() else []:
            r = _read(f, {}) or {}
            day = str(r.get("at", ""))[:10]
            if (since and day < since) or (until and day > until) or (project and r.get("project") != project):
                continue
            out.append(r)
        return out

    def retro_due(self) -> list[str]:
        """Projects whose steps are all done but that have no retrospective yet."""
        from .tour import TOUR_PROJECT
        done = []
        for p in self.ws.orient._projects():
            if p["project"] == TOUR_PROJECT:  # the tour ends in a real plan, not a retrospective
                continue
            if p["steps"] and not p["now"] and not self.retrospectives(project=p["project"]):
                done.append(p["project"])
        return done


_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
_HOME = re.compile(r"(/Users/|/home/|C:\\Users\\)[^\s/\\]+")


def _privacy_flags(text: str) -> list[str]:
    """Things worth a second look before anything leaves the computer. Flags, never refusals."""
    out = []
    if _EMAIL.search(text):
        out.append("contains an email address")
    if _HOME.search(text):
        out.append("contains a path with a computer user name")
    if ".private/" in text:
        out.append("refers to private harness records (.private/)")
    if re.search(r"(?i)(api[_-]?key|secret|password|token)\s*[:=]", text):
        out.append("may contain a key, password or token")
    return out


def _publish_hint(target: str, dest: Path) -> list[str]:
    if target == "github":
        return [f"cd \"{dest}\"", "git init && git add . && git commit -m \"First version\"",
                "gh repo create <name> --public --source . --push   (or create the repo on github.com and push)",
                "Optional: turn on GitHub Pages in the repo settings to show an index.html as a site."]
    if target == "web":
        return ["Open index.html in a browser to check it.",
                "Upload it to any host you use (your own site, GitHub Pages, Netlify Drop), "
                "or ask to publish it as a private Claude page you can share."]
    if target == "post":
        return ["Paste it into the blog, Substack, LinkedIn or forum you choose; add images by hand there."]
    return ["Open the folder and send or upload the files wherever you planned."]
