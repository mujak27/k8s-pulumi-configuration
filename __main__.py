import json
import pulumi
import pulumi_proxmoxve as proxmox
import os,yaml
from dotenv import load_dotenv
import ipaddress
load_dotenv()

provider = proxmox.Provider('proxmoxve',
    endpoint=os.getenv("PROXMOX_ENDPOINT"),
    insecure=(os.getenv("PROXMOX_INSECURE") == "True"),
    username=os.getenv("PROXMOX_USERNAME"),
    password=os.getenv("PROXMOX_PASSWORD"),
)

print("test")
print(os.getenv("PROXMOX_ENDPOINT"))

folder_path = "vms/22/"

def load_yaml_files_from_folder(folder_path):
    yaml_files = [file for file in os.listdir(folder_path) if file.endswith(".yaml")]
    loaded_data = []

    for yaml_file in yaml_files:
        file_path = os.path.join(folder_path, yaml_file)
        with open(file_path, 'r') as file:
            yaml_data = yaml.safe_load(file)
            loaded_data.append(yaml_data)

    return loaded_data

parsed_data = load_yaml_files_from_folder(folder_path)

for vm in parsed_data:
    disks = []
    nets = []
    ip_configs = []
    ssh_keys = []

    for v in vm:
        for vmcount in range(v['count']):
            base_resource_name=v['resource_name']
            name_counter = vmcount + 1
            base_vm_id=v['vm_id'],

            
            if 'disks' in v and v['disks'] is not None:
                for disk_entry in v['disks']:
                    for d in disk_entry:
                        disks.append(
                            proxmox.vm.VirtualMachineDiskArgs(
                                interface=disk_entry[d]['interface'],
                                datastore_id=disk_entry[d]['datastore_id'],
                                size=disk_entry[d]['size'],
                                file_format=disk_entry[d]['file_format'],
                                cache=disk_entry[d]['cache']
                            )
                        )

            for ip_config_entry in v['cloud_init']['ip_configs']:
                ipv4 = ip_config_entry.get('ipv4')

                if ipv4:
                    new_address = ''
                    ip, subnet = ipv4.get('address', '').split('/')
                    new_ip = str(ipaddress.ip_address(ip) + vmcount)
                    new_address = f"{new_ip}/{subnet}"

                    ip_configs = []
                    ip_configs.append(
                        proxmox.vm.VirtualMachineInitializationIpConfigArgs(
                            ipv4=proxmox.vm.VirtualMachineInitializationIpConfigIpv4Args(
                                address=new_address,
                                gateway=ipv4.get('gateway', '')
                            )
                        )
                    )


            for net_entry in v['network_devices']:
                for n in net_entry:
                    nets.append(
                        proxmox.vm.VirtualMachineNetworkDeviceArgs(
                            bridge=net_entry[n]['bridge'],
                            model=net_entry[n]['model']
                        )
                    )
            
            nodes = []
            for node in v['nodes']:
                nodes.append(node)

            virtual_machine = proxmox.vm.VirtualMachine(
                vm_id=base_vm_id[0] + vmcount,
                resource_name=f"{base_resource_name}-{name_counter}",
                # node_name=v['node_name'],
                node_name=nodes[vmcount % len(nodes)],
                agent=proxmox.vm.VirtualMachineAgentArgs(
                    enabled=v['agent']['enabled'],
                    type=v['agent']['type']
                ),
                bios=v['bios'],
                cpu=proxmox.vm.VirtualMachineCpuArgs(
                    cores=v['cpu']['cores'],
                    sockets=v['cpu']['sockets']
                ),
                clone=proxmox.vm.VirtualMachineCloneArgs(
                    node_name=v['clone']['node_name'],
                    vm_id=v['clone']['vm_id'],
                    full=v['clone']['full'],
                ),
                disks=disks,
                memory=proxmox.vm.VirtualMachineMemoryArgs(
                    dedicated=v['memory']['dedicated']
                ),
                name=f"{base_resource_name}-{name_counter}",
                network_devices=nets,
                initialization=proxmox.vm.VirtualMachineInitializationArgs(
                    type=v['cloud_init']['type'],
                    datastore_id=v['cloud_init']['datastore_id'],
                    interface=v['cloud_init']['interface'],
                    dns=proxmox.vm.VirtualMachineInitializationDnsArgs(
                        domain=v['cloud_init']['dns']['domain']
                    ),
                    ip_configs=ip_configs,
                    user_account=proxmox.vm.VirtualMachineInitializationUserAccountArgs(
                        username=os.getenv("SSH_USERNAME"),
                        password=os.getenv("SSH_PASSWORD"),
                        keys=json.loads(os.getenv("SSH_PUBLIC_KEY"))
                    ),
                ),
                on_boot=v['on_boot'],
                reboot=v['on_boot'],
                opts=pulumi.ResourceOptions(provider=provider,ignore_changes=v['ignore_changes']),
            )

            pulumi.export(v['name'], virtual_machine.id)

