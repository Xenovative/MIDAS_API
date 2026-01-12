import { initDb, addPaper } from './db.js';
import { readFileSync } from 'fs';
import { XMLParser } from 'fast-xml-parser';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

interface PaperXML {
  metadata: {
    title: string;
    author?: string;
    year?: string;
    periodical?: string;
    pages?: string;
    affiliation?: string;
    subtitle?: string;
  };
  content: string;
  path: string;
}

interface PapersDatabase {
  PapersDatabase: {
    Papers: {
      Paper: PaperXML[];
    };
  };
}

async function importXML() {
  const xmlPath = process.argv[2] || path.join(__dirname, '..', 'data', 'papers_database.xml');
  
  console.log(`Reading XML from: ${xmlPath}`);
  const xmlContent = readFileSync(xmlPath, 'utf-8');
  
  console.log('Parsing XML...');
  const parser = new XMLParser({
    ignoreAttributes: false,
    attributeNamePrefix: '@_',
    textNodeName: '#text',
  });
  
  const parsed = parser.parse(xmlContent) as PapersDatabase;
  const papers = parsed.PapersDatabase.Papers.Paper;
  
  console.log(`Found ${papers.length} papers to import`);
  
  await initDb();
  
  let imported = 0;
  let failed = 0;
  
  for (const paper of papers) {
    try {
      const meta = paper.metadata;
      const title = meta.title || 'Untitled';
      const author = meta.author || 'Unknown';
      const content = paper.content || '';
      
      // Extract year from metadata or default
      const year = meta.year || '1994';
      const publicationDate = `${year}-01-01`;
      
      // Build full title with subtitle if present
      const fullTitle = meta.subtitle ? `${title}：${meta.subtitle}` : title;
      
      // Use periodical name as publication
      const publication = meta.periodical || '道風：漢語神學學刊';
      
      // Generate topics based on content analysis
      const topics = generateTopics(fullTitle, content);
      
      // Generate keywords from title
      const keywords = generateKeywords(fullTitle, content);
      
      // Create abstract from first ~500 chars of content
      const abstract = generateAbstract(content);
      
      const id = addPaper({
        title: fullTitle,
        authors: author,
        abstract,
        content,
        publication,
        publication_date: publicationDate,
        doi: null,
        url: null,
        topics,
        keywords,
      });
      
      imported++;
      if (imported % 50 === 0) {
        console.log(`Imported ${imported} papers...`);
      }
    } catch (error) {
      failed++;
      console.error(`Failed to import paper: ${paper.metadata?.title || 'unknown'}`, error);
    }
  }
  
  console.log(`\nImport complete!`);
  console.log(`Successfully imported: ${imported}`);
  console.log(`Failed: ${failed}`);
}

function generateTopics(title: string, content: string): string {
  const topics: string[] = [];
  const text = (title + ' ' + content).toLowerCase();
  
  // Theology topics
  if (text.includes('神學') || text.includes('theology')) topics.push('神學');
  if (text.includes('基督') || text.includes('christ')) topics.push('基督教');
  if (text.includes('聖經') || text.includes('bible') || text.includes('舊約') || text.includes('新約')) topics.push('聖經研究');
  if (text.includes('哲學') || text.includes('philosophy')) topics.push('哲學');
  if (text.includes('倫理') || text.includes('ethics')) topics.push('倫理學');
  if (text.includes('歷史') || text.includes('history')) topics.push('歷史');
  if (text.includes('文化') || text.includes('culture')) topics.push('文化研究');
  if (text.includes('儒') || text.includes('confuci')) topics.push('儒學');
  if (text.includes('佛') || text.includes('buddhis')) topics.push('佛學');
  if (text.includes('道家') || text.includes('taois')) topics.push('道家');
  if (text.includes('現代') || text.includes('modern')) topics.push('現代性');
  if (text.includes('後現代') || text.includes('postmodern')) topics.push('後現代');
  if (text.includes('宗教') || text.includes('religio')) topics.push('宗教學');
  if (text.includes('教會') || text.includes('church')) topics.push('教會');
  if (text.includes('社會') || text.includes('social')) topics.push('社會學');
  if (text.includes('政治') || text.includes('politic')) topics.push('政治');
  
  // Default topic if none matched
  if (topics.length === 0) {
    topics.push('漢語神學');
  }
  
  return topics.slice(0, 5).join(', ');
}

function generateKeywords(title: string, content: string): string {
  // Extract key terms from title
  const keywords: string[] = [];
  
  // Add title words as keywords (filter short ones)
  const titleWords = title.split(/[，、：\s]+/).filter(w => w.length >= 2);
  keywords.push(...titleWords.slice(0, 5));
  
  return keywords.join(', ');
}

function generateAbstract(content: string): string {
  if (!content) return 'No abstract available.';
  
  // Clean up content - remove page markers and extra whitespace
  let cleaned = content
    .replace(/Blank\s*Page\s*此頁為空白頁/g, '')
    .replace(/\d+\s*《道風》漢語神學學刊/g, '')
    .replace(/第.+期．\d+年．[春夏秋冬]/g, '')
    .trim();
  
  // Take first ~500 characters as abstract
  if (cleaned.length > 500) {
    cleaned = cleaned.substring(0, 500);
    // Try to end at a sentence
    const lastPeriod = Math.max(
      cleaned.lastIndexOf('。'),
      cleaned.lastIndexOf('！'),
      cleaned.lastIndexOf('？')
    );
    if (lastPeriod > 300) {
      cleaned = cleaned.substring(0, lastPeriod + 1);
    } else {
      cleaned += '...';
    }
  }
  
  return cleaned || 'No abstract available.';
}

importXML().catch(console.error);
