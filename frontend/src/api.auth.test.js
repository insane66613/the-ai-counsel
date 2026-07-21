import { beforeEach, describe, expect, it, vi } from 'vitest';


describe('API admin authentication', () => {
  beforeEach(() => {
    vi.resetModules();
    vi.stubGlobal('window', {
      location: { hostname: 'localhost' },
      prompt: vi.fn(() => 'remote-admin-token'),
    });
  });

  it('prompts once and retries a 401 with a memory-only bearer token', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response('{"detail":"Authentication required"}', { status: 401 }))
      .mockResolvedValueOnce(new Response('[]', { status: 200 }));
    vi.stubGlobal('fetch', fetchMock);
    const { api } = await import('./api');

    await expect(api.listConversations()).resolves.toEqual([]);

    expect(window.prompt).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(fetchMock.mock.calls[1][1].headers.get('Authorization')).toBe('Bearer remote-admin-token');
  });
});
