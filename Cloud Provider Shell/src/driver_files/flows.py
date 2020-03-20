import os

from cloudshell.cli.session.session_exceptions import CommandExecutionException

from cloudshell.networking.juniper.cli.juniper_cli_configurator import JuniperCliConfigurator
from cloudshell.networking.juniper.command_actions.commit_rollback_actions import CommitRollbackActions
from driver_files.actions import LogicalSystemsActions
from driver_files.cli.command_modes import LSCommandMode, LSConfigCommandMode


class CreateRemoveLSFlow:
    def __init__(self, cli_configurator, logger):
        """Create Remove Logical Systems.

        :param logger: QsLogger object
        :param cloudshell.networking.juniper.cli.juniper_cli_configurator.JuniperCliConfigurator cli_configurator:
        """
        self._logger = logger
        self._cli_configurator = cli_configurator

    def create_ls(self, ls_name, int_list):
        with self._cli_configurator.enable_mode_service() as enable_session:
            sys_int_list = LogicalSystemsActions(enable_session, self._logger).get_int_list()

        with self._cli_configurator.config_mode_service() as config_session:
            ls_actions = LogicalSystemsActions(config_session, self._logger)
            commit_rollback = CommitRollbackActions(config_session, self._logger)

            config_int_list = ls_actions.get_conf_int_list()
            ls_int_list = ls_actions.get_ls_int_list()
            used_int_list = ls_int_list | config_int_list
            avail_int_list = sorted(sys_int_list - used_int_list - {i for i in int_list if i}, reverse=True)

            if len([i for i in int_list if not i]) > len(avail_int_list):
                raise Exception("Not enough available interfaces")
            int_list = {i if i else avail_int_list.pop() for i in int_list}

            not_available_list = set(int_list) & used_int_list
            if not_available_list:
                raise Exception("Interfaces {}, cannot be used.".format(str(not_available_list)))

            if not int_list.issubset(sys_int_list):
                raise Exception("Interface names is not correct {}".format(int_list - sys_int_list))

            try:
                ls_actions.create_ls(ls_name, int_list)
                commit_rollback.commit()
                return list(int_list)
            except CommandExecutionException:
                commit_rollback.rollback()
                raise

    def remove_ls(self, ls_name):
        with self._cli_configurator.config_mode_service() as cli_service:
            ls_actions = LogicalSystemsActions(cli_service, self._logger)
            commit_rollback = CommitRollbackActions(cli_service, self._logger)
            try:
                ls_actions.remove_ls(ls_name)
                commit_rollback.commit()
            except CommandExecutionException:
                commit_rollback.rollback()
                raise

    def send_ls_command(self, ls_name, command):
        with self._cli_configurator.enable_mode_service() as enable_service:
            with enable_service.enter_mode(LSCommandMode(ls_name)) as enable_ls_service:
                return self._ls_send_command(enable_ls_service, command)

    def send_ls_config_command(self, ls_name, command):
        with self._cli_configurator.enable_mode_service() as enable_service:
            with enable_service.enter_mode(LSCommandMode(ls_name)) as enable_ls_service:
                with enable_ls_service.enter_mode(LSConfigCommandMode(ls_name)) as config_ls_service:
                    return self._ls_send_command(config_ls_service, command)

    def _ls_send_command(self, session, command, separator=";"):
        return os.linesep.join(map(lambda cmd: session.send_command(cmd, remove_command_from_output=False),
                                   command.strip(separator).split(separator)))
