"""
main.py — SRH AI Content Creator
Demo entry point for the presentation.

Usage:
  python main.py --type blog    --topic "AI Ethics at SRH"
  python main.py --type social  --topic "Open Day June 2026" --extra "Join us on 14 June"
  python main.py --type program --topic "MSc Applied Data Science and AI"
  python main.py --type demo
"""

import argparse
import os
from datetime import datetime

from src.content_pipeline import Pipeline

OUTPUTS_DIR = "outputs"
DIVIDER = "\n" + "═" * 60 + "\n"

CONTENT_LABELS = {
    "blog":    "Blog Post",
    "social":  "Social Media Post",
    "program": "Program Description",
    "demo":    "Full Pipeline Demo",
}


def banner(title: str) -> str:
    return f"{DIVIDER}{title.upper()}{DIVIDER}"


def save(content: str, content_type: str, topic: str) -> str:
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = topic.lower().replace(" ", "_")[:40]
    filename = f"{OUTPUTS_DIR}/{content_type}_{slug}_{timestamp}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"<!-- type: {content_type} | topic: {topic} | generated: {timestamp} -->\n\n")
        f.write(content)
    return filename


def run_blog(pipeline: Pipeline, topic: str, extra: str) -> None:
    print(banner("Stage 2 — Monitor"))
    print(pipeline.monitor(topic=topic, content_type="blog", audience="prospective international students", extra=extra))

    print(banner("Stage 3 — Brief"))
    print(pipeline.brief())

    print(banner("Stage 4 — Publish · Generating blog post..."))
    content = pipeline.publish()
    print(content)

    path = save(content, "blog", topic)
    print(f"\n✓ Saved → {path}")


def run_social(pipeline: Pipeline, topic: str, extra: str) -> None:
    announcement = extra or topic
    print(banner("Stage 2 — Monitor"))
    print(pipeline.monitor(topic=topic, content_type="social", audience="prospective students", extra=announcement))

    print(banner("Stage 3 — Brief"))
    print(pipeline.brief())

    print(banner("Stage 4 — Publish · Generating social media posts..."))
    content = pipeline.publish()
    print(content)

    path = save(content, "social", topic)
    print(f"\n✓ Saved → {path}")


def run_program(pipeline: Pipeline, topic: str, extra: str) -> None:
    program_name = extra or topic
    print(banner("Stage 2 — Monitor"))
    print(pipeline.monitor(topic=topic, content_type="program", audience="prospective students", extra=program_name))

    print(banner("Stage 3 — Brief"))
    print(pipeline.brief())

    print(banner("Stage 4 — Publish · Generating program description..."))
    content = pipeline.publish()
    print(content)

    path = save(content, "program", topic)
    print(f"\n✓ Saved → {path}")


def run_demo(pipeline: Pipeline) -> None:
    """Walk through all five pipeline stages with a preset topic."""
    topic = "How SRH Prepares Students for Careers in AI"

    print(banner("Stage 2 — Monitor"))
    print(pipeline.monitor(topic=topic, content_type="blog", audience="prospective international master's students"))

    print(banner("Stage 3 — Brief"))
    print(pipeline.brief())

    print(banner("Stage 4 — Publish · Generating content..."))
    content = pipeline.publish()
    print(content)

    path = save(content, "demo", topic)
    print(f"\n✓ Saved → {path}")

    print(banner("Stage 5 — Iterate"))
    feedback = "Open with a specific student outcome stat. Avoid generic AI trend opener."
    print(pipeline.iterate(feedback=feedback))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SRH AI Content Creator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python main.py --type blog    --topic "AI Ethics at SRH"
  python main.py --type social  --topic "Open Day June 2026" --extra "Join us 14 June in Berlin"
  python main.py --type program --topic "MSc Applied Data Science and AI"
  python main.py --type demo
        """,
    )
    parser.add_argument(
        "--type",
        choices=["blog", "social", "program", "demo"],
        required=True,
        help="Content type to generate",
    )
    parser.add_argument("--topic", default="", help="Topic or subject for the content")
    parser.add_argument(
        "--extra",
        default="",
        help="Secondary input: announcement text (social) or program name (program)",
    )
    parser.add_argument(
        "--kb",
        default="knowledge_base/primary/",
        help="Path to knowledge base directory (default: knowledge_base/primary/)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print(banner(f"SRH AI Content Creator — {CONTENT_LABELS[args.type]}"))

    # Stage 1: Document (always runs)
    print(banner("Stage 1 — Document"))
    pipeline = Pipeline(kb_dir=args.kb)
    print(pipeline.document())

    if args.type == "demo":
        run_demo(pipeline)
    elif args.type == "blog":
        if not args.topic:
            print("Error: --topic is required for blog posts.")
            raise SystemExit(1)
        run_blog(pipeline, args.topic, args.extra)
    elif args.type == "social":
        if not args.topic:
            print("Error: --topic is required for social media posts.")
            raise SystemExit(1)
        run_social(pipeline, args.topic, args.extra)
    elif args.type == "program":
        if not args.topic:
            print("Error: --topic is required for program descriptions.")
            raise SystemExit(1)
        run_program(pipeline, args.topic, args.extra)

    print(banner("Done"))


if __name__ == "__main__":
    main()
