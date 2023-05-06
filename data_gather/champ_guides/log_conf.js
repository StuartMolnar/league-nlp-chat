const winston = require('winston');
const { format } = require('logform');

// Create a transport for writing to the file
const fileTransport = new winston.transports.File({
  filename: `app.log`,
  format: format.printf(info => {
    return `${info.timestamp} - ${info.level.toUpperCase()} - ${info.message}`;
  }),
  maxsize: 1048576, // max size of 1MB
});

// Create a transport for logging to the console
const consoleTransport = new winston.transports.Console({
  format: format.printf(info => {
    return `${info.timestamp} - ${info.level.toUpperCase()} - ${info.message}`;
  }),
});

// Create a logger instance
const logger = winston.createLogger({
  level: 'info',
  format: format.combine(
    format.timestamp({
      format: 'YYYY-MM-DD HH:mm:ss.SSS',
    }),
    format.errors({ stack: true }),
    format.splat(),
    format.json(),
  ),
  transports: [
    fileTransport,
    consoleTransport, // Add the console transport
  ],
});

module.exports = logger;
