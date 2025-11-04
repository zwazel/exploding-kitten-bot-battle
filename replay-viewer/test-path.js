// Test if __dirname works
import * as path from 'path';
import { fileURLToPath } from 'url';

console.log("Testing path resolution...");
console.log("typeof __dirname:", typeof __dirname);

// This won't work in ES modules
try {
  const badPath = path.join(__dirname, 'fixtures', 'test_replay.json');
  console.log("Bad path (using __dirname):", badPath);
} catch (e) {
  console.log("Error with __dirname:", e.message);
}

// This is the correct way in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const goodPath = path.join(__dirname, 'fixtures', 'test_replay.json');
console.log("Good path (using import.meta.url):", goodPath);
