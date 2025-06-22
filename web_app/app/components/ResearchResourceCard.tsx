import React from 'react';

export interface ResearchResource {
  title: string;
  url: string;
  type: string;
  source: string;
  description: string;
  relevance_score: number;
  research_task?: string;
}

const sourceIcons: Record<string, string> = {
  'YouTube': '📺',
  'Medium': '📝',
  'Stack Overflow': '💻',
  'GitHub': '🐙',
  'Documentation': '📚',
  'Udemy': '🎓',
  'Stanford University': '🎓',
  'Google Developers': '🔍',
  "O'Reilly": '📖',
};

export default function ResearchResourceCard({ resource }: { resource: ResearchResource }) {
  const typeIcon = resource.type.toLowerCase() === 'video' ? '🎥' : '📄';
  const sourceIcon = sourceIcons[resource.source] || '🔗';

  return (
    <div className="bg-card rounded-lg border border-border p-4 flex flex-col gap-2 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-center gap-2">
        <span className="text-2xl">{typeIcon}</span>
        <a
          href={resource.url}
          target="_blank"
          rel="noopener noreferrer"
          className="font-semibold text-lg text-primary hover:underline"
        >
          {resource.title}
        </a>
        <span className="ml-auto flex items-center gap-1 text-sm text-muted-foreground">
          <span>{sourceIcon}</span>
          <span>{resource.source}</span>
        </span>
      </div>
      <div className="text-sm text-muted-foreground line-clamp-3">{resource.description}</div>
      <div className="flex items-center gap-3 text-xs mt-1">
        <span className="bg-secondary rounded px-2 py-0.5">Relevance: {resource.relevance_score}/10</span>
        {resource.research_task && (
          <span className="bg-accent rounded px-2 py-0.5">Topic: {resource.research_task}</span>
        )}
      </div>
    </div>
  );
} 