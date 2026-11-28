import {
  Component,
  OnInit,
  ChangeDetectorRef
} from '@angular/core';

import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import {
  DocuMindApi,
  API_BASE
} from '../core/documind-api';


@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './workspace.html'
})
export class Workspace implements OnInit {

  api = new DocuMindApi();
  base = API_BASE;

  page = 'Dashboard';

  navigation = [
    { name: 'Dashboard', icon: 'bi-grid-1x2' },
    { name: 'Documents', icon: 'bi-folder2-open' },
    { name: 'AI Chat', icon: 'bi-chat-square-text' },
    { name: 'Summaries', icon: 'bi-stars' },
    { name: 'Smart Notes', icon: 'bi-journal-richtext' },
    { name: 'Settings', icon: 'bi-sliders' }
  ];

  descriptions: Record<string, string> = {
    Dashboard: 'Your intelligent document workspace.',
    Documents: 'Organize, manage and prepare your knowledge.',
    'AI Chat': 'Turn your documents into conversations.',
    Summaries: 'Discover what matters in less time.',
    'Smart Notes': 'Transform information into organized knowledge.',
    Settings: 'Manage your local intelligence environment.'
  };

  documents: any[] = [];
  conversations: any[] = [];
  summaries: any[] = [];
  notes: any[] = [];
  messages: any[] = [];

  stats: any = {};
  ai: any = {};
  backend: any = {};

  selected: string[] = [];
  activeConversation: any = null;
  activeSummary: any = null;

  search = '';
  question = '';
  summaryType = 'executive';
  forceRefresh = false;

  noteSearch = '';
  noteCategory = '';
  noteTag = '';

  editingNote: any = null;

  noteForm = {
    title: '',
    content: '',
    category: 'General',
    tags: ''
  };

  busy = false;
  loadingText = '';
  notice = '';
  noticeType = 'success';

  dragging = false;
  sidebarOpen = false;

  private noticeTimer: any;

  constructor(private cdr: ChangeDetectorRef) {}

  async ngOnInit() {

    try {
      const saved = JSON.parse(
        localStorage.getItem('documind-selected') || '[]'
      );

      this.selected = Array.isArray(saved)
        ? saved.filter(id => typeof id === 'string')
        : [];

    } catch {
      this.selected = [];
    }

    await this.refresh();
  }

  get readyDocuments() {
    return this.documents.filter(
      d => d.status === 'processed'
    );
  }

  get filteredDocuments() {

    const query = this.search.toLowerCase();

    return this.documents.filter(
      d => d.filename.toLowerCase().includes(query)
    );
  }

  get filteredNotes() {

    const query = this.noteSearch.toLowerCase();

    return this.notes.filter(n =>
      `${n.title} ${n.content}`.toLowerCase().includes(query)
      && (!this.noteCategory || n.category === this.noteCategory)
      && (!this.noteTag || n.tags.includes(this.noteTag))
    );
  }

  get categories(): string[] {
    return [...new Set<string>(
      this.notes.map(n => n.category)
    )];
  }

  get tags(): string[] {
    return [...new Set<string>(
      this.notes.flatMap(n => n.tags || [])
    )];
  }

  navigate(page: string) {
    if (this.busy) return;
    this.page = page;
    this.sidebarOpen = false;
  }

  notify(message: string, type = 'success') {

    this.notice = message;
    this.noticeType = type;

    clearTimeout(this.noticeTimer);

    this.noticeTimer = setTimeout(() => {
      this.notice = '';
      this.cdr.detectChanges();
    }, 5000);

    this.cdr.detectChanges();
  }

  async refresh() {

    const results = await Promise.allSettled([
      this.api.documents(),
      this.api.statistics(),
      this.api.conversations(),
      this.api.summaries(),
      this.api.notes(),
      this.api.backendHealth(),
      this.api.aiHealth()
    ]);

    const keys = [
      'documents', 'stats', 'conversations',
      'summaries', 'notes', 'backend', 'ai'
    ];

    results.forEach((result, index) => {

      if (result.status === 'fulfilled') {
        (this as any)[keys[index]] = result.value;
      }

    });

    if (results[5].status === 'rejected') {
      this.backend = {};
    }

    if (results[6].status === 'rejected') {
      this.ai = { connected: false };
    }

    this.selected = this.selected.filter(
      id => this.readyDocuments.some(d => d.id === id)
    );

    this.saveSelection();

    this.cdr.detectChanges();
  }

