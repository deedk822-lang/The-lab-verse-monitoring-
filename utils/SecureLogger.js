class SecureLogger {
    info(message, data) {
        console.log(JSON.stringify({ level: 'info', message, ...data }));
    }

    warn(message, data) {
        console.warn(JSON.stringify({ level: 'warn', message, ...data }));
    }

    error(message, data) {
        console.error(JSON.stringify({ level: 'error', message, ...data }));
    }

    debug(message, data) {
        console.debug(JSON.stringify({ level: 'debug', message, ...data }));
    }
}

module.exports = { SecureLogger };
