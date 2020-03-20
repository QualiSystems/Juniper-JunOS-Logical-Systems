from cloudshell.cli.configurator import AbstractModeConfigurator

class _LSConfManager(object):
    def __init__(self):
        pass

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class LSConfigurator(AbstractModeConfigurator):

    def __init__(self, base_configurator, ls_name):
        self.base_configurator = base_configurator
        self.ls_name = ls_name

    def enable_mode_service(self):
        pass



    def config_mode_service(self):
        pass
