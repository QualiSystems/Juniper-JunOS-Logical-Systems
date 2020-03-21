from cloudshell.networking.juniper.cli.juniper_cli_configurator import JuniperCliConfigurator
from driver_files.cli.cli import BackToEnableCLI
from driver_files.cli.command_modes import LSCommandMode, LSConfigCommandMode


class LSConfigurator(JuniperCliConfigurator):

    def __init__(self, ls_name, session_pool, resource_config, logger):
        super().__init__(BackToEnableCLI(session_pool), resource_config, logger)
        self.ls_name = ls_name
        self.ls_modes = self._init_ls_modes(ls_name)

    def _init_ls_modes(self, ls_name):
        ls_enable_mode = LSCommandMode(ls_name)
        ls_enable_mode.add_parent_mode(super(LSConfigurator, self).enable_mode)
        ls_config_mode = LSConfigCommandMode(ls_name)
        ls_config_mode.add_parent_mode(ls_enable_mode)
        return {LSCommandMode: ls_enable_mode, LSConfigCommandMode: ls_config_mode}

    @property
    def enable_mode(self):
        return self.ls_modes.get(LSCommandMode)

    @property
    def config_mode(self):
        return self.ls_modes.get(LSConfigCommandMode)

    def get_cli_service(self, command_mode):
        """Use cli.get_session to open CLI connection and switch into required mode.

        :param CommandMode command_mode: operation mode, can be
            default_mode/enable_mode/config_mode/etc.
        :return: created session in provided mode
        :rtype: cloudshell.cli.service.session_pool_context_manager.SessionPoolContextManager  # noqa: E501
        """
        return self._cli.get_session(
            self._defined_sessions(), command_mode, super(LSConfigurator, self).enable_mode, self._logger)
