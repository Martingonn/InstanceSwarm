import libvirt
import os
import subprocess

# Function to list available disk images
def list_disk_images(image_path="/var/lib/libvirt/images/"):
    """Lists all .qcow2 disk images in the specified directory."""
    disk_images = [filename for filename in os.listdir(image_path) if filename.endswith(".qcow2")]
    return disk_images

# Function to create a new disk image
def create_disk_image(vm_name, size_gb=10, image_path="/var/lib/libvirt/images/"):
    """Creates a new .qcow2 disk image."""
    disk_path = f"{image_path}{vm_name}.qcow2"
    try:
        subprocess.run(["qemu-img", "create", "-f", "qcow2", disk_path, f"{size_gb}G"], check=True)
        print(f"Disk image created: {disk_path}")
        return disk_path
    except subprocess.CalledProcessError as e:
        print(f"Failed to create disk image: {e}")
        exit(1)

# Function to select or create a disk image
def get_disk_image(vm_name, image_path="/var/lib/libvirt/images/"):
    """Prompts the user to select an existing disk image or create a new one."""
    choice = input("Do you want to use an existing disk image? (yes/no): ").strip().lower()
    if choice == "yes":
        disk_images = list_disk_images(image_path)
        if not disk_images:
            print("No existing disk images found. Creating a new one.")
            return create_disk_image(vm_name)
        
        print("Available disk images:")
        for i, image in enumerate(disk_images):
            print(f"{i+1}. {image}")
        
        while True:
            try:
                selection = int(input("Enter the number of the disk image you want to use: "))
                if 1 <= selection <= len(disk_images):
                    return f"{image_path}{disk_images[selection - 1]}"
                else:
                    print("Invalid choice. Please enter a valid number.")
            except ValueError:
                print("Invalid input. Please enter a number.")
    else:
        return create_disk_image(vm_name)

# Define the XML configuration for a VM
def create_vm_xml(vm_name, memory_mb, vcpu_count, disk_path):
    """Generates XML configuration for a VM."""
    return f"""
    <domain type='kvm'>
        <name>{vm_name}</name>
        <memory unit='MiB'>{memory_mb}</memory>
        <vcpu placement='static'>{vcpu_count}</vcpu>
        <os>
            <type arch='x86_64' machine='pc-q35-5.2'>hvm</type>
            <boot dev='hd'/>
        </os>
        <devices>
            <disk type='file' device='disk'>
                <source file='{disk_path}'/>
                <target dev='vda' bus='virtio'/>
            </disk>
            <interface type='network'>
                <source network='default'/>
                <model type='virtio'/>
            </interface>
        </devices>
    </domain>
    """

# Connect to the libvirt daemon
def connect_to_libvirt():
    """Connects to the libvirt daemon."""
    try:
        conn = libvirt.open('qemu:///system')
        if conn is None:
            print("Failed to connect to the hypervisor")
            exit(1)
        return conn
    except libvirt.libvirtError as e:
        print(f"Failed to connect to the hypervisor: {e}")
        exit(1)

# Main function to create VMs
def create_vms(conn, num_vms):
    """Creates a specified number of VMs."""
    for i in range(1, num_vms + 1):
        vm_name = f"vm_{i}"
        memory_mb = 512  # Allocate 512 MB RAM per VM
        vcpu_count = 1   # Allocate 1 CPU core per VM

        # Get or create a disk image
        disk_path = get_disk_image(vm_name)

        # Generate XML configuration for the VM
        xml_config = create_vm_xml(vm_name, memory_mb, vcpu_count, disk_path)

        # Define and start the VM
        try:
            dom = conn.defineXML(xml_config)
            dom.create()
            print(f"VM {vm_name} created and started successfully with disk image: {disk_path}")
        except libvirt.libvirtError as e:
            print(f"Failed to create VM {vm_name}: {e}")

# Main execution
if __name__ == "__main__":
    conn = connect_to_libvirt()
    num_vms = 25  # Number of VMs to create
    create_vms(conn, num_vms)
    conn.close()
