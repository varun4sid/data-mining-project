import pandas as pd

GAME_SUMMARY_PATH = "dataset/game_summary.csv"
PBP_PATH = "dataset/pbp.csv"
OUTPUT_PATH = "dataset/play_by_play.csv"
CHUNK_SIZE = 500_000

def parse_pctimestring_to_seconds(series: pd.Series) -> pd.Series:
	parts = series.str.split(":", expand=True)
	minutes = pd.to_numeric(parts[0], errors="coerce")
	seconds = pd.to_numeric(parts[1], errors="coerce")
	return (minutes * 60 + seconds).fillna(0).astype(int)


game_summary = pd.read_csv(GAME_SUMMARY_PATH, usecols=["game_id", "wl_home"])
game_summary = game_summary.drop_duplicates(subset=["game_id"])

wl_home_map = dict(zip(game_summary["game_id"], game_summary["wl_home"]))
valid_game_ids = set(wl_home_map.keys())

reader = pd.read_csv(
	PBP_PATH,
	usecols=["game_id", "period", "pctimestring", "scoremargin"],
	chunksize=CHUNK_SIZE,
)

for chunk_index, chunk in enumerate(reader):
	filtered = chunk[chunk["game_id"].isin(valid_game_ids)].copy()
	if filtered.empty:
		continue

	period = pd.to_numeric(filtered["period"], errors="coerce").fillna(0).astype(int)
	period_offset_seconds = (4 - period) * (12 * 60)
	period_time_seconds = parse_pctimestring_to_seconds(filtered["pctimestring"].astype(str))

	filtered["time"] = (period_offset_seconds + period_time_seconds).astype(int)
	filtered["wl_home"] = filtered["game_id"].map(wl_home_map)
	filtered["wl_home"] = filtered["wl_home"].apply(lambda x: 1 if x == "W" else 0)

	output = filtered[["time", "scoremargin", "wl_home"]]
	output.to_csv(
		OUTPUT_PATH,
		mode="w" if chunk_index == 0 else "a",
		header=chunk_index == 0,
		index=False,
	)
