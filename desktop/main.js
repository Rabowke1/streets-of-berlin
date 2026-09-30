// Streets of Berlin als Desktop-Anwendung (Electron): laedt das Browser-Spiel aus ./app ueber das
// eigene Protokoll app://game/ (damit fetch/Audio wie auf einem Webserver funktionieren).
const { app, BrowserWindow, Menu, ipcMain, net, protocol } = require('electron');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

const ROOT = path.join(__dirname, 'app');

protocol.registerSchemesAsPrivileged([
  { scheme: 'app', privileges: { standard: true, secure: true, supportFetchAPI: true, stream: true } },
]);
// Musik darf ohne vorherigen Klick starten
app.commandLine.appendSwitch('autoplay-policy', 'no-user-gesture-required');
Menu.setApplicationMenu(null);

// Fuer Tests: --sob-query="?autoplay&god" wird an die Spiel-URL gehaengt
const queryArg = process.argv.find((a) => a.startsWith('--sob-query='));
const query = queryArg ? queryArg.slice('--sob-query='.length) : '';

let win = null;

function notifyFullscreen() {
  if (win && !win.isDestroyed()) win.webContents.send('sob:fullscreen-changed', win.isFullScreen());
}
function setFullscreen(on) {
  if (!win) return;
  win.setFullScreen(on);
  notifyFullscreen();
  setTimeout(notifyFullscreen, 300);
}

function createWindow() {
  win = new BrowserWindow({
    width: 1280,
    height: 720,
    minWidth: 800,
    minHeight: 450,
    useContentSize: true,
    show: false,
    title: 'Streets of Berlin',
    backgroundColor: '#09070f',
    icon: path.join(__dirname, 'icon.png'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      sandbox: true,
      nodeIntegration: false,
      backgroundThrottling: false,
    },
  });
  win.once('ready-to-show', () => win.show());

  // F11 und Alt+Enter schalten Vollbild um
  win.webContents.on('before-input-event', (event, input) => {
    if (input.type !== 'keyDown') return;
    if (input.key === 'F11' || (input.alt && input.key === 'Enter')) {
      setFullscreen(!win.isFullScreen());
      event.preventDefault();
    }
  });
  // Vollbild-Zustand an die Seite melden. Unter Windows kommen enter/leave-full-screen nicht verlaesslich an,
  // deshalb zusaetzlich nach jeder Groessenaenderung und direkt nach dem Umschalten.
  win.on('enter-full-screen', notifyFullscreen);
  win.on('leave-full-screen', notifyFullscreen);
  win.on('resize', notifyFullscreen);

  // Keine fremden Seiten oder Popups
  win.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  win.webContents.on('will-navigate', (event, url) => { if (!url.startsWith('app://game/')) event.preventDefault(); });

  win.loadURL('app://game/index.html' + query);
}

if (!app.requestSingleInstanceLock()) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (win) { if (win.isMinimized()) win.restore(); win.focus(); }
  });

  app.whenReady().then(() => {
    protocol.handle('app', (request) => {
      const { pathname } = new URL(request.url);
      const file = path.normalize(path.join(ROOT, decodeURIComponent(pathname)));
      if (!file.startsWith(ROOT + path.sep)) return new Response('Nicht gefunden', { status: 404 });
      return net.fetch(pathToFileURL(file).toString());
    });

    ipcMain.on('sob:quit', () => app.quit());
    ipcMain.on('sob:set-fullscreen', (_event, on) => setFullscreen(!!on));
    // Umschalten entscheidet das Fenster selbst: der Zustand in der Seite kommt unter Windows verzoegert an
    ipcMain.on('sob:toggle-fullscreen', () => { if (win) setFullscreen(!win.isFullScreen()); });

    createWindow();
  });

  app.on('window-all-closed', () => app.quit());
}
