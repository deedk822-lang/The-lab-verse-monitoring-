import './otel';
import { Config } from './config/Config';
import { TheLapVerseCore } from './TheLapVerseCore';

// Load configuration and start the server
Config.load();
const port = Number(process.env.PORT || 3000);
new TheLapVerseCore().start(port).catch((error) => {
  console.error('Failed to start server:', error);
  process.exit(1);
});
