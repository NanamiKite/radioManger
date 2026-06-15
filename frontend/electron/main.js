const { app, BrowserWindow, Menu, Tray, dialog } = require('electron')
const path = require('path')
const fs = require('fs')

// 部署模式：auto = 从环境变量读取 | local = 本地后端 | lan = 局域网 | cloud = 云服务器
const DEPLOY_MODE = process.env.RADIOMANAGER_MODE || 'auto'
const API_URL = process.env.RADIOMANAGER_API_URL || 'http://localhost:8000'

let mainWindow = null

function getModeName() {
  if (DEPLOY_MODE === 'local' || DEPLOY_MODE === 'auto') return 'Local'
  if (DEPLOY_MODE === 'lan') return 'LAN'
  if (DEPLOY_MODE === 'cloud') return 'Cloud'
  return 'Local'
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    title: `RadioManager [${getModeName()}]`,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    }
  })

  // 构建模式下加载本地文件
  const distPath = path.join(app.getAppPath(), 'dist/index.html')
  if (fs.existsSync(distPath)) {
    mainWindow.loadFile(distPath)
  } else {
    // 开发模式加载 Vite 开发服务器
    mainWindow.loadURL('http://localhost:5173')
    mainWindow.webContents.openDevTools()
  }

  mainWindow.on('closed', () => { mainWindow = null })
}

// 应用菜单
const menuTemplate = [
  {
    label: 'RadioManager',
    submenu: [
      { label: `Mode: ${getModeName()}`, enabled: false },
      { type: 'separator' },
      { role: 'quit' }
    ]
  },
  {
    label: 'View',
    submenu: [
      { role: 'reload' },
      { role: 'toggleDevTools' },
      { type: 'separator' },
      { role: 'zoomIn' },
      { role: 'zoomOut' },
      { type: 'separator' },
      { role: 'togglefullscreen' }
    ]
  }
]

app.on('ready', () => {
  const menu = Menu.buildFromTemplate(menuTemplate)
  Menu.setApplicationMenu(menu)
  createWindow()
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow()
})
