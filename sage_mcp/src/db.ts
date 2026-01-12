import Database from 'better-sqlite3';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DB_PATH = process.env.SAGE_DB_PATH || path.join(__dirname, '..', 'data', 'sage.db');

export interface Paper {
  id: number;
  title: string;
  authors: string;
  abstract: string;
  content: string;
  publication: string;
  publication_date: string;
  doi: string | null;
  url: string | null;
  topics: string;
  keywords: string;
  created_at: string;
}

export interface SearchResult {
  id: number;
  title: string;
  authors: string;
  abstract: string;
  publication: string;
  publication_date: string;
  topics: string;
  relevance_score: number;
}

let db: Database.Database | null = null;

export function getDb(): Database.Database {
  if (!db) {
    throw new Error('Database not initialized. Call initDb() first.');
  }
  return db;
}

export async function initDb(): Promise<Database.Database> {
  const fs = await import('fs');
  const dir = path.dirname(DB_PATH);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  db = new Database(DB_PATH);
  initSchema();
  return db;
}

function initSchema(): void {
  if (!db) return;
  
  db.exec(`
    CREATE TABLE IF NOT EXISTS papers (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      authors TEXT NOT NULL,
      abstract TEXT NOT NULL,
      content TEXT NOT NULL,
      publication TEXT NOT NULL,
      publication_date TEXT NOT NULL,
      doi TEXT,
      url TEXT,
      topics TEXT NOT NULL,
      keywords TEXT NOT NULL,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_papers_topics ON papers(topics);
    CREATE INDEX IF NOT EXISTS idx_papers_publication ON papers(publication);
    CREATE INDEX IF NOT EXISTS idx_papers_date ON papers(publication_date);

    CREATE VIRTUAL TABLE IF NOT EXISTS papers_fts USING fts5(
      title,
      authors,
      abstract,
      content,
      topics,
      keywords,
      content='papers',
      content_rowid='id'
    );

    CREATE TRIGGER IF NOT EXISTS papers_ai AFTER INSERT ON papers BEGIN
      INSERT INTO papers_fts(rowid, title, authors, abstract, content, topics, keywords)
      VALUES (new.id, new.title, new.authors, new.abstract, new.content, new.topics, new.keywords);
    END;

    CREATE TRIGGER IF NOT EXISTS papers_ad AFTER DELETE ON papers BEGIN
      INSERT INTO papers_fts(papers_fts, rowid, title, authors, abstract, content, topics, keywords)
      VALUES ('delete', old.id, old.title, old.authors, old.abstract, old.content, old.topics, old.keywords);
    END;

    CREATE TRIGGER IF NOT EXISTS papers_au AFTER UPDATE ON papers BEGIN
      INSERT INTO papers_fts(papers_fts, rowid, title, authors, abstract, content, topics, keywords)
      VALUES ('delete', old.id, old.title, old.authors, old.abstract, old.content, old.topics, old.keywords);
      INSERT INTO papers_fts(rowid, title, authors, abstract, content, topics, keywords)
      VALUES (new.id, new.title, new.authors, new.abstract, new.content, new.topics, new.keywords);
    END;
  `);
}

export function searchPapers(query: string, limit: number = 10, topic?: string): SearchResult[] {
  const database = db;
  if (!database) throw new Error('Database not initialized');

  let sql: string;
  let params: any[];

  if (topic) {
    sql = `
      SELECT p.id, p.title, p.authors, p.abstract, p.publication, p.publication_date, p.topics,
             bm25(papers_fts) as relevance_score
      FROM papers_fts fts
      JOIN papers p ON fts.rowid = p.id
      WHERE papers_fts MATCH ? AND p.topics LIKE ?
      ORDER BY relevance_score
      LIMIT ?
    `;
    params = [query, `%${topic}%`, limit];
  } else {
    sql = `
      SELECT p.id, p.title, p.authors, p.abstract, p.publication, p.publication_date, p.topics,
             bm25(papers_fts) as relevance_score
      FROM papers_fts fts
      JOIN papers p ON fts.rowid = p.id
      WHERE papers_fts MATCH ?
      ORDER BY relevance_score
      LIMIT ?
    `;
    params = [query, limit];
  }

  return database.prepare(sql).all(...params) as SearchResult[];
}

export function getPaperById(id: number): Paper | undefined {
  const database = db;
  if (!database) throw new Error('Database not initialized');
  
  return database.prepare('SELECT * FROM papers WHERE id = ?').get(id) as Paper | undefined;
}

export function listTopics(): { topic: string; count: number }[] {
  const database = db;
  if (!database) throw new Error('Database not initialized');

  const papers = database.prepare('SELECT topics FROM papers').all() as { topics: string }[];
  const topicCounts = new Map<string, number>();

  for (const paper of papers) {
    const topics = paper.topics.split(',').map(t => t.trim());
    for (const topic of topics) {
      topicCounts.set(topic, (topicCounts.get(topic) || 0) + 1);
    }
  }

  return Array.from(topicCounts.entries())
    .map(([topic, count]) => ({ topic, count }))
    .sort((a, b) => b.count - a.count);
}

export function listPublications(): { publication: string; count: number }[] {
  const database = db;
  if (!database) throw new Error('Database not initialized');

  return database.prepare(`
    SELECT publication, COUNT(*) as count 
    FROM papers 
    GROUP BY publication 
    ORDER BY count DESC
  `).all() as { publication: string; count: number }[];
}

export function addPaper(paper: Omit<Paper, 'id' | 'created_at'>): number {
  const database = db;
  if (!database) throw new Error('Database not initialized');

  const stmt = database.prepare(`
    INSERT INTO papers (title, authors, abstract, content, publication, publication_date, doi, url, topics, keywords)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);

  const result = stmt.run(
    paper.title,
    paper.authors,
    paper.abstract,
    paper.content,
    paper.publication,
    paper.publication_date,
    paper.doi,
    paper.url,
    paper.topics,
    paper.keywords
  );

  return result.lastInsertRowid as number;
}

export function getPapersByTopic(topic: string, limit: number = 20): Paper[] {
  const database = db;
  if (!database) throw new Error('Database not initialized');

  return database.prepare(`
    SELECT * FROM papers 
    WHERE topics LIKE ? 
    ORDER BY publication_date DESC 
    LIMIT ?
  `).all(`%${topic}%`, limit) as Paper[];
}

export function getPapersByPublication(publication: string, limit: number = 20): Paper[] {
  const database = db;
  if (!database) throw new Error('Database not initialized');

  return database.prepare(`
    SELECT * FROM papers 
    WHERE publication = ? 
    ORDER BY publication_date DESC 
    LIMIT ?
  `).all(publication, limit) as Paper[];
}
