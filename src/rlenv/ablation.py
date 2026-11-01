"""Side-by-side report of a rules-shown run and its ablation (decisions 0011 and 0013)."""


def render_pair(
    shown: dict, hidden: dict, env: str, hidden_name: str, flag: str, short: str, clause: str
) -> str:
    """Two runs of one environment side by side: the rules shown (the control), and an
    ablation with them left out. The verdict is per question: near the ceiling either way, a
    convention gap (most misses follow one careless reading), or room to learn."""
    lines = [
        f"# {env}: rules shown against {hidden_name}",
        "",
        f"Model `{shown['model']}` on the same {shown['n']} items, once with each question's "
        f"rule in the prompt and once with {flag}.",
        "",
        f"| question | n | accuracy, rules shown | accuracy, {hidden_name} |",
        "|---|---|---|---|",
    ]
    hidden_by = {r["question"]: r for r in hidden["questions"]}
    pairs = [
        (r, hidden_by[r["question"]]) for r in shown["questions"] if r["question"] in hidden_by
    ]
    lines += [
        f"| {r['question']} | {r['n']} | {r['accuracy']:.3f} | {h['accuracy']:.3f} |"
        for r, h in pairs
    ]
    lines += [
        f"| all | {shown['n']} | {shown['reward']:.3f} | {hidden['reward']:.3f} |",
        "",
        f"Wrong answers in the {hidden_name} run that equal a careless reading of the rule:",
        "",
        "| question | careless reading | misses that match |",
        "|---|---|---|",
    ]
    for r in hidden["questions"]:
        lines += [f"| {r['question']} | {name} | {c} |" for name, c in r["traps"].items()]
    k_shown = round(shown["reward"] * shown["n"])
    lines += [
        "",
        "## What this means for RL",
        "",
        f"With the rules shown the model is right on {k_shown} of {shown['n']} items. That run "
        "is the control: nearly every rollout earns the same reward, so an RL policy this "
        f"strong gets almost no signal to learn from. Per question, against {hidden_name}:",
        "",
    ]
    for r, h in pairs:
        misses = h["n"] - round(h["accuracy"] * h["n"])
        head = f"- {r['question']}: {r['accuracy']:.3f} with the rules shown, "
        head += f"{h['accuracy']:.3f} {short}"
        if r["accuracy"] - h["accuracy"] < 0.05:  # within five points: no real drop
            lines.append(
                f"{head}: near the ceiling either way, so the model fills in this rule itself."
            )
        elif h.get("explained", 0) > misses / 2:
            lines.append(
                f"{head}, and {h['explained']} of the {misses} misses follow a careless reading of "
                f"the rule: a convention gap, {clause}."
            )
        else:
            lines.append(f"{head}: room to learn.")
    if "recognized" in shown and "recognized" in hidden:
        lines += [
            "",
            f"Replies that name the storm or its season: {shown['recognized']} of {shown['n']} "
            f"with the rules shown, {hidden['recognized']} {short}.",
        ]
    return "\n".join([*lines, ""])
