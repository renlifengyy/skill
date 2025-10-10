#!/usr/bin/env python3
"""Command-line personal skill tracking assistant.

This module provides a small but featureful CLI utility for managing
personal skill development.  Users can maintain a catalog of skills,
record practice sessions, set goals, and inspect progress – all backed
by a JSON file that lives next to the script (or a custom location
provided through ``--db``).
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Iterable, List, Optional

DEFAULT_DB = Path(__file__).with_name("skills.json")


@dataclass
class PracticeEntry:
    """A record of a practice session."""

    timestamp: str
    minutes: int
    intensity: str
    notes: Optional[str] = None


@dataclass
class Goal:
    """A goal that the user wants to reach for a given skill."""

    target_level: int
    deadline: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class Skill:
    """Model a skill with progress information."""

    name: str
    description: str
    category: Optional[str] = None
    level: int = 1
    experience: float = 0.0
    practice_log: List[PracticeEntry] = field(default_factory=list)
    goal: Optional[Goal] = None

    def add_practice(self, minutes: int, intensity: str, notes: Optional[str]) -> float:
        xp_gained = calculate_experience(minutes, intensity)
        entry = PracticeEntry(
            timestamp=datetime.utcnow().isoformat(timespec="seconds"),
            minutes=minutes,
            intensity=intensity,
            notes=notes or None,
        )
        self.practice_log.append(entry)
        self.apply_experience(xp_gained)
        return xp_gained

    def apply_experience(self, xp: float) -> None:
        self.experience += xp
        while self.experience >= experience_to_next_level(self.level):
            self.experience -= experience_to_next_level(self.level)
            self.level += 1

    def ensure_goal(self) -> Goal:
        if self.goal is None:
            self.goal = Goal(target_level=self.level)
        return self.goal


def calculate_experience(minutes: int, intensity: str) -> float:
    if minutes <= 0:
        raise ValueError("Practice minutes must be positive")
    intensity = intensity.lower()
    intensity_multiplier = {
        "low": 0.75,
        "medium": 1.0,
        "high": 1.5,
    }
    if intensity not in intensity_multiplier:
        raise ValueError("Intensity must be one of: low, medium, high")
    base_rate = 12.0  # base experience per 30 minutes
    segments = minutes / 30.0
    return base_rate * segments * intensity_multiplier[intensity]


def experience_to_next_level(level: int) -> float:
    return 60 + (level - 1) * 40


def load_skills(path: Path) -> Dict[str, Skill]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    skills: Dict[str, Skill] = {}
    for item in data:
        practice_log = [PracticeEntry(**entry) for entry in item.get("practice_log", [])]
        goal_data = item.get("goal")
        goal = Goal(**goal_data) if goal_data else None
        skill = Skill(
            name=item["name"],
            description=item.get("description", ""),
            category=item.get("category"),
            level=item.get("level", 1),
            experience=item.get("experience", 0.0),
            practice_log=practice_log,
            goal=goal,
        )
        skills[skill.name.lower()] = skill
    return skills


def save_skills(path: Path, skills: Iterable[Skill]) -> None:
    payload = []
    for skill in skills:
        data = asdict(skill)
        payload.append(data)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def require_skill(skills: Dict[str, Skill], name: str) -> Skill:
    key = name.lower()
    if key not in skills:
        raise SystemExit(f"Skill '{name}' does not exist. Use the 'add' command first.")
    return skills[key]


def add_skill_command(args: argparse.Namespace, skills: Dict[str, Skill], path: Path) -> None:
    key = args.name.lower()
    if key in skills:
        raise SystemExit(f"Skill '{args.name}' already exists.")
    skill = Skill(name=args.name, description=args.description, category=args.category)
    skills[key] = skill
    save_skills(path, skills.values())
    print(f"Added skill '{skill.name}' in category '{skill.category or 'uncategorized'}'.")


def list_skills_command(_: argparse.Namespace, skills: Dict[str, Skill], __: Path) -> None:
    if not skills:
        print("No skills tracked yet. Add one with the 'add' command.")
        return
    for skill in sorted(skills.values(), key=lambda s: s.name.lower()):
        goal_text = ""
        if skill.goal:
            goal_text = f" (goal: level {skill.goal.target_level}{format_deadline(skill.goal.deadline)})"
        print(f"- {skill.name} — level {skill.level}, {skill.experience:.1f} XP towards next level{goal_text}")


def show_skill_command(args: argparse.Namespace, skills: Dict[str, Skill], __: Path) -> None:
    skill = require_skill(skills, args.name)
    print(f"Name       : {skill.name}")
    print(f"Category   : {skill.category or '—'}")
    print(f"Description: {skill.description or '—'}")
    print(f"Level      : {skill.level}")
    print(f"Experience : {skill.experience:.1f} / {experience_to_next_level(skill.level):.1f}")
    if skill.goal:
        print("Goal       : level {target} {deadline}".format(
            target=skill.goal.target_level,
            deadline=format_deadline(skill.goal.deadline, prefix="by ")
            if skill.goal.deadline
            else ""
        ))
        if skill.goal.notes:
            print(f"Goal notes : {skill.goal.notes}")
    if skill.practice_log:
        print("Practice log:")
        for entry in reversed(skill.practice_log[-10:]):
            notes = f" — {entry.notes}" if entry.notes else ""
            print(f"  {entry.timestamp} · {entry.minutes} min · {entry.intensity}{notes}")
    else:
        print("Practice log: (no sessions recorded yet)")


def practice_command(args: argparse.Namespace, skills: Dict[str, Skill], path: Path) -> None:
    skill = require_skill(skills, args.name)
    try:
        xp_gained = skill.add_practice(args.minutes, args.intensity, args.notes)
    except ValueError as exc:
        raise SystemExit(str(exc))
    save_skills(path, skills.values())
    print(f"Recorded {args.minutes} minutes of {args.intensity} practice for '{skill.name}'.")
    print(f"Experience gained: {xp_gained:.1f} XP.")
    print(f"Level now: {skill.level} ({skill.experience:.1f}/{experience_to_next_level(skill.level):.1f} XP).")


def level_up_command(args: argparse.Namespace, skills: Dict[str, Skill], path: Path) -> None:
    skill = require_skill(skills, args.name)
    if args.levels <= 0:
        raise SystemExit("Levels must be positive.")
    skill.level += args.levels
    skill.experience = 0.0
    save_skills(path, skills.values())
    print(f"Skill '{skill.name}' advanced to level {skill.level}.")


def goal_command(args: argparse.Namespace, skills: Dict[str, Skill], path: Path) -> None:
    skill = require_skill(skills, args.name)
    if args.clear:
        skill.goal = None
        save_skills(path, skills.values())
        print(f"Cleared goal for '{skill.name}'.")
        return
    if args.deadline:
        try:
            _ = date.fromisoformat(args.deadline)
        except ValueError as exc:
            raise SystemExit(f"Invalid deadline date: {exc}")
    goal = skill.ensure_goal()
    goal.target_level = args.target_level or goal.target_level
    goal.deadline = args.deadline or goal.deadline
    goal.notes = args.notes or goal.notes
    save_skills(path, skills.values())
    print(f"Updated goal for '{skill.name}' to reach level {goal.target_level}{format_deadline(goal.deadline)}.")


def progress_command(args: argparse.Namespace, skills: Dict[str, Skill], __: Path) -> None:
    skill = require_skill(skills, args.name)
    needed = experience_to_next_level(skill.level)
    remaining = max(0.0, needed - skill.experience)
    print(f"{skill.name}: level {skill.level}")
    print(f"Progress  : {skill.experience:.1f}/{needed:.1f} XP ({(skill.experience / needed) * 100:.1f}%).")
    if remaining:
        print(f"Remaining : {remaining:.1f} XP to next level.")
    else:
        print("Ready to level up! Consider running 'level-up'.")
    if skill.goal:
        print(f"Goal      : level {skill.goal.target_level}{format_deadline(skill.goal.deadline)}")
        if skill.goal.deadline:
            days_left = (date.fromisoformat(skill.goal.deadline) - date.today()).days
            print(f"Deadline  : {skill.goal.deadline} ({days_left} days left)")
        if skill.goal.notes:
            print(f"Goal notes: {skill.goal.notes}")


def remove_command(args: argparse.Namespace, skills: Dict[str, Skill], path: Path) -> None:
    key = args.name.lower()
    if key not in skills:
        raise SystemExit(f"Skill '{args.name}' is not tracked.")
    del skills[key]
    save_skills(path, skills.values())
    print(f"Removed skill '{args.name}'.")


def format_deadline(deadline: Optional[str], prefix: str = " by ") -> str:
    return f"{prefix}{deadline}" if deadline else ""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Track and plan your personal skills.")
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help=f"Path to the skills database (default: {DEFAULT_DB}).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a new skill to track.")
    add_parser.add_argument("name", help="Name of the skill.")
    add_parser.add_argument("description", help="Short description of the skill.")
    add_parser.add_argument("--category", help="Category label for grouping skills.")
    add_parser.set_defaults(func=add_skill_command)

    subparsers.add_parser("list", help="List all tracked skills.").set_defaults(func=list_skills_command)

    show_parser = subparsers.add_parser("show", help="Show detailed information about a skill.")
    show_parser.add_argument("name", help="Name of the skill.")
    show_parser.set_defaults(func=show_skill_command)

    practice_parser = subparsers.add_parser("practice", help="Log a practice session and gain experience.")
    practice_parser.add_argument("name", help="Name of the skill.")
    practice_parser.add_argument("minutes", type=int, help="Duration of the practice session in minutes.")
    practice_parser.add_argument(
        "--intensity",
        choices=["low", "medium", "high"],
        default="medium",
        help="Practice intensity; controls experience gain.",
    )
    practice_parser.add_argument("--notes", help="Optional notes about the session.")
    practice_parser.set_defaults(func=practice_command)

    level_parser = subparsers.add_parser("level-up", help="Manually level up a skill.")
    level_parser.add_argument("name", help="Name of the skill.")
    level_parser.add_argument("--levels", type=int, default=1, help="Number of levels to add.")
    level_parser.set_defaults(func=level_up_command)

    goal_parser = subparsers.add_parser("goal", help="Set or update a goal for a skill.")
    goal_parser.add_argument("name", help="Name of the skill.")
    goal_parser.add_argument("--target-level", type=int, help="Desired level to reach.")
    goal_parser.add_argument("--deadline", help="Deadline for the goal (YYYY-MM-DD).")
    goal_parser.add_argument("--notes", help="Additional notes about the goal.")
    goal_parser.add_argument("--clear", action="store_true", help="Clear the current goal.")
    goal_parser.set_defaults(func=goal_command)

    progress_parser = subparsers.add_parser("progress", help="Show progress toward the next level and goals.")
    progress_parser.add_argument("name", help="Name of the skill.")
    progress_parser.set_defaults(func=progress_command)

    remove_parser = subparsers.add_parser("remove", help="Stop tracking a skill.")
    remove_parser.add_argument("name", help="Name of the skill to remove.")
    remove_parser.set_defaults(func=remove_command)

    return parser


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    skills = load_skills(args.db)
    func = getattr(args, "func")
    func(args, skills, args.db)


if __name__ == "__main__":
    main()
