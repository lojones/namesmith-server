import logging

def setup_logger(name):
    logger = logging.getLogger(name)
    
    # Only setup handlers if they haven't been set up already
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # Create console handler
        console_handler = logging.StreamHandler()

        # Create formatter and add it to handler
        log_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(log_format)

        # Add handler to the logger
        logger.addHandler(console_handler)

    return logger 