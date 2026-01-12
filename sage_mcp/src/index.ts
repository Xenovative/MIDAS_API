#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import {
  initDb,
  searchPapers,
  getPaperById,
  listTopics,
  listPublications,
  addPaper,
  getPapersByTopic,
  getPapersByPublication,
  type Paper,
} from './db.js';

const server = new Server(
  {
    name: 'sage-mcp',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
      resources: {},
    },
  }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'search_papers',
        description:
          'Search for academic papers and periodicals using semantic/keyword search. Returns relevant papers with titles, authors, abstracts, and relevance scores. Use this to find research on specific topics.',
        inputSchema: {
          type: 'object',
          properties: {
            query: {
              type: 'string',
              description: 'Search query - can be keywords, phrases, or natural language questions about the research topic',
            },
            limit: {
              type: 'number',
              description: 'Maximum number of results to return (default: 10, max: 50)',
              default: 10,
            },
            topic: {
              type: 'string',
              description: 'Optional: filter results to a specific topic/category',
            },
          },
          required: ['query'],
        },
      },
      {
        name: 'get_paper',
        description:
          'Retrieve the full content of a specific paper by its ID. Use this after search_papers to get the complete text for detailed analysis or citation.',
        inputSchema: {
          type: 'object',
          properties: {
            id: {
              type: 'number',
              description: 'The paper ID (obtained from search_papers results)',
            },
          },
          required: ['id'],
        },
      },
      {
        name: 'list_topics',
        description:
          'List all available research topics/categories in the database with paper counts. Use this to discover what subjects are covered.',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
      {
        name: 'list_publications',
        description:
          'List all journals and publications in the database with paper counts. Use this to see available sources.',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
      {
        name: 'get_papers_by_topic',
        description:
          'Get papers filtered by a specific topic. Returns papers sorted by publication date.',
        inputSchema: {
          type: 'object',
          properties: {
            topic: {
              type: 'string',
              description: 'The topic to filter by',
            },
            limit: {
              type: 'number',
              description: 'Maximum number of results (default: 20)',
              default: 20,
            },
          },
          required: ['topic'],
        },
      },
      {
        name: 'get_papers_by_publication',
        description:
          'Get papers from a specific journal or publication. Returns papers sorted by publication date.',
        inputSchema: {
          type: 'object',
          properties: {
            publication: {
              type: 'string',
              description: 'The publication/journal name',
            },
            limit: {
              type: 'number',
              description: 'Maximum number of results (default: 20)',
              default: 20,
            },
          },
          required: ['publication'],
        },
      },
      {
        name: 'add_paper',
        description:
          'Add a new paper to the database. Use this to expand the knowledge base with new research.',
        inputSchema: {
          type: 'object',
          properties: {
            title: { type: 'string', description: 'Paper title' },
            authors: { type: 'string', description: 'Comma-separated list of authors' },
            abstract: { type: 'string', description: 'Paper abstract' },
            content: { type: 'string', description: 'Full paper content/text' },
            publication: { type: 'string', description: 'Journal or publication name' },
            publication_date: { type: 'string', description: 'Publication date (YYYY-MM-DD format)' },
            doi: { type: 'string', description: 'DOI identifier (optional)' },
            url: { type: 'string', description: 'URL to the paper (optional)' },
            topics: { type: 'string', description: 'Comma-separated list of topics/categories' },
            keywords: { type: 'string', description: 'Comma-separated list of keywords' },
          },
          required: ['title', 'authors', 'abstract', 'content', 'publication', 'publication_date', 'topics', 'keywords'],
        },
      },
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'search_papers': {
        const query = args?.query as string;
        const limit = Math.min((args?.limit as number) || 10, 50);
        const topic = args?.topic as string | undefined;

        const results = searchPapers(query, limit, topic);

        if (results.length === 0) {
          return {
            content: [
              {
                type: 'text',
                text: `No papers found matching "${query}"${topic ? ` in topic "${topic}"` : ''}. Try different keywords or check available topics with list_topics.`,
              },
            ],
          };
        }

        const formatted = results.map((r, i) => 
          `## ${i + 1}. ${r.title}\n` +
          `**ID:** ${r.id} | **Authors:** ${r.authors}\n` +
          `**Publication:** ${r.publication} (${r.publication_date})\n` +
          `**Topics:** ${r.topics}\n` +
          `**Abstract:** ${r.abstract}\n`
        ).join('\n---\n\n');

        return {
          content: [
            {
              type: 'text',
              text: `Found ${results.length} relevant papers:\n\n${formatted}\n\nUse get_paper with the ID to retrieve full content.`,
            },
          ],
        };
      }

      case 'get_paper': {
        const id = args?.id as number;
        const paper = getPaperById(id);

        if (!paper) {
          return {
            content: [{ type: 'text', text: `Paper with ID ${id} not found.` }],
          };
        }

        return {
          content: [
            {
              type: 'text',
              text: formatPaperFull(paper),
            },
          ],
        };
      }

      case 'list_topics': {
        const topics = listTopics();
        if (topics.length === 0) {
          return {
            content: [{ type: 'text', text: 'No topics found. The database may be empty.' }],
          };
        }

        const formatted = topics.map(t => `- **${t.topic}**: ${t.count} paper(s)`).join('\n');
        return {
          content: [
            {
              type: 'text',
              text: `# Available Topics\n\n${formatted}`,
            },
          ],
        };
      }

      case 'list_publications': {
        const pubs = listPublications();
        if (pubs.length === 0) {
          return {
            content: [{ type: 'text', text: 'No publications found. The database may be empty.' }],
          };
        }

        const formatted = pubs.map(p => `- **${p.publication}**: ${p.count} paper(s)`).join('\n');
        return {
          content: [
            {
              type: 'text',
              text: `# Available Publications\n\n${formatted}`,
            },
          ],
        };
      }

      case 'get_papers_by_topic': {
        const topic = args?.topic as string;
        const limit = (args?.limit as number) || 20;
        const papers = getPapersByTopic(topic, limit);

        if (papers.length === 0) {
          return {
            content: [{ type: 'text', text: `No papers found in topic "${topic}".` }],
          };
        }

        const formatted = papers.map((p, i) => 
          `${i + 1}. **${p.title}** (ID: ${p.id})\n   ${p.authors} - ${p.publication} (${p.publication_date})`
        ).join('\n');

        return {
          content: [
            {
              type: 'text',
              text: `# Papers in "${topic}"\n\n${formatted}`,
            },
          ],
        };
      }

      case 'get_papers_by_publication': {
        const publication = args?.publication as string;
        const limit = (args?.limit as number) || 20;
        const papers = getPapersByPublication(publication, limit);

        if (papers.length === 0) {
          return {
            content: [{ type: 'text', text: `No papers found from "${publication}".` }],
          };
        }

        const formatted = papers.map((p, i) => 
          `${i + 1}. **${p.title}** (ID: ${p.id})\n   ${p.authors} (${p.publication_date})`
        ).join('\n');

        return {
          content: [
            {
              type: 'text',
              text: `# Papers from "${publication}"\n\n${formatted}`,
            },
          ],
        };
      }

      case 'add_paper': {
        const paper = {
          title: args?.title as string,
          authors: args?.authors as string,
          abstract: args?.abstract as string,
          content: args?.content as string,
          publication: args?.publication as string,
          publication_date: args?.publication_date as string,
          doi: (args?.doi as string) || null,
          url: (args?.url as string) || null,
          topics: args?.topics as string,
          keywords: args?.keywords as string,
        };

        const id = addPaper(paper);
        return {
          content: [
            {
              type: 'text',
              text: `Paper added successfully with ID: ${id}\n\nTitle: ${paper.title}\nAuthors: ${paper.authors}`,
            },
          ],
        };
      }

      default:
        return {
          content: [{ type: 'text', text: `Unknown tool: ${name}` }],
          isError: true,
        };
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return {
      content: [{ type: 'text', text: `Error: ${message}` }],
      isError: true,
    };
  }
});

