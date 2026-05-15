import subprocess
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DiffLine:
    file: str
    line_number: int
    content: str


def parse_patch_content(patch_content: str) -> List[DiffLine]:
    added_lines = []
    current_file = None
    current_line_number = 0

    for line in patch_content.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]
        elif line.startswith("@@"):
            # Parse the @@ -xx,y +zz,w @@ header to get the starting line number
            parts = line.split(" ")
            if len(parts) >= 3:
                plus_part = parts[2]
                if plus_part.startswith("+"):
                    line_info = plus_part[1:].split(",")
                    current_line_number = (
                        int(line_info[0]) - 1
                    )  # Subtract 1 because we add 1 before processing
        elif line.startswith("+") and not line.startswith("+++"):
            current_line_number += 1
            if current_file:
                added_lines.append(
                    DiffLine(file=current_file, line_number=current_line_number, content=line[1:])
                )
        elif not line.startswith("-") and not line.startswith("\\"):
            # Context line
            current_line_number += 1

    return added_lines


def get_git_diff(staged: bool = False) -> str:
    cmd = ["git", "diff"]
    if staged:
        cmd.append("--cached")
    else:
        cmd.append("HEAD")

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout


def get_pr_diff(pr_number: int) -> str:
    cmd = ["gh", "pr", "diff", str(pr_number)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout


def get_added_lines(
    diff_path: Optional[str] = None, staged: bool = False, pr: Optional[int] = None
) -> List[DiffLine]:
    if diff_path:
        with open(diff_path, "r", encoding="utf-8") as f:
            diff_content = f.read()
    elif pr is not None:
        diff_content = get_pr_diff(pr)
    else:
        diff_content = get_git_diff(staged)

    return parse_patch_content(diff_content)
