import argparse
import sys
import chess.pgn


def parse_elo(raw_value):
    """Return int Elo or None if value is missing/invalid."""
    if raw_value is None:
        return None
    value = str(raw_value).strip()
    if not value or value == "?":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def passes_threshold(white_elo, black_elo, min_elo, mode):
    if white_elo is None or black_elo is None:
        return False
    if mode == "both":
        return white_elo >= min_elo and black_elo >= min_elo
    return white_elo >= min_elo or black_elo >= min_elo


def build_parser():
    parser = argparse.ArgumentParser(
        description="Filter a PGN file and keep only games above Elo threshold."
    )
    parser.add_argument("--input-pgn", default="lichess_db.pgn", help="Input PGN path")
    parser.add_argument("--output-pgn", default="lichess_db.pgn", help="Output PGN path")
    parser.add_argument("--min-elo", type=int, default=2500, help="Minimum Elo threshold")
    parser.add_argument(
        "--mode",
        choices=["both", "any"],
        default="both",
        help="both = both players must be >= threshold, any = at least one player >= threshold",
    )
    parser.add_argument("--max-games", type=int, default=None, help="Optional cap on scanned games")
    parser.add_argument("--progress-every", type=int, default=1000, help="Progress print interval")
    parser.add_argument("--encoding", default="utf-8", help="File encoding")
    return parser


def main():
    args = build_parser().parse_args()

    scanned = 0
    kept = 0
    skipped_missing_elo = 0
    skipped_below_threshold = 0

    try:
        with open(args.input_pgn, "r", encoding=args.encoding, errors="replace") as in_file, \
                open(args.output_pgn, "w", encoding=args.encoding) as out_file:
            while True:
                if args.max_games is not None and scanned >= args.max_games:
                    break

                game = chess.pgn.read_game(in_file)
                if game is None:
                    break

                scanned += 1

                white_elo = parse_elo(game.headers.get("WhiteElo"))
                black_elo = parse_elo(game.headers.get("BlackElo"))

                if white_elo is None or black_elo is None:
                    skipped_missing_elo += 1
                    continue

                if not passes_threshold(white_elo, black_elo, args.min_elo, args.mode):
                    skipped_below_threshold += 1
                    continue

                exporter = chess.pgn.FileExporter(out_file)
                game.accept(exporter)
                out_file.write("\n\n")
                kept += 1

                if args.progress_every > 0 and scanned % args.progress_every == 0:
                    print(f"Processed {scanned} games, kept {kept}...", file=sys.stderr)

    except FileNotFoundError:
        print(f"Input file not found: {args.input_pgn}", file=sys.stderr)
        sys.exit(1)

    print("Done.")
    print(f"Input: {args.input_pgn}")
    print(f"Output: {args.output_pgn}")
    print(f"Scanned: {scanned}")
    print(f"Kept: {kept}")
    print(f"Skipped (missing/invalid Elo): {skipped_missing_elo}")
    print(f"Skipped (below threshold): {skipped_below_threshold}")


if __name__ == "__main__":
    main()

