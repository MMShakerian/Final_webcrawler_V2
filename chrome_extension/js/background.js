chrome.action.onClicked.addListener((tab) => {
  // باز کردن تب جدید با صفحه افزونه
  chrome.tabs.create({
    url: chrome.runtime.getURL('popup.html')
  });
}); 