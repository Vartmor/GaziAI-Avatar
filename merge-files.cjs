const fs = require('fs');
const path = require('path');

const outputFile = 'all_files_content.txt';
const rootDir = __dirname; // Çalıştırdığın dizin

const allowedExtensions = [
  '.js', '.jsx', '.json', '.md', '.html', '.css', '.txt', '.cjs', '.mjs', '.py','.env','.gitignore'
];

// Hariç tutulacak klasörler
const ignoredDirs = new Set(['node_modules', '__pycache__', '.git', '.idea', '.venv']);

// Hariç tutulacak dosya uzantıları
const ignoredFileExtensions = new Set(['.pyc']);

function isTextFile(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  if (ignoredFileExtensions.has(ext)) return false;
  return allowedExtensions.includes(ext);
}

function readAllFiles(dir, fileList = []) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const entryPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (ignoredDirs.has(entry.name)) continue; // İstenmeyen klasörleri atla
      readAllFiles(entryPath, fileList);
    } else if (entry.isFile()) {
      fileList.push(entryPath);
    }
  }
  return fileList;
}

function main() {
  const allFiles = readAllFiles(rootDir);
  let output = '';
  for (const file of allFiles) {
    if (file === path.join(rootDir, outputFile)) continue; // Çıktı dosyasını atla
    if (!isTextFile(file)) continue; // Sadece metin dosyalarını ekle
    const content = fs.readFileSync(file, 'utf8');
    if (content.includes('node_modules')) continue; // İçeriğinde node_modules geçenleri atla
    output += `--- ${file} ---\n${content}\n\n`;
  }
  fs.writeFileSync(outputFile, output, 'utf8');
  fs.chmodSync(outputFile, 0o666); // Dosyayı herkes için yazılabilir yap
  console.log('Sadece metin dosyaları toplandı:', outputFile);
}

main();