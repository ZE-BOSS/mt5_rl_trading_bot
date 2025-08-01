import os

def create_dirs():
    dirs = [
        'data/historical',
        'data/live',
        'models/production',
        'models/staging',
        'journals/trades',
        'journals/backtests',
        'tests/unit',
        'tests/integration'
    ]
    
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, '.gitkeep'), 'w') as f:
            pass

if __name__ == "__main__":
    create_dirs()