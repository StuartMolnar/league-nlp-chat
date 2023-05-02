const winston = require('winston');
const { format } = require('logform');
const fs = require('fs');

// Create the log directory if it doesn't exist
const logDir = 'logs';
if (!fs.existsSync(logDir)) {
  fs.mkdirSync(logDir);
}

// Create a transport for writing to the file
const transport = new winston.transports.File({
  filename: `app.log`,
  format: format.printf(info => {
    return `${info.timestamp} - ${info.level.toUpperCase()} - ${info.message}`;
  }),
  maxsize: 1048576, // max size of 1MB
  maxFiles: 5, // max 5 log files
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
    transport,
  ],
});

module.exports = logger;
