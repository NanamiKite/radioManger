import { cpSync, existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

const source = fileURLToPath(new URL('../resources/android/', import.meta.url))
const destination = fileURLToPath(new URL('../android/app/src/main/res/', import.meta.url))

if (!existsSync(destination)) {
  throw new Error('Android project not found. Run npx cap add android first.')
}

cpSync(source, destination, { recursive: true })
console.log('Copied RadioManager launcher and adaptive icons to the Android project.')
