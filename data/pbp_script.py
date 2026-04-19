import pandas as pd

INPUT_PATH = "data/play_by_play.csv"
OUTPUT_PATH = "data/pbp.csv"
CHUNK_SIZE = 200_000
PROGRESS_STEP = 100_000

def count_data_rows(csv_path: str) -> int:
	# Count newline-delimited records once to provide deterministic progress logs.
	with open(csv_path, "rb") as f:
		line_count = 0
		for buffer in iter(lambda: f.read(1024 * 1024), b""):
			line_count += buffer.count(b"\n")
	return max(line_count - 1, 0)

required_columns = ['game_id', 'period', 'pctimestring', 'scoremargin']

total_rows = count_data_rows(INPUT_PATH)
processed_rows = 0
next_log_threshold = PROGRESS_STEP

reader = pd.read_csv(INPUT_PATH, usecols=required_columns, chunksize=CHUNK_SIZE)

for chunk_index, chunk in enumerate(reader):
	filtered = chunk[
		chunk['period'].isin([1, 2, 3, 4])
		& ~chunk['scoremargin'].isin(['TIE',None])
	]

	filtered.to_csv(
		OUTPUT_PATH,
		mode='w' if chunk_index == 0 else 'a',
		header=chunk_index == 0,
		index=False,
	)

	processed_rows += len(chunk)
	while next_log_threshold <= processed_rows:
		print(f"{next_log_threshold:,}/{total_rows:,}")
		next_log_threshold += PROGRESS_STEP

if processed_rows % PROGRESS_STEP != 0:
	print(f"{processed_rows:,}/{total_rows:,}")