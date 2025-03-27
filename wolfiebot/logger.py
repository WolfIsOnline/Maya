import logging


class _LogColors:
    """Color codes for formatting log messages."""

    WHITE = "\033[97m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BRIGHT_RED = "\033[91m"
    DARK_RED = "\033[31m"
    RESET = "\033[0m"


class Level:
    """Enumeration of log levels."""

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class _ColoredFormatter(logging.Formatter):
    COLOR_MAP = {
        Level.DEBUG: _LogColors.WHITE,
        Level.INFO: _LogColors.GREEN,
        Level.WARNING: _LogColors.YELLOW,
        Level.ERROR: _LogColors.BRIGHT_RED,
        Level.CRITICAL: _LogColors.DARK_RED,
    }

    def __init__(self, fmt):
        """Initialize the _ColoredFormatter class.

        Args:
            fmt (str): The log message format string.
        """
        super().__init__(fmt=fmt, datefmt="%m/%d/%Y %I:%M:%S %p")

    def format(self, record):
        """Format the log record with colors.
        This overrides the default Formatter.format() method to add colors
        based on the log level. The color map is defined in COLOR_MAP.

        Args:
            record: The log record to format.

        Returns:
            The formatted log message string with colors.
        """
        color = self.COLOR_MAP.get(record.levelno, _LogColors.WHITE)
        message = super().format(record)
        return f"{color}{message}{_LogColors.RESET}"


class Logger:
    _loggers = {}

    @classmethod
    def get_instance(
        cls, name: str, level: Level = Level.INFO, handler: logging.Handler = None
    ):
        """Get an instance of the Logger class.

        This implements a singleton pattern to ensure only one Logger instance exists
        per name. The first call with a given name will create the instance, subsequent
        calls will return the existing instance.

        Args:
          name: The name for the logger instance.
          level: The log level to set on the logger.
          handler: Optional log handler to attach to the logger.

        Returns:
          The Logger instance for the given name.
        """
        if name not in cls._loggers:
            cls._loggers[name] = cls(name, level, handler)
        return cls._loggers[name]

    def __init__(self, name: str, level: Level, handler: logging.Handler = None):
        """Initialize the Logger class.

        This initializes the Python logger with the given name, log level, and handler.
        It configures the handler formatter, attaches the handler to the logger,
        sets the log level on the logger and handler, and disables propagation
        to parent loggers.

        Args:
            name (str): The name for the logger. This is used to get the logger instance.
            level (Level): The log level to set on the logger and handler.
            handler (logging.Handler): Optional log handler. Defaults to StreamHandler.
        """
        self.log = logging.getLogger(name)
        self.handler = handler or logging.StreamHandler()
        self.formatter = _ColoredFormatter(
            "[%(levelname)s] - [%(asctime)s] - [%(name)s] - %(message)s"
        )
        self.handler.setFormatter(self.formatter)
        self.log.addHandler(self.handler)
        self.log.setLevel(level)
        self.handler.setLevel(level)
        self.log.propagate = False

    def debug(self, msg, *args, **kwargs):
        """Log a debug message.

        Logs a message with level DEBUG on the logger. The arguments are interpreted
        using str.format().

        Args:
            msg (str): The message to log.
            *args: Format args for the message.
            **kwargs: Keyword args for the message.
        """
        self.log.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """Log an info message.

        Logs a message with level INFO on the logger. The arguments are interpreted
        using str.format().

        Args:
            msg (str): The message to log.
            *args: Format args for the message.
            **kwargs: Keyword args for the message.
        """
        self.log.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """Log a warning message.

        Logs a message with level WARNING on the logger. The arguments are interpreted
        using str.format().

        Args:
            msg (str): The message to log.
            *args: Format args for the message.
            **kwargs: Keyword args for the message.
        """
        self.log.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """Log an error message.

        Logs a message with level ERROR on the logger. The arguments are interpreted
        using str.format().

        Args:
            msg (str): The message to log.
            *args: Format args for the message.
            **kwargs: Keyword args for the message.
        """
        self.log.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """Log a critical message.

        Logs a message with level CRITICAL on the logger. The arguments are interpreted
        using str.format().

        Args:
            msg (str): The message to log.
            *args: Format args for the message.
            **kwargs: Keyword args for the message.
        """
        self.log.critical(msg, *args, **kwargs)
