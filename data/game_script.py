import pandas as pd

df = pd.read_csv('data/game.csv')
required_columns = ['game_id', 'game_date', 'team_abbreviation_home', 'team_abbreviation_away', 'wl_home', 'season_type']

df = df[required_columns]
df = df[df["season_type"].isin(["Regular Season", "Playoffs"])].drop(columns=["season_type"])
df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce").dt.strftime("%Y-%m-%d")

df.to_csv('data/game_summary.csv', index=False)