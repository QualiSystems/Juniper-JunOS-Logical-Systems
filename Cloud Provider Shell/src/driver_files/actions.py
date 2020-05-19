import re

from cloudshell.cli.command_template.command_template_executor import CommandTemplateExecutor
import driver_files.command_templates as command_template


class LogicalSystemsActions(object):
    def __init__(self, cli_service, logger):
        """LS Actions.

        :param cli_service: config mode cli_service
        :type cli_service: CliService
        :param logger:
        :type logger: Logger
        :return:
        """
        self._cli_service = cli_service
        self._logger = logger

    def create_ls(self, ls_name, interfaces):
        executor = CommandTemplateExecutor(
            self._cli_service, command_template.CREATE_LS)
        output = ""
        for int_name in interfaces:
            output += executor.execute_command(ls_name=ls_name, int_name=int_name)
        return output

    def remove_ls(self, ls_name):
        return CommandTemplateExecutor(
            self._cli_service, command_template.REMOVE_LS).execute_command(ls_name=ls_name)

    def get_int_list(self):
        output = CommandTemplateExecutor(
            self._cli_service, command_template.SHOW_ALL_INTERFACES).execute_command()
        return self._parse_interfaces(output)

    def get_ls_names(self):
        output = CommandTemplateExecutor(
            self._cli_service, command_template.SHOW_LS).execute_command()
        return output

    def get_conf_int_list(self):
        output = CommandTemplateExecutor(
            self._cli_service, command_template.SHOW_INTERFACES).execute_command()
        return self._parse_interfaces(output)

    def get_ls_int_list(self):
        output = self.get_ls_names()
        return self._parse_interfaces(output)

    @staticmethod
    def _parse_interfaces(data):
        interfaces = set()
        for line in data.splitlines():
            match = re.search(r"(ge-\d+/\d+/\d+|xe-\d+/\d+/\d+)", line)
            if match:
                interfaces.add(match.group(1))
        return interfaces