server.setRequestHandler(ListResourcesRequestSchema, async () => {
  const topics = listTopics();
  const publications = listPublications();

  return {
    resources: [
      {
        uri: 'sage://topics',
        name: 'Available Topics',
        description: `List of ${topics.length} research topics in the database`,
        mimeType: 'text/plain',
      },
      {
        uri: 'sage://publications',
        name: 'Available Publications',
        description: `List of ${publications.length} journals/publications in the database`,
        mimeType: 'text/plain',
      },
    ],
  };
});

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const { uri } = request.params;

  if (uri === 'sage://topics') {
    const topics = listTopics();
    const text = topics.map(t => `${t.topic}: ${t.count} papers`).join('\n');
    return {
      contents: [{ uri, mimeType: 'text/plain', text }],
    };
  }

  if (uri === 'sage://publications') {
    const pubs = listPublications();
    const text = pubs.map(p => `${p.publication}: ${p.count} papers`).join('\n');
    return {
      contents: [{ uri, mimeType: 'text/plain', text }],
    };
  }

  throw new Error(`Unknown resource: ${uri}`);
});

function formatPaperFull(paper: Paper): string {
  return `# ${paper.title}

**Authors:** ${paper.authors}
**Publication:** ${paper.publication}
**Date:** ${paper.publication_date}
${paper.doi ? `**DOI:** ${paper.doi}` : ''}
${paper.url ? `**URL:** ${paper.url}` : ''}
**Topics:** ${paper.topics}
**Keywords:** ${paper.keywords}

## Abstract

${paper.abstract}

## Full Content

${paper.content}
`;
}

async function main() {
  await initDb();
  
  const transport = new StdioServerTransport();
  await server.connect(transport);
  
  console.error('Sage MCP Server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
