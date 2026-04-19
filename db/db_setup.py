import sqlite3
import pandas as pd
import os

DB_PATH = 'db/nba_data.db'
GAME_SUMMARY_CSV = 'dataset/game_summary.csv'
PBP_CSV = 'dataset/play_by_play.csv'

def setup_db():
    os.makedirs('db', exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table 1: game_summary
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS game_summary (
        game_id TEXT PRIMARY KEY,
        game_date DATE,
        team_abbreviation_home TEXT,
        team_abbreviation_away TEXT,
        wl_home INTEGER
    )
    ''')
    
    # Table 2: pbp_data
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pbp_data (
        time_left_seconds INTEGER,
        point_differential INTEGER,
        home_win INTEGER
    )
    ''')
    
    print("Ingesting game_summary.csv...")
    df_game = pd.read_csv(GAME_SUMMARY_CSV)
    df_game['wl_home'] = df_game['wl_home'].apply(lambda x: 1 if x == 'W' else 0)
    df_game.to_sql('game_summary', conn, if_exists='replace', index=False)
    
    print("Ingesting play_by_play.csv...")
    # The columns in dataset/play_by_play.csv are time, scoremargin, wl_home
    chunksize = 200_000
    for i, chunk in enumerate(pd.read_csv(PBP_CSV, chunksize=chunksize)):
        chunk = chunk.rename(columns={
            'time': 'time_left_seconds',
            'scoremargin': 'point_differential',
            'wl_home': 'home_win'
        })
        
        # Ensure values are within bounds as defined in instructions
        chunk['time_left_seconds'] = chunk['time_left_seconds'].clip(lower=0, upper=2880)
        
        chunk.to_sql('pbp_data', conn, if_exists='append' if i > 0 else 'replace', index=False)
        print(f"Ingested { (i+1)*len(chunk) } rows")
        
    conn.close()
    print("Data ingestion complete!")

if __name__ == "__main__":
    setup_db()
