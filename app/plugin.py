class Plugin(object):
    log_prefix = None
    logger = None

    def set_logger(self, logger, prefix=None):
        self.log_prefix = prefix
        self.logger = logger

    def log(self, text, color='black'):
        if self.logger is not None:
            self.logger.log(text, color=color, prefix=self.log_prefix)
