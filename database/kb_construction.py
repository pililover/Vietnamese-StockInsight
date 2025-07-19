import sqlite3

# Tạo kết nối tới file DB
conn = sqlite3.connect('stock_insights.db')
c = conn.cursor()

# Articles
c.execute('''
CREATE TABLE IF NOT EXISTS Articles (
    article_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT NOT NULL,
    source_url   TEXT,
    publish_date TEXT,
    content      TEXT NOT NULL
);
''')

# Tạo bảng Entities
c.execute('''
CREATE TABLE IF NOT EXISTS Entities (
    entity_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id   INTEGER NOT NULL,
    entity_text  TEXT NOT NULL,
    entity_type  TEXT NOT NULL,
    confidence   TEXT CHECK(confidence IN ('high','medium')),
    detected_by  TEXT CHECK(detected_by IN ('ensemble','phoBERT_only','xlmr_only')),
    FOREIGN KEY(article_id) REFERENCES Articles(article_id) ON DELETE CASCADE
);
''')

# Tạo bảng Sentences
c.execute('''
CREATE TABLE IF NOT EXISTS Sentences (
    sentence_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id      INTEGER NOT NULL,
    sentence_text   TEXT NOT NULL,
    sentiment_label TEXT,
    sentiment_score REAL,
    FOREIGN KEY(article_id) REFERENCES Articles(article_id) ON DELETE CASCADE
);
''')

conn.commit()
conn.close()
print("DB and tables created successfully.")