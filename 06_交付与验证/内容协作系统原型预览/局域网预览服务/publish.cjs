const fs = require('fs'), path = require('path'), crypto = require('crypto'), vm = require('vm');
const root = __dirname, workspace = path.resolve(root, '../../..'), source = path.join(workspace, '04_原型与说明');
const args = process.argv.slice(2), currentPath = path.join(root, 'current.json');
function activate(data) {
  const temp = currentPath + '.tmp';
  fs.writeFileSync(temp, JSON.stringify(data, null, 2));
  fs.renameSync(temp, currentPath);
}
function checkRelease(name) {
  if (!/^release-\d+$/.test(name || '')) throw Error('Invalid release');
  const dir = path.join(root, 'releases', name);
  const manifest = JSON.parse(fs.readFileSync(path.join(dir, 'release-manifest.json')));
  for (const item of manifest.files) {
    const file = path.resolve(dir, item.path);
    if (!file.startsWith(dir + path.sep) || crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex') !== item.sha256) {
      throw Error('Release integrity failed: ' + item.path);
    }
  }
  return manifest;
}
if (args[0] === 'activate-existing') {
  const name = args[1];
  checkRelease(name);
  const previous = JSON.parse(fs.readFileSync(currentPath)).release;
  activate({ release: name, previous, publishedAt: new Date().toISOString() });
  console.log(JSON.stringify({ release: name, previous, activated: true }));
  process.exit(0);
}
if (args[0] === 'rollback') {
  const current = JSON.parse(fs.readFileSync(currentPath));
  if (!current.previous) throw Error('No previous release');
  checkRelease(current.previous);
  activate({ release: current.previous, previous: current.release, publishedAt: new Date().toISOString() });
  console.log('Rolled back to ' + current.previous);
  process.exit(0);
}
if (args[0] && args[0] !== 'build') throw Error('Unknown command: ' + args[0]);
require(path.join(source, 'shared/build-requirement-notes.cjs'));
const release = 'release-' + new Date().toISOString().replace(/[^0-9]/g, '');
const target = path.join(root, 'releases', release);
fs.mkdirSync(target, { recursive: true });
const files = [];
function add(relative, buffer) {
  const out = path.join(target, relative);
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, buffer);
  files.push({ path: relative.replace(/\\/g, '/'), sha256: crypto.createHash('sha256').update(buffer).digest('hex') });
}
const compat = `if(!crypto.randomUUID){crypto.randomUUID=function(){const b=crypto.getRandomValues(new Uint8Array(16));b[6]=(b[6]&15)|64;b[8]=(b[8]&63)|128;const h=Array.from(b,x=>x.toString(16).padStart(2,'0')).join('');return h.slice(0,8)+'-'+h.slice(8,12)+'-'+h.slice(12,16)+'-'+h.slice(16,20)+'-'+h.slice(20)}};`;
add('compat.js', Buffer.from(compat));
const runtimeDirs = ['AI协作工作台-风格探索', 'PG02-项目管理', 'PG07-资源管理',
  'PG11-内容协作智能体', 'PG13-智能体配置', 'PG14-系统管理', 'shared'];
const blockedDirs = new Set(['预览图', '入库预览图', '协作状态预览图', 'vendor', 'iteration-boards']);
const blockedFiles = new Set(['原型图索引.html', '协作状态原型图索引.html', 'review.html', 'review.js', 'review.css']);
const allowed = /\.(html|css|js|webm|mp4|wav|mp3|woff2|ico|png|jpe?g|svg)$/i;
function walk(dir, relative = '') {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.isSymbolicLink()) throw Error('Symlink not allowed');
    if (entry.isDirectory()) {
      if (!blockedDirs.has(entry.name)) walk(path.join(dir, entry.name), path.join(relative, entry.name));
    } else if (allowed.test(entry.name) && !blockedFiles.has(entry.name)) {
      const sourceRelative = path.join(relative, entry.name);
      let data = fs.readFileSync(path.join(dir, entry.name));
      if (entry.name.endsWith('.html')) data = Buffer.from(data.toString('utf8').replace(/<head([^>]*)>/i, '<head$1><script src="/compat.js"></script>'));
      add(path.join('04_原型与说明', sourceRelative), data);
      if (!relative.startsWith('AI协作工作台-风格探索')) add(path.join('页面', sourceRelative), data);
    }
  }
}
for (const directory of runtimeDirs) walk(path.join(source, directory), directory);
const workbench = path.join(workspace, '06_交付与验证/AI协作工作台UI风格方案/交互Demo.html');
add('06_交付与验证/AI协作工作台UI风格方案/交互Demo.html', fs.readFileSync(workbench));
add('原型预览.html', fs.readFileSync(path.join(root, '原型预览.html')));
for (const item of files) {
  const absolute = path.join(target, item.path);
  if (item.path.endsWith('.js')) new vm.Script(fs.readFileSync(absolute, 'utf8'), { filename: item.path });
  if (!item.path.endsWith('.html')) continue;
  const html = fs.readFileSync(absolute, 'utf8');
  for (const match of html.matchAll(/(?:src|href)=["']([^"']+)["']/g)) {
    const ref = match[1];
    if (/^(?:https?:|data:|blob:|#|javascript:|mailto:|\{)/i.test(ref)) continue;
    const name = decodeURIComponent(ref.split(/[?#]/)[0]);
    if (!name) continue;
    const resolved = name.startsWith('/') ? path.join(target, name.slice(1)) : path.resolve(path.dirname(absolute), name);
    if (!resolved.startsWith(target + path.sep) || !fs.existsSync(resolved)) throw Error('Missing or out-of-root dependency: ' + item.path + ' -> ' + ref);
  }
}
fs.writeFileSync(path.join(target, 'release-manifest.json'), JSON.stringify({ release, created: new Date().toISOString(), files }, null, 2));
console.log(JSON.stringify({ release, files: files.length, activated: false }));
