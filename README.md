# skill

A simple command-line assistant for tracking personal skills. Use it to
add new skills, log practice sessions, set goals, and review progress.

## Usage

```bash
python skill.py add "Guitar" "Practice fingerstyle guitar" --category Music
python skill.py practice "Guitar" 45 --intensity high --notes "Worked on arpeggios"
python skill.py goal "Guitar" --target-level 5 --deadline 2024-12-31 --notes "Perform at recital"
python skill.py progress "Guitar"
```

By default data is stored in `skills.json` next to the script. Provide a
custom location with `--db path/to/file.json` when running commands.
