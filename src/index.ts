import { TheLapVerseCore } from './TheLapVerseCore';

async function bootstrap() {
  const core = new TheLapVerseCore();
  await core.start();
}

bootstrap();

