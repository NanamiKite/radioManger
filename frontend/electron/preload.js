const { contextBridge, ipcMain } = require('electron')

contextBridge.exposeInMainWorld('electron', {
  // 可以在这里定义IPC通信接口
})

// IPC事件监听
