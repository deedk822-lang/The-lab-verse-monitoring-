export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
}

export class Logger {
  private level: LogLevel = LogLevel.INFO;

  constructor() {
    this.level = LogLevel[process.env.LOG_LEVEL?.toUpperCase() as keyof typeof LogLevel] || LogLevel.INFO;
  }

  private log(level: LogLevel, message: string, meta?: any): void {
    if (level < this.level) return;

    const timestamp = new Date().toISOString();
    const levelStr = LogLevel[level];
    const metaStr = meta ? ` ${JSON.stringify(meta)}` : '';

    console.log(`[${timestamp}] [${levelStr}] ${message}${metaStr}`);
  }

  debug(message: string, meta?: any): void {
    this.log(LogLevel.DEBUG, message, meta);
  }

  info(message: string, meta?: any): void {
    this.log(LogLevel.INFO, message, meta);
  }

  warn(message: string, meta?: any): void {
    this.log(LogLevel.WARN, message, meta);
  }

  error(message: string, meta?: any): void {
    this.log(LogLevel.ERROR, message, meta);
  }
}

export const logger = new Logger();