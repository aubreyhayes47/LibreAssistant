export let messages = [];
export let isLoading = false;
export let currentSessionId = 'default';

export async function sendMessage(message) {
  messages.push({ role: 'user', content: message });
}
