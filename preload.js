const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('april', {
  sendMessage: (text) => ipcRenderer.invoke('send-message', text),
  onReply: (callback) => {
    ipcRenderer.on('reply', (event, data) => callback(data))
  },
  close: () => ipcRenderer.send('window-close'),
  minimize: () => ipcRenderer.send('window-minimize'),
  toggleAlwaysOnTop: (enable) => ipcRenderer.send('window-always-on-top', enable)
})