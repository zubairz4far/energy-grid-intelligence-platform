from __future__ import annotations

import argparse
import json

from .evaluation import write_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Energy grid intelligence benchmark")
    subparsers = parser.add_subparsers(dest="command", required=True)
    benchmark = subparsers.add_parser("benchmark", help="run the OPSD DE-LU v0.1 benchmark")
    benchmark.add_argument("--data-dir", default=".cache/opsd")
    benchmark.add_argument("--output", default="evals/results/v0.1_opsd_de_lu.json")
    benchmark.add_argument("--download", action="store_true")
    benchmark.add_argument("--seed", type=int, default=42)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "benchmark":
        report = write_report(
            args.output,
            args.data_dir,
            download=args.download,
            seed=args.seed,
        )
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
