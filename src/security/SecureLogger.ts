export class SecureLogger {
  constructor(context: string) {}
  info(data: any, message: string) { console.log(`INFO [${message}]`, data); }
  error(data: any, message: string) { console.error(`ERROR [${message}]`, data); }
}
