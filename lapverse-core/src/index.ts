<<<<<<< HEAD
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
=======
import { TheLapVerseCore } from './TheLapVerseCore';

const port = Number(process.env.PORT || 3000);
new TheLapVerseCore().start(port);
>>>>>>> origin/feat/ai-connectivity-layer
