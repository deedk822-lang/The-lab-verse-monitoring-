import './otel.js';
import { Config } from './config/Config.js';
import { TheLapVerseCore } from './TheLapVerseCore.js';

// Load configuration and start the server
Config.load?.();
const port = Number(process.env.PORT || 3000);
const server = new TheLapVerseCore();
server.start(port).catch(error => {
    console.error('Failed to start server:', error);
    process.exit(1);
});
