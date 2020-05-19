import json
import os
import uuid

import jsonpickle
from cloudshell.api.cloudshell_api import AttributeNameValue
from cloudshell.cli.service.cli import CLI
from cloudshell.cli.service.session_pool_manager import SessionPoolManager

from cloudshell.cp.core import DriverRequestParser
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.cp.core.models import DriverResponse, DeployAppResult, VmDetailsData, VmDetailsProperty
from cloudshell.shell.core.driver_context import AutoLoadDetails

from cloudshell.shell.core.session.logging_session import LoggingSessionContext

from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext

from cloudshell.shell.flows.connectivity.basic_flow import AbstractConnectivityFlow

from cloudshell.networking.juniper.cli.juniper_cli_configurator import JuniperCliConfigurator
from cloudshell.networking.juniper.flows.configuration_flow import JuniperConfigurationFlow
from cloudshell.shell.flows.command.basic_flow import RunCommandFlow

from driver_files.cli.configurator import LSConfigurator
from driver_files.flows import CreateRemoveLSFlow
from driver_files.resource_config import JuniperCPResourceConfig


class JuniperLSCloudProviderDriver(ResourceDriverInterface):
    SHELL_NAME = "Juniper LS Cloud Provider"
    SUPPORTED_OS = [r'[Jj]uniper']

    class ATTRIBUTE:
        INST_UUID = "Instance UUID"
        LS_NAME = "LS Name"
        VNIC_SOURCE = "Requested Source vNIC Name"
        VNIC_TARGET = "Requested Target vNIC Name"

    def __init__(self):
        """
        ctor must be without arguments, it is created with reflection at run time
        """
        self.request_parser = DriverRequestParser()
        self._session_pool = None

    def initialize(self, context):
        """
        Called every time a new instance of the driver is created

        This method can be left unimplemented but this is a good place to load and cache the driver configuration,
        initiate sessions etc.
        Whatever you choose, do not remove it.

        :param InitCommandContext context: the context the command runs on
        """
        resource_config = JuniperCPResourceConfig.from_context(self.SHELL_NAME, context)
        session_pool_size = int(resource_config.sessions_concurrency_limit)
        self._session_pool = SessionPoolManager(max_pool_size=session_pool_size, pool_timeout=100)
        return 'Finished initializing'

    # <editor-fold desc="Mandatory Commands">

    # <editor-fold desc="Discovery">

    def get_inventory(self, context):
        """
        Called when the cloud provider resource is created
        in the inventory.

        Method validates the values of the cloud provider attributes, entered by the user as part of the cloud provider resource creation.
        In addition, this would be the place to assign values programmatically to optional attributes that were not given a value by the user.

        If one of the validations failed, the method should raise an exception

        :param AutoLoadCommandContext context: the context the command runs on
        :return Attribute and sub-resource information for the Shell resource you can return an AutoLoadDetails object
        :rtype: AutoLoadDetails
        """

        # run 'shellfoundry generate' in order to create classes that represent your data model

        return AutoLoadDetails([], [])

    # </editor-fold>

    # <editor-fold desc="App Deployment">

    def Deploy(self, context, request, cancellation_context=None):
        """
        Called when reserving a sandbox during setup, a call for each app in the sandbox.

        Method creates the compute resource in the cloud provider - VM instance or container.

        If App deployment fails, return a "success false" action result.

        :param cloudshell.shell.core.driver_context.ResourceCommandContext context:
        :param str request: A JSON string with the list of requested deployment actions
        :param CancellationContext cancellation_context:
        :return:
        :rtype: str
        """

        '''
        # parse the json strings into action objects
        actions = self.request_parser.convert_driver_request_to_actions(request)
        
        # extract DeployApp action
        deploy_action = single(actions, lambda x: isinstance(x, DeployApp))
        
        # if we have multiple supported deployment options use the 'deploymentPath' property 
        # to decide which deployment option to use. 
        deployment_name = deploy_action.actionParams.deployment.deploymentPath
                
        deploy_result = _my_deploy_method(context, actions, cancellation_context)
        return DriverResponse(deploy_result).to_driver_response_json()
        '''
        with LoggingSessionContext(context) as logger:
            logger.info(request)
            api = CloudShellSessionContext(context).get_api()
            resource_config = JuniperCPResourceConfig.from_context(self.SHELL_NAME, context, api, self.SUPPORTED_OS)
            cli_configurator = JuniperCliConfigurator(CLI(self._session_pool), resource_config, logger)

            ls_flow = CreateRemoveLSFlow(cli_configurator, logger)

            actions = DriverRequestParser().convert_driver_request_to_actions(request)
            reservation_details = api.GetReservationDetails(context.reservation.reservation_id,
                                                            disableCache=True).ReservationDescription

            results = []
            for deploy_action in actions:
                app_name = deploy_action.actionParams.appName

                int_dict = self._get_int_names(reservation_details, app_name)
                logger.info("{}:{}".format(app_name, str(int_dict)))
                if not int_dict:
                    raise Exception("Failed to deploy Logical System without interfaces. "
                                    "Please create appropriate connections")

                vm_name = "{}-{}-".format(app_name.replace(" ", "-"),
                                            context.reservation.reservation_id[-2:])
                vm_uuid = uuid.uuid4().hex[:4]
                vm_name += vm_uuid

                while ls_flow.check_ls_name_exist(vm_name):
                    vm_uuid = uuid.uuid4().hex[:4]
                    vm_name += vm_uuid
                reserved_int_list = self._get_reserved_ports(api, reservation_details, app_name, context.resource.name)
                deployed_int_dict = ls_flow.create_ls(vm_name, int_dict, reserved_int_list)
                vm_instance_data = [
                    # VmDetailsProperty(self.ATTRIBUTE.INST_UUID, vm_uuid),
                    VmDetailsProperty(self.ATTRIBUTE.LS_NAME, vm_name),
                ]
                vm_interfaces_data = [VmDetailsProperty("vNIC {} Name".format(list(deployed_int_dict.keys()).index(i)),
                                                        deployed_int_dict.get(i)) for i in deployed_int_dict]
                connectors_to_update = {k: v for k, v in deployed_int_dict.items() if v != int_dict.get(k)}
                self._update_connectors(api, context.reservation.reservation_id, connectors_to_update)

                vm_instance_data.extend(vm_interfaces_data)

                deploy_result = DeployAppResult(actionId=deploy_action.actionId,
                                                infoMessage="Deployment Completed Successfully",
                                                vmUuid=vm_uuid,
                                                vmName=vm_name,
                                                deployedAppAddress=resource_config.address,
                                                deployedAppAttributes=[],
                                                vmDetailsData=VmDetailsData(vm_instance_data))

                results.append(deploy_result)
            return DriverResponse(results).to_driver_response_json()

    def _extract_attribute(self, attributes, name):
        for attr in attributes:
            if attr.Name.lower() == name.lower():
                return attr.Value

    def _get_int_names(self, reserv_details, app_name):
        int_names = {}
        for connector in reserv_details.Connectors:
            if app_name == connector.Source:
                int_names[connector] = self._extract_attribute(connector.Attributes, self.ATTRIBUTE.VNIC_SOURCE)
            if app_name == connector.Target:
                int_names[connector] = self._extract_attribute(connector.Attributes, self.ATTRIBUTE.VNIC_TARGET)
        return int_names

    def _update_connectors(self, api, reservation_id, int_names):
        for connector, port in int_names.items():
            attrs = connector.Attributes
            attrs.append(AttributeNameValue("Requested Source vNIC Name", port))
            api.SetConnectorAttributes(reservation_id, connector.Source, connector.Target, attrs)

    def _get_reserved_ports(self, api, reserv_details, app_name, cp_name):
        reserved_ports = []
        for ls_app in reserv_details.Apps:
            if app_name != ls_app.Name and ls_app.DeploymentPaths[0].DeploymentService.CloudProvider == cp_name:
                reserved_ports.extend(self._get_int_names(reserv_details, ls_app.Name).keys())
        for ls_resource in reserv_details.Resources:
            if ls_resource.VmDetails and ls_resource.VmDetails.CloudProviderFullName == cp_name:
                reserved_ports.extend(
                    [port.Value for port in ls_resource.VmDetails.InstanceData if port.Name.lower().startswith("vnic")])
            resource_details = api.GetResourceDetails(ls_resource.Name)
            for res_info in resource_details.ChildResources:
                vnic = self._extract_attribute(res_info.ResourceAttributes,
                                           'Juniper Virtual Router Shell.GenericVPort.Requested vNIC Name')
                if vnic and vnic not in reserved_ports:
                    reserved_ports.append(vnic)

        return list(filter(lambda x: x, reserved_ports))

    def run_custom_command(self, context, ports, custom_command):
        """Send custom command

        :param ResourceCommandContext context: ResourceCommandContext object with all Resource Attributes inside
        :return: result
        :rtype: str
        """
        with LoggingSessionContext(context) as logger:
            api = CloudShellSessionContext(context).get_api()

            resource_config = JuniperCPResourceConfig.from_context(self.SHELL_NAME, context, api, self.SUPPORTED_OS)

            response = ""
            for endpoint in context.remote_endpoints:
                res_details = api.GetResourceDetails(endpoint.name)
                ls_name = self._extract_attribute(res_details.VmDetails.InstanceData, self.ATTRIBUTE.LS_NAME)
                ls_cli_configurator = LSConfigurator(ls_name, self._session_pool, resource_config, logger)

                send_command_operations = RunCommandFlow(logger, ls_cli_configurator)
                response += send_command_operations.run_custom_command(custom_command)
            return response

    def run_custom_config_command(self, context, ports, custom_command):
        """Send custom command in configuration mode

        :param ResourceCommandContext context: ResourceCommandContext object with all Resource Attributes inside
        :return: result
        :rtype: str
        """
        with LoggingSessionContext(context) as logger:
            api = CloudShellSessionContext(context).get_api()

            resource_config = JuniperCPResourceConfig.from_context(self.SHELL_NAME, context, api, self.SUPPORTED_OS)

            response = ""
            for endpoint in context.remote_endpoints:
                res_details = api.GetResourceDetails(endpoint.name)
                ls_name = self._extract_attribute(res_details.VmDetails.InstanceData, self.ATTRIBUTE.LS_NAME)
                ls_cli_configurator = LSConfigurator(ls_name, self._session_pool, resource_config, logger)

                send_command_operations = RunCommandFlow(logger, ls_cli_configurator)
                response += send_command_operations.run_custom_config_command(custom_command)
            return response

    def PowerOn(self, context, ports):
        """
        Called when reserving a sandbox during setup, a call for each app in the sandbox can also be run manually by the sandbox end-user from the deployed App's commands pane

        Method spins up the VM

        If the operation fails, method should raise an exception.

        :param ResourceRemoteCommandContext context:
        :param ports:
        """
        pass

    def remote_refresh_ip(self, context, ports, cancellation_context):
        """

        Called when reserving a sandbox during setup, a call for each app in the sandbox can also be run manually by the sandbox end-user from the deployed App's commands pane

        Method retrieves the VM's updated IP address from the cloud provider and sets it on the deployed App resource
        Both private and public IPs are retrieved, as appropriate.

        If the operation fails, method should raise an exception.

        :param ResourceRemoteCommandContext context:
        :param ports:
        :param CancellationContext cancellation_context:
        :return:
        """
        pass

    def GetVmDetails(self, context, requests, cancellation_context):
        """
        Called when reserving a sandbox during setup, a call for each app in the sandbox can also be run manually by the sandbox
        end-user from the deployed App's VM Details pane

        Method queries cloud provider for instance operating system, specifications and networking information and
        returns that as a json serialized driver response containing a list of VmDetailsData.

        If the operation fails, method should raise an exception.

        :param ResourceCommandContext context:
        :param str requests:
        :param CancellationContext cancellation_context:
        :return:
        """

        with LoggingSessionContext(context) as logger:
            logger.info(requests)
            api = CloudShellSessionContext(context).get_api()

            vm_details_data = []

            requests_json = json.loads(requests)

            for refresh_request in requests_json["items"]:
                vm_name = refresh_request["deployedAppJson"]["name"]
                # deployment_service = refresh_request["appRequestJson"]["deploymentService"][
                #     "name"]
                resource_details = api.GetResourceDetails(vm_name)
                # logger.info(yaml.dump(resource_details))
                ls_name = self._extract_attribute(resource_details.VmDetails.InstanceData, self.ATTRIBUTE.LS_NAME)
                logger.info("LS Name: {}".format(ls_name))
                vm_inst_data = [VmDetailsProperty(self.ATTRIBUTE.LS_NAME, ls_name)]
                # for res_info in resource_details.ChildResources:
                #     port_name = res_info.Name
                #     vnic = self._extract_attribute(res_info.ResourceAttributes,
                #                                    'Juniper Virtual Router Shell.GenericVPort.Requested vNIC Name')
                #     vm_inst_data.append(VmDetailsProperty(port_name, vnic))
                vm_details_data.append(VmDetailsData(vm_inst_data, [], vm_name))
            return str(jsonpickle.encode(vm_details_data, unpicklable=False))

    def PowerCycle(self, context, ports, delay):
        """ please leave it as is """
        pass

    # <editor-fold desc="Power off / Delete">

    def PowerOff(self, context, ports):
        """
        Called during sandbox's teardown can also be run manually by the sandbox end-user from the deployed App's commands pane

        Method shuts down (or powers off) the VM instance.

        If the operation fails, method should raise an exception.

        :param ResourceRemoteCommandContext context:
        :param ports:
        """
        pass

    def DeleteInstance(self, context, ports):
        """
        Called during sandbox's teardown or when removing a deployed App from the sandbox

        Method deletes the VM from the cloud provider.

        If the operation fails, method should raise an exception.

        :param ResourceRemoteCommandContext context:
        :param ports:
        """
        with LoggingSessionContext(context) as logger:
            api = CloudShellSessionContext(context).get_api()
            resource_config = JuniperCPResourceConfig.from_context(self.SHELL_NAME, context, api, self.SUPPORTED_OS)
            cli_configurator = JuniperCliConfigurator(CLI(self._session_pool), resource_config, logger)

            ls_flow = CreateRemoveLSFlow(cli_configurator, logger)

            for endpoint in context.remote_endpoints:
                res_details = api.GetResourceDetails(endpoint.name)
                ls_name = self._extract_attribute(res_details.VmDetails.InstanceData, self.ATTRIBUTE.LS_NAME)
                ls_flow.remove_ls(ls_name)

    # </editor-fold>

    # </editor-fold>

    ### NOTE: According to the Connectivity Type of your shell, remove the commands that are not
    ###       relevant from this file and from drivermetadata.xml.

    # <editor-fold desc="Mandatory Commands For L2 Connectivity Type">

    def save(self, context, ports, folder_path, configuration_type, vrf_management_name):
        """Save selected file to the provided destination

        :param ResourceCommandContext context: ResourceCommandContext object with all Resource Attributes inside
        :param configuration_type: source file, which will be saved
        :param folder_path: destination path where file will be saved
        :param vrf_management_name: VRF management Name
        :return str saved configuration file name:
        """
        with LoggingSessionContext(context) as logger:
            api = CloudShellSessionContext(context).get_api()

            resource_config = JuniperCPResourceConfig.from_context(self.SHELL_NAME, context, api, self.SUPPORTED_OS)

            if not configuration_type:
                configuration_type = 'running'

            if not vrf_management_name:
                vrf_management_name = resource_config.vrf_management_name

            response = ""
            for endpoint in context.remote_endpoints:
                res_details = api.GetResourceDetails(endpoint.name)
                ls_name = self._extract_attribute(res_details.VmDetails.InstanceData, self.ATTRIBUTE.LS_NAME)
                ls_cli_configurator = LSConfigurator(ls_name, self._session_pool, resource_config, logger)

                configuration_operations = JuniperConfigurationFlow(resource_config, logger, ls_cli_configurator)
                logger.info('Save started')
                response += configuration_operations.save(folder_path=folder_path,
                                                          configuration_type=configuration_type,
                                                          vrf_management_name=vrf_management_name) + os.linesep
                logger.info('Save completed')

            return response

    # @GlobalLock.lock
    def restore(self, context, ports, path, configuration_type, restore_method, vrf_management_name):
        """Restore selected file to the provided destination

        :param ResourceCommandContext context: ResourceCommandContext object with all Resource Attributes inside
        :param path: source config file
        :param configuration_type: running or startup configs
        :param restore_method: append or override methods
        :param vrf_management_name: VRF management Name
        """
        with LoggingSessionContext(context) as logger:
            api = CloudShellSessionContext(context).get_api()

            resource_config = JuniperCPResourceConfig.from_context(self.SHELL_NAME, context, api, self.SUPPORTED_OS)

            if not configuration_type:
                configuration_type = 'running'

            if not restore_method:
                restore_method = 'override'

            if not vrf_management_name:
                vrf_management_name = resource_config.vrf_management_name

            for endpoint in context.remote_endpoints:
                res_details = api.GetResourceDetails(endpoint.name)
                ls_name = self._extract_attribute(res_details.VmDetails.InstanceData, self.ATTRIBUTE.LS_NAME)
                ls_cli_configurator = LSConfigurator(ls_name, self._session_pool, resource_config, logger)

                configuration_operations = JuniperConfigurationFlow(
                    resource_config, logger, ls_cli_configurator
                )
                logger.info('Restore for LS {} started'.format(ls_name))
                configuration_operations.restore(path=path, restore_method=restore_method,
                                                 configuration_type=configuration_type,
                                                 vrf_management_name=vrf_management_name)
                logger.info('Restore for LS {} completed'.format(ls_name))

    def ApplyConnectivityChanges(self, context, request):
        """
        Called during the orchestration setup and also called in a live sandbox when
        and instance is connected or disconnected from a VLAN
        service or from another instance (P2P connection).

        Method connects/disconnect VMs to VLANs based on requested actions (SetVlan, RemoveVlan)
        It's recommended to follow the "get or create" pattern when implementing this method.

        If operation fails, return a "success false" action result.

        :param ResourceCommandContext context: The context object for the command with resource and reservation info
        :param str request: A JSON string with the list of requested connectivity changes
        :return: a json object with the list of connectivity changes which were carried out by the driver
        :rtype: str
        """
        with LoggingSessionContext(context) as logger:
            connectivity_flow = LSConnectivityFlow(logger)
            # logger.info('Start applying connectivity changes, request is: {0}'.format(str(request)))
            result = connectivity_flow.apply_connectivity_changes(request=request)
            # logger.info('Finished applying connectivity changes, response is: {0}'.format(str(result)))
            # logger.info('Apply Connectivity changes completed')
            return result

    # </editor-fold> 

    # <editor-fold desc="Mandatory Commands For L3 Connectivity Type">

    # def PrepareSandboxInfra(self, context, request, cancellation_context):
    #     """
    #     Called in the beginning of the orchestration flow (preparation stage), even before Deploy is called.
    #
    #     Prepares all of the required infrastructure needed for a sandbox operating with L3 connectivity.
    #     For example, creating networking infrastructure like VPC, subnets or routing tables in AWS, storage entities such as S3 buckets, or
    #     keyPair objects for authentication.
    #     In general, any other entities needed on the sandbox level should be created here.
    #
    #     Note:
    #     PrepareSandboxInfra can be called multiple times in a sandbox.
    #     Setup can be called multiple times in the sandbox, and every time setup is called, the PrepareSandboxInfra method will be called again.
    #     Implementation should support this use case and take under consideration that the cloud resource might already exist.
    #     It's recommended to follow the "get or create" pattern when implementing this method.
    #
    #     When an error is raised or method returns action result with success false
    #     Cloudshell will fail sandbox creation, so bear that in mind when doing so.
    #
    #     :param ResourceCommandContext context:
    #     :param str request:
    #     :param CancellationContext cancellation_context:
    #     :return:
    #     :rtype: str
    #     """
    #     '''
    #     # parse the json strings into action objects
    #     actions = self.request_parser.convert_driver_request_to_actions(request)
    #
    #     action_results = _my_prepare_connectivity(context, actions, cancellation_context)
    #
    #     return DriverResponse(action_results).to_driver_response_json()
    #     '''
    # pass

    # def CleanupSandboxInfra(self, context, request):
    #     """
    #     Called at the end of reservation teardown
    #
    #     Cleans all entities (beside VMs) created for sandbox, usually entities created in the
    #     PrepareSandboxInfra command.
    #
    #     Basically all created entities for the sandbox will be deleted by calling the methods: DeleteInstance, CleanupSandboxInfra
    #
    #     If a failure occurs, return a "success false" action result.
    #
    #     :param ResourceCommandContext context:
    #     :param str request:
    #     :return:
    #     :rtype: str
    #     """
    #     '''
    #     # parse the json strings into action objects
    #     actions = self.request_parser.convert_driver_request_to_actions(request)
    #
    #     action_results = _my_cleanup_connectivity(context, actions)
    #
    #     return DriverResponse(action_results).to_driver_response_json()
    #     '''
    #     pass

    # </editor-fold>

    # <editor-fold desc="Optional Commands For L3 Connectivity Type">

    def SetAppSecurityGroups(self, context, request):
        """
        Called via cloudshell API call

        Programmatically set which ports will be open on each of the apps in the sandbox, and from
        where they can be accessed. This is an optional command that may be implemented.
        Normally, all outbound traffic from a deployed app should be allowed.
        For inbound traffic, we may use this method to specify the allowed traffic.
        An app may have several networking interfaces in the sandbox. For each such interface, this command allows to set
        which ports may be opened, the protocol and the source CIDR

        If operation fails, return a "success false" action result.

        :param ResourceCommandContext context:
        :param str request:
        :return:
        :rtype: str
        """
        pass

    # </editor-fold>

    def cleanup(self):
        """
        Destroy the driver session, this function is called every time a driver instance is destroyed
        This is a good place to close any open sessions, finish writing to log files, etc.
        """
        pass


class LSConnectivityFlow(AbstractConnectivityFlow):

    def _add_vlan_flow(self, vlan_range, port_mode, port_name, qnq, c_tag):
        """Add VLAN, has to be implemented."""
        return "Success"

    def _remove_vlan_flow(self, vlan_range, port_name, port_mode):
        """Remove VLAN, has to be implemented."""
        return "Success"
