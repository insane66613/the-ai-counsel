import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import rehypeSanitize, { defaultSchema } from 'rehype-sanitize';

const REMARK_PLUGINS = [remarkGfm];
const SANITIZE_SCHEMA = {
  ...defaultSchema,
  tagNames: [...new Set([...(defaultSchema.tagNames || []), 'details', 'summary', 'mark'])],
};
// Preserve the small set of useful raw HTML model responses use, then strip
// active content and unsafe attributes before React sees it.
const REHYPE_PLUGINS = [rehypeRaw, [rehypeSanitize, SANITIZE_SCHEMA]];

export function MarkdownRenderer({ children }) {
  const content = typeof children === 'string' ? children : String(children || '');

  return (
    <ReactMarkdown remarkPlugins={REMARK_PLUGINS} rehypePlugins={REHYPE_PLUGINS}>
      {content}
    </ReactMarkdown>
  );
}

export default function MarkdownContent({ children, className = '' }) {
  const content = typeof children === 'string' ? children : String(children || '');
  const classes = ['markdown-content', className].filter(Boolean).join(' ');

  return (
    <div className={classes}>
      <MarkdownRenderer>{content}</MarkdownRenderer>
    </div>
  );
}
