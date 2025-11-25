import { setupServer } from 'msw/node';
import { Console } from 'console';

global.console = new Console(process.stdout, process.stderr);
