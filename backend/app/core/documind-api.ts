export const API_BASE = 'http://127.0.0.1:8000';

export class DocuMindApi {

  async request<T = any>(
    path: string,
    method = 'GET',
    body?: any
  ): Promise<T> {

    const options: RequestInit = { method };

    if (body instanceof FormData) {
      options.body = body;
    } else if (body !== undefined) {
      options.headers = {
        'Content-Type': 'application/json'
      };
      options.body = JSON.stringify(body);
    }

    const response = await fetch(
      `${API_BASE}${path}`,
      options
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));

      throw new Error(
        typeof error.detail === 'string'
          ? error.detail
          : JSON.stringify(error.detail || response.statusText)
      );
    }

    return response.json();
  }

  documents() {
    return this.request('/api/documents/');
  }

  statistics() {
    return this.request('/api/documents/statistics');
  }

  backendHealth() {
    return this.request('/api/health');
  }

  aiHealth() {
    return this.request('/api/chat/health');
  }

  upload(file: File) {

    const form = new FormData();
    form.append('file', file);

    return this.request(
      '/api/documents/upload',
      'POST',
      form
    );
  }

  process(id: string) {
    return this.request(
      `/api/intelligence/process/${id}`,
      'POST'
    );
  }

  renameDocument(id: string, filename: string) {
    return this.request(
      `/api/documents/${id}/rename`,
      'PATCH',
      { filename }
    );
  }

  deleteDocument(id: string) {
    return this.request(
      `/api/documents/${id}`,
      'DELETE'
    );
  }

  conversations() {
    return this.request('/api/chat/conversations');
  }

  createConversation(title: string, document_ids: string[]) {
    return this.request(
      '/api/chat/conversations',
      'POST',
      { title, document_ids }
    );
  }

  conversation(id: string) {
    return this.request(
      `/api/chat/conversations/${id}`
    );
  }

  renameConversation(id: string, title: string) {
    return this.request(
      `/api/chat/conversations/${id}`,
      'PATCH',
      { title }
    );
  }

  deleteConversation(id: string) {
    return this.request(
      `/api/chat/conversations/${id}`,
      'DELETE'
    );
  }

  summaries() {
    return this.request('/api/summaries/');
  }

  generateSummary(
    document_ids: string[],
    summary_type: string,
    force_refresh = false
  ) {
    return this.request(
      '/api/summaries/generate',
      'POST',
      { document_ids, summary_type, force_refresh }
    );
  }

  deleteSummary(id: string) {
    return this.request(
      `/api/summaries/${id}`,
      'DELETE'
    );
  }

  notes() {
    return this.request('/api/notes/');
  }

  createNote(body: any) {
    return this.request('/api/notes/', 'POST', body);
  }

  updateNote(id: string, body: any) {
    return this.request(
      `/api/notes/${id}`,
      'PUT',
      body
    );
  }

  generateNote(document_ids: string[], title: string) {
    return this.request(
      '/api/notes/generate',
      'POST',
      {
        document_ids,
        title,
        category: 'AI Insights'
      }
    );
  }

  deleteNote(id: string) {
    return this.request(
      `/api/notes/${id}`,
      'DELETE'
    );
  }

  async streamChat(
    id: string,
    question: string,
    onEvent: (event: any) => void
  ) {

    const response = await fetch(
      `${API_BASE}/api/chat/conversations/${id}/stream`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ question })
      }
    );

    if (!response.ok || !response.body) {
      throw new Error('Unable to start AI conversation.');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let buffer = '';
    let completed = false;

    const handleLine = (line: string) => {

      if (!line.startsWith('data:')) return;

      const event = JSON.parse(line.slice(5).trim());

      if (event.type === 'error') {
        throw new Error(event.message);
      }

      if (event.type === 'done') {
        completed = true;
      }

      onEvent(event);
    };

    try {

      while (true) {

        const { value, done } = await reader.read();

        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          handleLine(line.trim());
        }
      }

      buffer += decoder.decode();

      if (buffer.trim()) {
        handleLine(buffer.trim());
      }

      if (!completed) {
        throw new Error('AI response ended unexpectedly.');
      }

    } finally {
      await reader.cancel().catch(() => {});
      reader.releaseLock();
    }
  }
}