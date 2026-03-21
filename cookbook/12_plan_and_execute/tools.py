"""Python tools for recipe 12: Plan and Execute.

Loaded with:
    spl2 run ... --tools cookbook/12_plan_and_execute/tools.py

CALL write_code_files(@final_report, @output_dir) INTO @files_written
"""

import os
import re

from spl2.tools import spl_tool


@spl_tool
def write_code_files(content: str, output_dir: str) -> str:
    """Parse fenced code blocks with '# filename:' comments and write each to output_dir.

    Expects blocks in this format anywhere in the content:

        ```python
        # filename: app/main.py
        ...code...
        ```

    Returns a summary of files written.
    """
    if not output_dir.strip():
        return "No output_dir specified — files not written"

    os.makedirs(output_dir, exist_ok=True)

    # Match ```<lang>\n# filename: <path>\n<code>```
    pattern = re.compile(
        r"```(?:\w+)?\n#\s*filename:\s*(\S+)\n(.*?)```",
        re.DOTALL,
    )

    files_written = []
    for match in pattern.finditer(content):
        rel_path = match.group(1).strip()
        code = match.group(2)
        filepath = os.path.join(output_dir, rel_path)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code)
        files_written.append(rel_path)

    if not files_written:
        return (
            "No code files found — ensure code blocks have a '# filename: path' "
            "comment as the first line inside the fence."
        )

    lines = [f"Written {len(files_written)} file(s) to {output_dir}:"]
    lines += [f"  {f}" for f in files_written]
    return "\n".join(lines)
