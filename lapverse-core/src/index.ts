import './otel';
import { Config } from './config/Config';
import { TheLapVerseCore } from './TheLapVerseCore';

// Load configuration and start the server
Config.load();
const server = new TheLapVerseCore();
server.start().catch(error => {
    console.error('Failed to start server:', error);
    process.exit(1);
});