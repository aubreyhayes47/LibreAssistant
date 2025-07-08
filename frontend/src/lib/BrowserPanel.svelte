<script>
  import { invoke } from '@tauri-apps/api/core';
  let url = $state('https://example.com');
  let iframeSrc = $state('https://example.com');
  let summary = $state('');
  let isLoading = $state(false);

  async function navigate() {
    if (!url.trim()) return;
    iframeSrc = url.startsWith('http') ? url : `https://${url}`;
    isLoading = true;
    try {
      await invoke('add_history_entry', { url: iframeSrc, title: iframeSrc });
    } catch (e) {
      console.error('History entry error', e);
    } finally {
      isLoading = false;
    }
  }

  async function summarize() {
    isLoading = true;
    try {
      const resp = await invoke('summarize_page', { url: iframeSrc });
      if (resp.success) {
        summary = resp.summary;
      } else {
        summary = `Error: ${resp.error}`;
      }
    } catch (e) {
      summary = `Error: ${e}`;
    } finally {
      isLoading = false;
    }
  }
</script>

<div class="browser-panel">
  <div class="controls">
    <input bind:value={url} placeholder="Enter URL" />
    <button onclick={navigate} disabled={isLoading}>Go</button>
    <button onclick={summarize} disabled={isLoading}>Summarize</button>
  </div>
  <iframe class="webview" src={iframeSrc} title="browser preview"></iframe>
  {#if summary}
    <div class="summary">
      <h3>Page Summary</h3>
      <pre>{summary}</pre>
    </div>
  {/if}
</div>

<style>
.browser-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.controls {
  display: flex;
  gap: 10px;
}
.webview {
  width: 100%;
  height: 400px;
  border: 1px solid #ccc;
  border-radius: 8px;
}
.summary {
  background: #f8f9fa;
  padding: 10px;
  border: 1px solid #e9ecef;
  border-radius: 8px;
}
.summary pre {
  white-space: pre-wrap;
}
</style>
