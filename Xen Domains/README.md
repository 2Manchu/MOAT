# Setting up a DomU
One approach to creating a DomU is to use the kernel and ramdisk that are already present on the Dom0 system. In our case, it is the PetaLinux kernel and ramdisk. Alternatively, one may opt to use a different Linux operating system, which is the approach we take.

## Files
In this directory are the following files:

* vmlinux-5.15.0-119-generic (kernel)
* initrd.img-5.15.0-119-generic (ramdisk)
* ubuntu-rootfs.img.tar.gz (Root filesystem for persistent storage)
* ubuntu.cfg (DomU configuration file)

## DomU Features
This DomU is configured to use an Ubuntu ramdisk and Ubuntu Base edition root filesystem image. It has been set up with the `stress-ng` package via `virt-customize` to facilitate execution time testing with a variety of different programs.

## DomUs with Different Operating Systems
If your preference is not Ubuntu, it is possible to use different OSes, such as Alpine Linux, under your DomUs. You will need to extract the kernel and ramdisk from the image that you've downloaded. DomUs can only direct boot an uncompressed kernel (vmlinux), so you will also need to decompress your new kernel or configure the DomUs to use a bootloader that can load compressed kernels (vmlinuz).

## Preparation
Not much preparation is necessary to create this DomU. On your local device:

1. The RootFS is compressed to save space. Untar it into this directory with a tool of your choice.
2. We have set the default user as `root`, whose password is also `root`. If you wish to change this or add a user, you can install `libguestfs-tools` and use the command `virt-customize -a ubuntu-rootfs.img --root-password password:[your password]`.
3. There can sometimes be issues with the filysystem being mounted read-only, so ensure that read-write permissions are set for the rootfs image with. `sudo chmod 777 ubuntu-rootfs.img`
4. Make any necessary modifications to the DomU configuration file `ubuntu.cfg` regarding CPU core assignment and memory allocation. More details can be found [here](https://xenbits.xen.org/docs/unstable/man/xl.cfg.5.html)
5. Copy the kernel, ramdisk, unzipped ubuntu-rootfs.img file, and configuration file into a new folder on the persistent root partition of the SD card plugged into the ZCU106. This will likely be `/run/media/root-mmcblk0p2/[DomU-Name]`, where [DomU-Name] is the name of your DomU, if there are no other MMC devices plugged in. This is necessary because the default root directory (`'/'`) points to the ramdisk, which makes it non-persistent.
6. Once the files have been copied to the SD card, the user will need to create two more copies of the DomU configuration files and root filesystem images, as one copy is necessary per core that is used to generate interference. It is not necessary to copy the ramdisk and kernel images, as those items are read-only and not specific to a given core. The configuration files should be renamed to core1.cfg, core2.cfg, and core3.cfg, or up to however many cores the user’s target system has. The untarred root filesystem images should also be renamed according to this scheme. Each configuration file will also need to have two parameters modified to point to the correct disk image and assigned its corresponding CPU core. This should be done as follows:   
```
core[x].cfg
	...
	disk=['/run/media/root-mmcblk0p2/ubuntu/core[x].img,raw,xvda[x],rw']
	cpus=[x]
	Replace [x] with the number of the core you are configuring
	...
```
Once this configuration has been completed, the user can move on to setting up the test framework with their desired contention generation types and baseline programs.


### Manual DomU Creation
Normally, the frontend handles DomU creation and deletion automatically. If the user wishes to do this manually, it may be done as follows:   s
Create the the DomU with the command `sudo xl create -c [DomU-Name]/ubuntu.cfg`. The inclusion of the `-c` flag automatically connects the serial console of the DomU so output is immediately visible. If you omit the flag, you can list the name of the VM and connect to the console with `sudo xl list` and `sudo xl console [DomU-name-from-list]`, respectively.

### Manual DomU Deletion
There are several ways to shut down a domain. The first is with `sudo xl shutdown [DomU-Name]`, which signals to the guest that a graceful shutdown should be initiated. If that fails to work, `sudo xl destroy [DomU-Name]` will immediately terminate the VM.
