import logging

from cloudshell.cli.service.session_pool_manager import SessionPoolManager

from driver_files.cli.session_pool_context_manager import ReturnEnableSessionPoolContextManager


class BackToEnableCLI(object):
    def __init__(self, session_pool=SessionPoolManager()):
        self._session_pool = session_pool

    def get_session(self, defined_sessions, command_mode, enable_mode, logger=None):
        """Get session from the pool or create new.

        :param collections.Iterable defined_sessions:
        :param cloudshell.cli.command_mode.CommandMode command_mode:
        :param logging.Logger logger:
        :rtype: cloudshell.cli.service.session_pool_context_manager.SessionPoolContextManager  # noqa: E501
        """
        if not isinstance(defined_sessions, list):
            defined_sessions = [defined_sessions]

        if not logger:
            logger = logging.getLogger("cloudshell_cli")
        return ReturnEnableSessionPoolContextManager(
            self._session_pool, defined_sessions, command_mode, enable_mode, logger
        )
