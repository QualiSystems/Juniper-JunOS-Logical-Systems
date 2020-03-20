from collections import OrderedDict

from cloudshell.cli.service.command_mode import CommandMode


class LSCommandMode(CommandMode):
    PROMPT_TEMPLATE = r":{ls_name}>\s*$"
    ENTER_COMMAND_TEMPLATE = "set cli logical-system {ls_name}"
    EXIT_COMMAND = "clear cli logical-system"

    def __init__(self, ls_name):
        self.ls_name = ls_name
        CommandMode.__init__(
            self,
            self.PROMPT_TEMPLATE.format(ls_name=ls_name),
            self.ENTER_COMMAND_TEMPLATE.format(ls_name=ls_name),
            self.EXIT_COMMAND,
            enter_action_map=self.enter_action_map(),
            exit_action_map=self.exit_action_map(),
            enter_error_map=self.enter_error_map(),
            exit_error_map=self.exit_error_map(),
            use_exact_prompt=True,
        )

    def enter_action_map(self):
        return OrderedDict()

    def enter_error_map(self):
        return OrderedDict([(r"[Ee]rror:", "Command error")])

    def exit_action_map(self):
        return OrderedDict()

    def exit_error_map(self):
        return OrderedDict([(r"[Ee]rror:", "Command error")])


class LSConfigCommandMode(CommandMode):
    PROMPT_TEMPLATE = r"(\[edit\]\s*.+:{ls_name}#)\s*$"
    ENTER_COMMAND = "configure"
    EXIT_COMMAND = "exit"

    def __init__(self, ls_name):
        CommandMode.__init__(
            self,
            self.PROMPT_TEMPLATE.format(ls_name=ls_name),
            self.ENTER_COMMAND,
            self.EXIT_COMMAND,
            enter_action_map=self.enter_action_map(),
            exit_action_map=self.exit_action_map(),
            enter_error_map=self.enter_error_map(),
            exit_error_map=self.exit_error_map(),
            use_exact_prompt=True,
        )

    def enter_action_map(self):
        return OrderedDict()

    def enter_error_map(self):
        return OrderedDict([(r"[Ee]rror:", "Command error")])

    def exit_action_map(self):
        return OrderedDict()

    def exit_error_map(self):
        return OrderedDict([(r"[Ee]rror:", "Command error")])
