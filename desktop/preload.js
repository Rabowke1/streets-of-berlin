// Schmale Bruecke zwischen Spiel und Fenster: Beenden und Vollbild (kein Node-Zugriff fuer die Seite).
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('sobDesktop', {
  quit: () => ipcRenderer.send('sob:quit'),
  setFullscreen: (on) => ipcRenderer.send('sob:set-fullscreen', !!on),
  toggleFullscreen: () => ipcRenderer.send('sob:toggle-fullscreen'),
  onFullscreen: (callback) => ipcRenderer.on('sob:fullscreen-changed', (_event, on) => callback(!!on)),
});
