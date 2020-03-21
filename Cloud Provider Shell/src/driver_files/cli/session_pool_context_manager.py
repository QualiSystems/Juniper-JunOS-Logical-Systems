from cloudshell.cli.service.session_pool_context_manager import SessionPoolContextManager

from driver_files.cli.command_modes import LSCommandMode, LSConfigCommandMode


class ReturnEnableSessionPoolContextManager(SessionPoolContextManager):
    def __init__(self, session_pool, defined_sessions, command_mode, enable_mode, logger):
        super(ReturnEnableSessionPoolContextManager, self).__init__(session_pool, defined_sessions, command_mode,
                                                                    logger)
        self._enable_mode = enable_mode
        self.cli_service = None

    def __enter__(self):
        self.cli_service = super(ReturnEnableSessionPoolContextManager, self).__enter__()
        return self.cli_service

    def __exit__(self, exc_type, exc_val, exc_tb):
        if isinstance(self.cli_service.command_mode, (LSCommandMode, LSConfigCommandMode)):
            self.cli_service._change_mode(self._enable_mode)
        return super(ReturnEnableSessionPoolContextManager, self).__exit__(exc_type, exc_val, exc_tb)
