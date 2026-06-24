import { CapacitorConfig } from '@capacitor/cli'

const config: CapacitorConfig = {
  appId: 'com.radiomanager.app',
  appName: 'RadioManager',
  webDir: 'dist',
  server: {
    androidScheme: 'https',
    cleartext: false,
    allowNavigation: [
      'localhost',
      '127.0.0.1',
      '10.0.2.2',
      '*.radiomanager.local',
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
