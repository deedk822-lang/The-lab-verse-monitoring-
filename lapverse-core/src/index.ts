import { TheLapVerseCore } from './TheLapVerseCore';

const port = Number(process.env.PORT || 3000);
new TheLapVerseCore().start(port);
