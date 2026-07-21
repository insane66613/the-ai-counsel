import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import MarkdownContent from './MarkdownContent';


describe('MarkdownContent security', () => {
  it('removes active HTML from untrusted markdown', () => {
    const html = renderToStaticMarkup(
      <MarkdownContent>{'<iframe srcdoc="<script>window.pwned=true</script>"></iframe><script>alert(1)</script>Safe'}</MarkdownContent>,
    );

    expect(html).toContain('Safe');
    expect(html).not.toContain('<iframe');
    expect(html).not.toContain('<script');
    expect(html).not.toContain('srcdoc');
  });

  it('preserves the safe raw HTML used by model responses', () => {
    const html = renderToStaticMarkup(
      <MarkdownContent>{'<details><summary>Reasoning</summary><mark>Useful</mark></details>'}</MarkdownContent>,
    );

    expect(html).toContain('<details>');
    expect(html).toContain('<summary>Reasoning</summary>');
    expect(html).toContain('<mark>Useful</mark>');
  });
});
