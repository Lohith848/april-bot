const { app, BrowserWindow, ipcMain } = require('electron')
const path = require('path')
const { spawn } = require('child_process')

let win
let python

function createWindow() {
  win = new BrowserWindow({
    width: 400,
    height: 650,
    frame: false,
    resizable: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js')
    }
  })

  win.loadFile('index.html')

  // Window controls
  ipcMain.on('window-close', () => win.hide())
  ipcMain.on('window-minimize', () => win.minimize())
  ipcMain.on('window-always-on-top', (event, enable) => {
    win.setAlwaysOnTop(enable)
  })

  // Start Python bot
  python = spawn('python', [path.join(__dirname, 'python', 'bot.py')], {
    stdio: ['pipe', 'pipe', 'pipe']
  })

  python.stdout.on('data', (data) => {
    const msg = data.toString().trim()
    if (msg && win) {
      win.webContents.send('reply', { text: msg })
    }
  })

  python.stderr.on('data', (data) => {
    console.error('Bot error:', data.toString())
  })

  python.on('close', (code) => {
    console.log('Bot exited with code:', code)
  })
}

app.whenReady().then(() => {
  createWindow()
})

app.on('window-all-closed', () => {
  if (python) {
    python.kill()
  }
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// Handle send message from renderer
ipcMain.handle('send-message', async (event, text) => {
  if (python && python.stdin) {
    python.stdin.write(text + '\n')
    return true
  }
  return false
})