"""
hermes-cyclus plugin — loop engineering primitives for Hermes Agent.

Registers:
  Tools: cyclus_queue, cyclus_evidence
  Hooks: none (v18)
  Skills: cyclus-ralplan, cyclus-ralph, cyclus-deep-interview, cyclus-autopilot (bundled)
"""

import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

_TOOLSET = "cyclus"


def _install_skills(
    skills_src_root: Path | None = None,
    skills_dest_root: Path | None = None,
) -> None:
    """Install bundled skills to ~/.hermes/skills/cyclus/ if not already present.

    Skips skills that are already installed — the user's copy takes precedence.
    Uses an atomic copy-then-rename pattern to avoid partial installs.
    """
    if skills_dest_root is None:
        try:
            from hermes_cli.config import get_hermes_home
            skills_dest_root = get_hermes_home() / "skills" / "cyclus"
        except Exception:
            skills_dest_root = Path.home() / ".hermes" / "skills" / "cyclus"

    if skills_src_root is None:
        skills_src_root = Path(__file__).parent / "skills"

    if not skills_src_root.exists():
        return

    skills_dest_root.mkdir(parents=True, exist_ok=True)

    for skill_dir in skills_src_root.iterdir():
        if not skill_dir.is_dir():
            continue
        dest = skills_dest_root / skill_dir.name
        if dest.exists():
            continue  # already installed; never overwrite user's copy
        tmp_dest = dest.parent / (dest.name + "._installing")
        try:
            if tmp_dest.exists():
                shutil.rmtree(tmp_dest)
            shutil.copytree(skill_dir, tmp_dest)
            tmp_dest.rename(dest)  # atomic on same filesystem
        except Exception as e:
            logger.warning("Failed to install skill '%s': %s", skill_dir.name, e)
            shutil.rmtree(tmp_dest, ignore_errors=True)


def register(ctx):
    """Entry point called by Hermes plugin discovery."""
    _install_skills()

    from .tools.queue_tool import CYCLUS_QUEUE_SCHEMA, cyclus_queue_handler
    from .tools.evidence_tool import CYCLUS_EVIDENCE_SCHEMA, cyclus_evidence_handler

    ctx.register_tool("cyclus_queue", _TOOLSET, CYCLUS_QUEUE_SCHEMA, cyclus_queue_handler,
                       description=CYCLUS_QUEUE_SCHEMA["description"])
    ctx.register_tool("cyclus_evidence", _TOOLSET, CYCLUS_EVIDENCE_SCHEMA, cyclus_evidence_handler,
                       description=CYCLUS_EVIDENCE_SCHEMA["description"])
