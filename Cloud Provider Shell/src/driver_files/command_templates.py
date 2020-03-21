from cloudshell.cli.command_template.command_template import CommandTemplate

from cloudshell.networking.juniper.command_templates.generic_action_error_map import (
    ACTION_MAP,
    ERROR_MAP,
)

CREATE_LS = CommandTemplate(
    "set logical-systems {ls_name} interfaces {int_name} unit 0",
    action_map=ACTION_MAP,
    error_map=ERROR_MAP,
)

REMOVE_LS = CommandTemplate(
    "delete logical-systems {ls_name}",
    action_map=ACTION_MAP,
    error_map=ERROR_MAP,
)

SHOW_INTERFACES = CommandTemplate(
    "show interfaces",
    action_map=ACTION_MAP,
    error_map=ERROR_MAP,
)

SHOW_ALL_INTERFACES = CommandTemplate(
    "show interfaces terse",
    action_map=ACTION_MAP,
    error_map=ERROR_MAP,
)

SHOW_LS = CommandTemplate(
    "show logical-systems",
    action_map=ACTION_MAP,
    error_map=ERROR_MAP,
)
