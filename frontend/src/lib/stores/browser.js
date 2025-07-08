export const browserStore = {
  currentUrl: '',
  currentTitle: '',
  canGoBack: false,
  canGoForward: false,
  isLoading: false,
  history: [],
  async navigateTo(url) {
    this.currentUrl = url;
    this.currentTitle = url;
    this.history.push({ url, title: url });
  }
};
