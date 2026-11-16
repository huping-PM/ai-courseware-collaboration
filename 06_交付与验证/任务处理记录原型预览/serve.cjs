const http = require('http');
const fs = require('fs');
const path = require('path');
const root = path.resolve(__dirname, '../..');
const mime = {'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.md':'text/plain; charset=utf-8','.png':'image/png','.svg':'image/svg+xml'};
function createServer() {
  return http.createServer((req,res) => {
    let file;
    try { file = path.resolve(root, '.' + decodeURIComponent(new URL(req.url,'http://localhost').pathname)); }
    catch { res.writeHead(400).end(); return; }
    if (file !== root && !file.startsWith(root + path.sep)) { res.writeHead(403).end(); return; }
    if (!fs.existsSync(file) || !fs.statSync(file).isFile()) { res.writeHead(404).end(); return; }
    res.setHeader('Content-Type',mime[path.extname(file)] || 'application/octet-stream');
    res.setHeader('Cache-Control','no-store');
    fs.createReadStream(file).pipe(res);
  });
}
module.exports = {createServer,root};
if (require.main === module) createServer().listen(8821,'127.0.0.1',() => console.log('Local preview ready: http://127.0.0.1:8821'));
