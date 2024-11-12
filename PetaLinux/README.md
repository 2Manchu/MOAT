# Introduction
This directory contains files pertaining to building a PetaLinux image containing Xen for the ZCU106. Additionally, a pre-built PetaLinux image for the ZCU106 containing Xen and Stress-NG has been provided if the user does not desire to make any modifications to the choices that were made here.

# How to Build PetaLinux 2023.1 with Xen Support for ZCU106
The following instructions detail the process of building Xen for the Xilinx ZCU106. All steps were tested on a Ubuntu 22.04 using PetaLinux 2023.1 and the corresponding 2023.1 BSP. The information here was retrieved and modified from the following locations:  
https://www.hackster.io/whitney-knitter/ai-at-the-edge-xen-hypervisor-on-the-zcu102-067333  
https://xilinx-wiki.atlassian.net/wiki/spaces/A/pages/2552201222/Building+Xen+Hypervisor+with+PetaLinux+2022.2  
https://xilinx-wiki.atlassian.net/wiki/spaces/A/pages/2552201222/Building+Xen+Hypervisor+with+PetaLinux+2022.2#Booting-with-ImageBulider  
https://docs.amd.com/r/en-US/ug1144-petalinux-tools-reference-guide/petalinux-package-boot-Examples  
https://docs.amd.com/r/2023.1-English/ug1144-petalinux-tools-reference-guide/petalinux-package-wic

## Prerequisites
Installation of [PetaLinux 2023.1 Tools](https://www.xilinx.com/member/forms/download/xef.html?filename=petalinux-v2023.1-05012318-installer.run) with settings.sh sourced in your terminal
Downloaded [Xilinx ZCU106 2023.1 BSP Package](https://www.xilinx.com/member/forms/download/xef.html?filename=xilinx-zcu106-v2023.1-05080224.bsp) to a convenient location

## Create and Configure the Project
Change to the directory where you would like the project to be created.  
Create the project:  
`petalinux-create -t project -s <path to ZCU106 BSP>`  
`cd xilinx-zcu106-2023.1`  
We now need to configure the RootFS to package Xen tools and the PERF tools. First start the RootFS configurator:  
`petalinux-config -c rootfs`  
Then under the following submenus, select these options:  
```
Petalinux Package Groups  ---> packagegroup-petalinux-xen   --->  [*] packagegroup-petalinux-xen
Filesystem Packages ---> console ---> tools ---> xen ---> [*] xen-tools
Filesystem Packages ---> misc ---> [*] perf
```
Now set the RootFS type and Image name with main configurator:  
```
Image Packaging Configuration  --->  Root filesystem type (INITRAMFS)  ---> (X) INITRD
Image Packaging Configuration --->  Update/edit the name petalinux-initramfs-image to petalinux-image-minimal
```
We also need to tell PetaLinux to include Xen hardware in the device tree:  
`DTG Settings ---> [*] Enable Xen hardware DTSI`  

We also configure PetaLinux to autologin as root upon bootup in order to work more efficiently with the frontend:   
```
Image Features ---> [*] debug-tweaks
Image Features ---> [*] empty-root-password
Image Features ---> [*] serial-autologin-root
```

## Add Stress-NG to the Petalinux Build (optional)
To use stress-NG as a baseline benchmark program in the testbench, we can add a BitBake recipe so that the package is included in Dom0. First create the new recipe and add it to the PetaLinux project:  
`petalinux-create -t apps -n stress-ng --enable`  
The directory for the new layer will be under `$PROJ_ROOT/project-spec/meta-user/recipes-apps/stress-ng`.  
Use a text editor to open the `stress-ng.bb` file and replace the contents with the following:  
```
SUMMARY = "Simple stress-ng application"
SECTION = "PETALINUX/apps"
HOMEPAGE = "https://kernel.ubuntu.com/~cking/stress-ng/"
LICENSE = "GPL-2.0-only"
LIC_FILES_CHKSUM = "file://COPYING;md5=b234ee4d69f5fce4486a80fdaf4a4263"

BB_STRICT_CHECKSUM = "0"

SRC_URI = "https://github.com/ColinIanKing/stress-ng/archive/refs/tags/V0.18.05.tar.gz"

S = "${WORKDIR}/stress-ng-0.18.05"

do_compile() {
    oe_runmake
}

do_install() {
    oe_runmake install DESTDIR=${D}
    rm -rf ${D}/usr/share/bash-completion
}

```
An important note - If you're pulling down a different version of stress-ng than what's listed here, you'll need to recompute the md5 checksum on the license file and update the value in the bb file. Running `petalinux-build` will now include this package.

## Build and Package the Image
Build the PetaLinux image with `petalinux-build` and `cd` back to the project root directory after the build has completed (if not already there).  
After the image has built, we will need to generate a U-boot script to load Xen, and generate a BOOT.BIN containing the FSBL and U-boot:  
## Generating U-boot Script
Clone ImageBuilder: `git clone https://gitlab.com/xen-project/imagebuilder.git && cd imagebuilder`  
Open `config` using a text editor and replace the contents with the following:  
```
MEMORY_START="0x0"
MEMORY_END="0x80000000"

DEVICE_TREE="system.dtb"
XEN="xen"
DOM0_KERNEL="Image"
DOM0_MEM=1536
DOM0_VCPUS=1
DOM0_RAMDISK="rootfs.cpio.gz"

NUM_DOMUS=0

UBOOT_SOURCE="boot.source"
UBOOT_SCRIPT="boot.scr"
```
You should ensure that the device tree, xen binary, and rootfs names are consistent with the output of the build contained in `$PROJ_ROOT/images/linux/`, otherwise the script will error out.  
Generate the script with `./scripts/uboot-script-gen -c config -d ../images/linux/ -t "load mmc 0:1"`, where the argument to `-t` indicates that we will be loading from an SD card.  
## Generate BOOT.BIN
`BOOT.BIN` contains the first-stage bootloader and U-boot proper, which will then execute the boot script generated by the output of the previous step to load Xen and the Linux kernel.  
`cd` back to `$PROJ_ROOT/images/linux`.
Use `petalinux-package` to generate the boot binary:  
`petalinux-package --boot --format BIN --fsbl zynqmp_fsbl.elf --u-boot`  
We can now package the RootFS, device tree, and boot files into a WIC disk image:  
`petalinux-package --wic --bootfiles "BOOT.BIN boot.scr Image system.dtb xen rootfs.cpio.gz"`

Flash the generated `petalinux-sdimage.wic` file onto an SD card using BalenaEtcher or utility of your choice, and boot the system.
