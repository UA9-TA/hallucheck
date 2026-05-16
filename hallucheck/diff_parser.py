import subprocess


def parse_diff(diff_content):
    added_lines = []
    current_file = None
    line_number = 0

    for line in diff_content.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]
        elif line.startswith("@@"):
            # @@ -1,4 +1,5 @@
            parts = line.split(" ")
            if len(parts) >= 3 and parts[2].startswith("+"):
                line_info = parts[2][1:].split(",")
                line_number = int(line_info[0]) - 1
        elif line.startswith("+") and not line.startswith("+++"):
            line_number += 1
            if current_file and current_file.endswith(".py"):
                added_lines.append({"file": current_file, "line": line_number, "content": line[1:]})
        elif not line.startswith("-") and not line.startswith("\\"):
            line_number += 1

    return added_lines


def get_git_diff(staged=False, pr=None):
    if pr:
        cmd = ["gh", "pr", "diff", str(pr)]
    elif staged:
        cmd = ["git", "diff", "--cached"]
    else:
        cmd = ["git", "diff", "HEAD"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running git diff: {e}")
        return ""
