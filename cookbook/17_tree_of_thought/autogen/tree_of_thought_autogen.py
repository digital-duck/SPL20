"""
AutoGen equivalent of tree_of_thought.spl

Coordinated agents (Thinker, Scorer, Selector, Verifier) explore multiple
reasoning paths and select/synthesize a final solution.

Usage:
    pip install pyautogen
    python cookbook/17_tree_of_thought/autogen/tree_of_thought_autogen.py \
        --problem "Design a sustainable urban transport system."
"""

import argparse
from pathlib import Path

from autogen import ConversableAgent


# ── Agent system messages ─────────────────────────────────────────────────────

THINKER_SYSTEM = """\
You are a creative problem solver. Your job is to provide unique initial
approaches and develop them into detailed reasoning paths."""

SCORER_SYSTEM = """\
You are a technical reviewer. Score reasoning paths from 1-10 based on
feasibility and depth. Reply ONLY with the numeric score."""

SELECTOR_SYSTEM = """\
You are a senior analyst. Given multiple reasoning paths and their scores,
identify the best one and output its content as the winner."""

REFINER_SYSTEM = """\
You are a technical writer. Refine a reasoning path into a complete,
polished, and comprehensive solution."""

VERIFIER_SYSTEM = """\
You are a critical reviewer. Verify if a solution is sound and complete.
Output 'sound' if it is correct, otherwise provide a brief critique."""

SYNTHESIZER_SYSTEM = """\
You are a master of synthesis. Combine insights from multiple reasoning
paths into one final, comprehensive solution."""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ── Main runner ───────────────────────────────────────────────────────────────

def run(problem: str, models: list, log_dir: str) -> str:
    def get_config(model):
        return {
            "config_list": [{
                "model":    model,
                "base_url": "http://localhost:11434/v1",
                "api_key":  "ollama",
            }]
        }

    # Agents
    thinker = ConversableAgent("Thinker", system_message=THINKER_SYSTEM, human_input_mode="NEVER")
    scorer  = ConversableAgent("Scorer",  system_message=SCORER_SYSTEM,  human_input_mode="NEVER")
    selector = ConversableAgent("Selector", system_message=SELECTOR_SYSTEM, human_input_mode="NEVER")
    refiner = ConversableAgent("Refiner", system_message=REFINER_SYSTEM, human_input_mode="NEVER")
    verifier = ConversableAgent("Verifier", system_message=VERIFIER_SYSTEM, human_input_mode="NEVER")
    synthesizer = ConversableAgent("Synthesizer", system_message=SYNTHESIZER_SYSTEM, human_input_mode="NEVER")

    results_map = {}
    
    # Phase 1 & 2: Explore paths
    for i, model in enumerate(models):
        print(f"Exploring path {i+1}/{len(models)} using {model}...")
        cfg = get_config(model)
        thinker.llm_config = cfg
        scorer.llm_config = cfg
        
        init_reply = thinker.generate_reply(messages=[{"content": f"Problem: {problem}\nProvide an initial unique approach.", "role": "user"}])
        init_path = str(init_reply)
        
        dev_reply = thinker.generate_reply(messages=[{"content": f"Problem: {problem}\nInitial approach: {init_path}\nDevelop this path one level deeper.", "role": "user"}])
        developed_path = str(dev_reply)
        
        score_reply = scorer.generate_reply(messages=[{"content": f"Problem: {problem}\nPath: {developed_path}\nScore this path 1-10.", "role": "user"}])
        score = str(score_reply).strip()
        
        results_map[model] = {"content": developed_path, "score": score}
        _write(f"{log_dir}/path_{model}.md", developed_path)

    # Base model config for selection and final steps
    base_cfg = get_config(models[0])
    selector.llm_config = base_cfg
    refiner.llm_config = base_cfg
    verifier.llm_config = base_cfg
    synthesizer.llm_config = base_cfg

    # Phase 4: Select best
    print("Selecting best path...")
    select_reply = selector.generate_reply(messages=[{"content": f"Problem: {problem}\nResults Map: {results_map}\nIdentify and output the best path's content.", "role": "user"}])
    best_path = str(select_reply)
    
    # Phase 5: Refine
    print("Refining winning path...")
    refine_reply = refiner.generate_reply(messages=[{"content": f"Problem: {problem}\nWinning path: {best_path}\nRefine into a final solution.", "role": "user"}])
    solution = str(refine_reply)
    
    # Phase 6: Verify
    print("Verifying solution...")
    verify_reply = verifier.generate_reply(messages=[{"content": f"Problem: {problem}\nSolution: {solution}\nIs this solution sound?", "role": "user"}])
    verification = str(verify_reply)
    _write(f"{log_dir}/verification.md", verification)

    if "sound" not in verification.lower():
        print("Verification failed — synthesizing all paths...")
        synth_reply = synthesizer.generate_reply(messages=[{"content": f"Problem: {problem}\nAll Paths: {results_map}\nSynthesize a final solution.", "role": "user"}])
        solution = str(synth_reply)

    _write(f"{log_dir}/final_solution.md", solution)
    return solution


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Tree of Thought — AutoGen edition")
    p.add_argument("--problem",   default="Design a sustainable urban transport system.")
    p.add_argument("--models",    nargs="+", default=["gemma3", "phi4", "qwen2.5"])
    p.add_argument("--log-dir",   default="cookbook/17_tree_of_thought/autogen/logs-autogen")
    args = p.parse_args()

    result = run(args.problem, args.models, args.log_dir)
    print("\n" + "=" * 60)
    print("FINAL SOLUTION:")
    print(result)

if __name__ == "__main__":
    main()
