#!/usr/bin/python
# -*- coding: utf-8 -*-

import cloudshell.shell.standards.attribute_names as attribute_names
from cloudshell.shell.standards.core.resource_config_entities import ResourceAttrRO
from cloudshell.shell.standards.resource_config_generic_models import GenericCLIConfig, GenericBackupConfig


class JuniperCPResourceConfig(GenericCLIConfig, GenericBackupConfig):
    vrf_management_name = ResourceAttrRO(
        attribute_names.VRF_MANAGEMENT_NAME, ResourceAttrRO.NAMESPACE.SHELL_NAME
    )
    pass
