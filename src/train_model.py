import sqlite3
import pickle
import river.tree as tree
import river.metrics as metrics

DB_PATH = '../db/nba_data.db'
MODEL_PATH = 'hoeffding_model.pkl'

def train():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    model = tree.HoeffdingTreeClassifier()
    # Brier Score is mathematically equivalent to Mean Squared Error for probabilities
    metric = metrics.MSE()
    
    # Server-side cursor / fetching row by row
    cursor.execute("SELECT time_left_seconds, point_differential, home_win FROM pbp_data")
    
    count = 0
    print("Starting streaming model training...")
    while True:
        rows = cursor.fetchmany(100000)
        if not rows:
            break
        
        for time_left, pt_diff, home_win in rows:
            x = {'time_left': time_left, 'point_diff': pt_diff}
            y = home_win
            
            y_pred_proba = model.predict_proba_one(x)
            if y_pred_proba:
                prob_1 = y_pred_proba.get(1, 0.0)
                metric.update(y, prob_1)
            
            model.learn_one(x, y)
            count += 1
            
        print(f"Trained on {count:,} rows. Brier Score: {metric.get():.4f}")

    print(f"Final Brier Score after {count:,} rows: {metric.get():.4f}")
    
    print("Saving model to", MODEL_PATH)
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
        
    conn.close()

if __name__ == "__main__":
    train()
