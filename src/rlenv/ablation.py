"""Side-by-side report of a rules-shown run and its ablation (decisions 0011 and 0013)."""


def render_pair(shown: dict, hidden: dict, env: str, hidden_name: str, flag: str) -> str:
    """Two runs of one environment side by side: the rules shown, and an ablation with them
    left out (decisions 0011 and 0013)."""
    k_shown = round(shown["reward"] * shown["n"])
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
    for r in shown["questions"]:
        if (h := hidden_by.get(r["question"])) is not None:
            lines.append(
                f"| {r['question']} | {r['n']} | {r['accuracy']:.3f} | {h['accuracy']:.3f} |"
            )
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
    rl = (
        f"With the rules shown the model is right on {k_shown} of {shown['n']} items, so nearly "
        "every rollout earns the same reward and an RL policy this strong gets almost no signal "
        "to learn from; that version serves as a regression check, or for weaker models."
    )
    if hidden["reward"] < shown["reward"] - 0.1:
        rl += (
            f" With {hidden_name}, accuracy falls to {hidden['reward']:.3f}: the gap is what the "
            f"left-out rules carry, so the {hidden_name} version has room to learn."
        )
    else:
        rl += (
            f" With {hidden_name}, accuracy is {hidden['reward']:.3f}, so the model fills in the "
            "left-out rules itself and both versions are near the ceiling for it."
        )
    lines += ["", "## What this means for RL", "", rl]
    for r in hidden["questions"]:  # misses that follow one reading may be a fair convention
        misses = r["n"] - round(r["accuracy"] * r["n"])
        for name, c in r["traps"].items():
            if misses >= 5 and c >= misses / 4:
                lines += [
                    "",
                    f"On {r['question']}, {c} of the {misses} wrong answers equal '{name}'. With "
                    "the rule left out, that can follow a convention other than ours, so this "
                    "part of the gap measures which convention the model picks, not its skill.",
                ]
    lines.append("")
    return "\n".join(lines)