  async run(
    label: string,
    action: () => Promise<void>
  ) {

    if (this.busy) return;

    this.busy = true;
    this.loadingText = label;

    try {
      await action();
    } catch (error: any) {
      this.notify(error.message || 'Operation failed.', 'error');
    } finally {
      this.busy = false;
      this.loadingText = '';
      this.cdr.detectChanges();
    }
  }

  saveSelection() {
    localStorage.setItem(
      'documind-selected',
      JSON.stringify(this.selected)
    );
  }

  toggleDocument(id: string) {

    if (this.selected.includes(id)) {
      this.selected = this.selected.filter(x => x !== id);
    } else {

      if (this.selected.length >= 20) {
        this.notify('Select a maximum of 20 documents.', 'error');
        return;
      }

      this.selected = [...this.selected, id];
    }

    this.saveSelection();
  }

  fileSize(bytes: number): string {

    if (!bytes) return '0 B';

    if (bytes < 1024) return `${bytes} B`;

    if (bytes < 1048576) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }

    return `${(bytes / 1048576).toFixed(1)} MB`;
  }

  fileIcon(extension: string): string {

    const icons: Record<string, string> = {
      '.pdf': 'bi-file-earmark-pdf',
      '.docx': 'bi-file-earmark-word',
      '.doc': 'bi-file-earmark-word',
      '.xlsx': 'bi-file-earmark-excel',
      '.xls': 'bi-file-earmark-excel',
      '.csv': 'bi-filetype-csv',
      '.json': 'bi-filetype-json'
    };

    return icons[extension] || 'bi-file-earmark-text';
  }

  async uploadFiles(files: FileList | File[]) {

    if (!files.length) return;

    await this.run('Uploading and processing documents', async () => {

      let completed = 0;
      const failures: string[] = [];

      for (const file of Array.from(files)) {

        try {

          this.loadingText = `Processing ${file.name}`;

          const document = await this.api.upload(file);

          if (document.status !== 'processed') {
            await this.api.process(document.id);
          }

          completed++;

        } catch (error: any) {
          failures.push(`${file.name}: ${error.message}`);
        }
      }

      await this.refresh();

      this.notify(
        failures.length
          ? `${completed} uploaded. ${failures.join('; ')}`
          : `${completed} document(s) uploaded.`,
        failures.length ? 'error' : 'success'
      );
    });
  }

  onFileInput(event: Event) {

    const input = event.target as HTMLInputElement;

    if (input.files) {
      this.uploadFiles(Array.from(input.files));
    }

    input.value = '';
  }

  onDrop(event: DragEvent) {

    event.preventDefault();
    this.dragging = false;

    if (event.dataTransfer?.files) {
      this.uploadFiles(event.dataTransfer.files);
    }
  }

  async processDocument(document: any) {

    await this.run('Processing document', async () => {
      await this.api.process(document.id);
      await this.refresh();
      this.notify('Processing request completed.');
    });
  }

  async renameDocument(document: any) {

    const filename = prompt(
      'Enter the new filename, including its extension:',
      document.filename
    );

    if (!filename || filename === document.filename) return;

    await this.run('Renaming document', async () => {
      await this.api.renameDocument(document.id, filename);
      await this.refresh();
      this.notify('Document renamed.');
    });
  }

  async deleteDocument(document: any) {

    if (!confirm(
      `Delete "${document.filename}"? Existing chats referencing it may be affected.`
    )) return;

    await this.run('Deleting document', async () => {
      await this.api.deleteDocument(document.id);
      await this.refresh();
      this.notify('Document deleted.');
    });
  }

  download(path: string) {

    const link = window.document.createElement('a');
    link.href = this.base + path;
    link.click();
  }

  async newConversation() {

    if (!this.selected.length) {
      this.notify('Select at least one processed document.', 'error');
      return;
    }

    await this.run('Creating conversation', async () => {

      const conversation = await this.api.createConversation(
        `Document Chat ${new Date().toLocaleDateString()}`,
        this.selected
      );

      this.activeConversation = conversation;
      this.messages = [];

      await this.refresh();

      this.notify('Conversation created.');
    });
  }

  async openConversation(conversation: any) {

    await this.run('Loading conversation', async () => {

      const result = await this.api.conversation(conversation.id);

      this.activeConversation = result;
      this.messages = result.messages || [];

      this.selected = result.document_ids.filter(
        (id: string) => this.readyDocuments.some(d => d.id === id)
      );

      this.saveSelection();
    });
  }

  async renameConversation(conversation: any) {

    const title = prompt('Conversation title:', conversation.title);

    if (!title?.trim()) return;

    await this.run('Renaming conversation', async () => {

      const updated = await this.api.renameConversation(
        conversation.id,
        title
      );

      if (this.activeConversation?.id === conversation.id) {
        this.activeConversation = updated;
      }

      await this.refresh();
    });
  }

  async deleteConversation(conversation: any) {

    if (!confirm('Delete this conversation?')) return;

    await this.run('Deleting conversation', async () => {

      await this.api.deleteConversation(conversation.id);

      if (this.activeConversation?.id === conversation.id) {
        this.activeConversation = null;
        this.messages = [];
      }

      await this.refresh();
    });
  }

  async sendMessage() {

    const question = this.question.trim();

    if (!question || this.busy) return;

    if (!this.activeConversation) {

      this.notify('Create or open a conversation first.', 'error');
      return;
    }

    await this.run('AI is analyzing your documents', async () => {

      this.question = '';

      const userMessage = {
        role: 'user',
        content: question,
        sources: []
      };

      const assistantMessage: any = {
        role: 'assistant',
        content: '',
        sources: []
      };

      this.messages.push(userMessage, assistantMessage);

      try {

        await this.api.streamChat(
          this.activeConversation.id,
          question,
          event => {

            if (event.type === 'sources') {
              assistantMessage.sources = event.sources;
            }

            if (event.type === 'token') {
              assistantMessage.content += event.content;
            }

            if (event.type === 'done') {
              Object.assign(assistantMessage, event.message);
            }

            this.cdr.detectChanges();
            this.scrollChat();
          }
        );

      } catch (error) {

        assistantMessage.content += '\n\n[Response interrupted]';

        this.question = question;
        throw error;
      }

      await this.refresh();
    });
  }

  scrollChat() {

    const element = document.getElementById('chat-scroll');

    if (element) {
      element.scrollTop = element.scrollHeight;
    }
  }

  async generateSummary() {

    if (!this.selected.length) {
      this.notify('Select documents to summarize.', 'error');
      return;
    }

    await this.run('Generating document summary', async () => {

      const result = await this.api.generateSummary(
        this.selected,
        this.summaryType,
        this.forceRefresh
      );

      this.activeSummary = result.summary;

      await this.refresh();

      this.notify(
        result.cached
          ? 'Loaded summary from cache.'
          : 'Summary generated successfully.'
      );
    });
  }

  async deleteSummary(summary: any) {

    if (!confirm('Delete this summary?')) return;

    await this.run('Deleting summary', async () => {

      await this.api.deleteSummary(summary.id);

      if (this.activeSummary?.id === summary.id) {
        this.activeSummary = null;
      }

      await this.refresh();
    });
  }

  editNote(note: any) {

    this.editingNote = note;

    this.noteForm = {
      title: note.title,
      content: note.content,
      category: note.category,
      tags: note.tags.join(', ')
    };
  }

  clearNote() {

    this.editingNote = null;

    this.noteForm = {
      title: '',
      content: '',
      category: 'General',
      tags: ''
    };
  }

  async saveNote() {

    if (!this.noteForm.title.trim() || !this.noteForm.content.trim()) {

      this.notify('Enter a note title and content.', 'error');
      return;
    }

    await this.run('Saving note', async () => {

      const payload = {
        title: this.noteForm.title,
        content: this.noteForm.content,
        category: this.noteForm.category || 'General',
        tags: this.noteForm.tags
          .split(',')
          .map(tag => tag.trim())
          .filter(Boolean)
      };

      if (this.editingNote) {
        await this.api.updateNote(this.editingNote.id, payload);
      } else {
        await this.api.createNote({
          ...payload,
          document_ids: this.selected
        });
      }

      this.clearNote();

      await this.refresh();

      this.notify('Note saved successfully.');
    });
  }

  async generateNote() {

    if (!this.selected.length) {
      this.notify('Select documents for AI notes.', 'error');
      return;
    }

    await this.run('Generating structured AI notes', async () => {

      const note = await this.api.generateNote(
        this.selected,
        this.noteForm.title || 'AI Generated Notes'
      );

      await this.refresh();

      this.editNote(note);

      this.notify('AI notes generated.');
    });
  }

  async deleteNote(note: any) {

    if (!confirm('Delete this note?')) return;

    await this.run('Deleting note', async () => {

      await this.api.deleteNote(note.id);

      if (this.editingNote?.id === note.id) {
        this.clearNote();
      }

      await this.refresh();
    });
  }
}