// Baut die Desktop-Version: kopiert das Browser-Spiel nach desktop/app und packt es mit Electron.
//
//   npm install                         (einmalig, im Ordner desktop/)
//   npm run build:win                   -> dist/StreetsOfBerlin-win32-x64/StreetsOfBerlin.exe + ZIP
//   npm run build:linux                 -> dist/StreetsOfBerlin-linux-x64/StreetsOfBerlin
//   npm start                           -> direkt starten (Entwicklung)
//   --electron-zip-dir <ordner>         -> vorab geladenes Electron-ZIP verwenden (statt Download)
//
// Funktioniert unter Windows, Linux und macOS; die Windows-.exe laesst sich auch unter Linux bauen
// (Icon und Versionsinfo werden dann mit resedit gesetzt, ohne Wine).
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const WEB = path.join(HERE, '..', 'web');
const APP = path.join(HERE, 'app');
const DIST = path.join(HERE, 'dist');
const pkg = JSON.parse(fs.readFileSync(path.join(HERE, 'package.json'), 'utf8'));

const args = process.argv.slice(2);
const opt = (name, def) => { const i = args.indexOf('--' + name); return i >= 0 ? args[i + 1] : def; };
const platform = opt('platform', process.platform);
const arch = opt('arch', 'x64');
// Optional: Ordner mit bereits heruntergeladenem electron-vX-<platform>-<arch>.zip (z.B. hinter einem Proxy)
const electronZipDir = opt('electron-zip-dir', process.env.ELECTRON_ZIP_DIR);

// --- 1) Spiel-Dateien bereitstellen -----------------------------------------------------
function stage() {
  for (const f of ['index.html', 'style.css', 'js/bundle.js', 'assets/atlas.json', 'assets/anchors.json']) {
    if (!fs.existsSync(path.join(WEB, f))) throw new Error(`web/${f} fehlt – zuerst "python Tools/WebBuild/build_web.py" ausfuehren`);
  }
  fs.rmSync(APP, { recursive: true, force: true });
  fs.mkdirSync(path.join(APP, 'js'), { recursive: true });
  fs.copyFileSync(path.join(WEB, 'index.html'), path.join(APP, 'index.html'));
  fs.copyFileSync(path.join(WEB, 'style.css'), path.join(APP, 'style.css'));
  fs.copyFileSync(path.join(WEB, 'js', 'bundle.js'), path.join(APP, 'js', 'bundle.js'));
  fs.cpSync(path.join(WEB, 'assets'), path.join(APP, 'assets'), { recursive: true });
  console.log('Spiel nach desktop/app kopiert');
}

// --- 2) Windows-Ressourcen (Icon, Versionsinfo) --------------------------------------------
async function patchExe(exePath) {
  const ResEdit = await import('resedit');
  const exe = ResEdit.NtExecutable.from(fs.readFileSync(exePath), { ignoreCert: true });
  const res = ResEdit.NtExecutableResource.from(exe);

  const ico = ResEdit.Data.IconFile.from(fs.readFileSync(path.join(HERE, 'icon.ico')));
  const groups = ResEdit.Resource.IconGroupEntry.fromEntries(res.entries);
  const target = groups.length ? groups[0] : { id: 1, lang: 1033 };
  ResEdit.Resource.IconGroupEntry.replaceIconsForResource(res.entries, target.id, target.lang, ico.icons.map((i) => i.data));

  const [a, b, c] = pkg.version.split('.').map(Number);
  const vi = ResEdit.Resource.VersionInfo.fromEntries(res.entries)[0] || ResEdit.Resource.VersionInfo.createEmpty();
  vi.setFileVersion(a, b, c, 0, 1033);
  vi.setProductVersion(a, b, c, 0, 1033);
  vi.setStringValues({ lang: 1033, codepage: 1200 }, {
    ProductName: pkg.productName,
    FileDescription: pkg.productName,
    CompanyName: pkg.author,
    LegalCopyright: `© ${new Date().getFullYear()} ${pkg.author}`,
    OriginalFilename: 'StreetsOfBerlin.exe',
    InternalName: 'StreetsOfBerlin',
    FileVersion: pkg.version,
    ProductVersion: pkg.version,
  });
  vi.outputToResourceEntries(res.entries);
  res.outputResource(exe);
  fs.writeFileSync(exePath, Buffer.from(exe.generate()));
  console.log('Icon und Versionsinfo gesetzt');
}

function zipDir(dir, zipPath) {
  fs.rmSync(zipPath, { force: true });
  const name = path.basename(dir);
  if (process.platform === 'win32') {
    execFileSync('powershell', ['-NoProfile', '-Command', `Compress-Archive -Path '${dir}' -DestinationPath '${zipPath}'`], { stdio: 'inherit' });
  } else {
    execFileSync('zip', ['-qr9', zipPath, name], { cwd: path.dirname(dir), stdio: 'inherit' });
  }
  console.log(`ZIP: ${path.relative(HERE, zipPath)} (${(fs.statSync(zipPath).size / 1e6).toFixed(1)} MB)`);
}

// --- 3) Packen -----------------------------------------------------------------------
async function build() {
  const { packager } = await import('@electron/packager');
  const [out] = await packager({
    dir: HERE,
    out: DIST,
    platform,
    arch,
    name: 'StreetsOfBerlin',
    executableName: 'StreetsOfBerlin',
    appVersion: pkg.version,
    overwrite: true,
    electronZipDir: electronZipDir ? path.resolve(electronZipDir) : undefined,
    asar: true,
    prune: true,
    // Icon fuer Linux/macOS; unter Windows setzt patchExe das Icon (geht so auch ohne Wine)
    icon: platform === 'win32' ? undefined : path.join(HERE, 'icon.png'),
    ignore: [/^\/dist($|\/)/, /^\/node_modules($|\/)/, /^\/build\.mjs$/, /^\/smoke-test\.mjs$/, /^\/make_icon\.py$/, /^\/README\.md$/],
  });
  console.log('Gepackt:', path.relative(HERE, out));
  if (platform === 'win32') await patchExe(path.join(out, 'StreetsOfBerlin.exe'));
  // Kurze Anleitung ins Paket legen
  fs.writeFileSync(path.join(out, 'LIESMICH.txt'), [
    'Streets of Berlin',
    '',
    platform === 'win32' ? 'Start: StreetsOfBerlin.exe doppelklicken (den ganzen Ordner zusammen lassen).' : 'Start: ./StreetsOfBerlin',
    'Vollbild: F11 oder Alt+Enter (oder Optionen -> Vollbild).',
    'Steuerung: WASD/Pfeile, J Schlag, K/Leertaste Sprung, L Spezial, I Rueckschlag, Enter/Esc Pause.',
    'Alles laesst sich unter Optionen -> Steuerung anpassen umbelegen. Gamepads werden unterstuetzt.',
    '',
  ].join('\r\n'));
  zipDir(out, path.join(DIST, `StreetsOfBerlin-${platform === 'win32' ? 'win' : platform}-${arch}.zip`));
}

stage();
if (!args.includes('--stage-only')) await build();
