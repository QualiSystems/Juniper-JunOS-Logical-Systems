from cloudshell.networking.juniper.cli.juniper_cli_configurator import JuniperCliConfigurator


class _LSConfManager(object):
    def __init__(self):
        pass

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class LSConfigurator(JuniperCliConfigurator):

    def __init__(self, ls_name, cli, resource_config, logger):
        super().__init__(cli, resource_config, logger)
        self.ls_name = ls_name

    def enable_mode_service(self):
        pass

    def config_mode_service(self):
        pass
