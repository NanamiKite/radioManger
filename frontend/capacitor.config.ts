import { CapacitorConfig } from '@capacitor/cli'

const config: CapacitorConfig = {
  appId: 'com.radiomanager.app',
  appName: 'RadioManager',
  webDir: 'dist',
  server: {
    androidScheme: 'http',
    cleartext: true,
    allowNavigation: [
      '*'
    ]
  },
  android: {
    buildOptions: {
      keystorePath: undefined,
      releaseType: 'AAB',
    }
  },
  plugins: {
    CapacitorHttp: {
      enabled: true,
    }
  }
}

export default config
