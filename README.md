# XLS co-simulation demo

Copyright (C) Antmicro 2024

This repository contains a demo for co-simulation of XLS and Gem5/Renode.

This demonstration uses the following projects as git submodules:
- [XLS](https://github.com/google/xls/)
- [gem5](https://github.com/gem5/gem5)
- [Renode](https://github.com/renode/renode)
- [Firmware](https://github.com/antmicro/xls-cosimulation-riscv-firmware)

## Build

The system packages required for this demo are also listed in the CI workflow
file, in the job `Install dependencies`. Depending on the OS flavor, this list
may vary.

```
sudo apt update
sudo apt install -y git automake autoconf libtool g++ coreutils policykit-1 \
    libgtk2.0-dev uml-utilities gtk-sharp2 python3 build-essential gfortran \
    libblas-dev libgoogle-perftools-dev liblapack-dev libtinfo5 m4 \
    protobuf-compiler python-is-python3 python3-dev python3-distutils \
    python3-pip scons wget
```

Don't forget to initialize and update the git submodules in this repository.

### gem5

Once dependencies are installed, build gem5:

```
cd gem5
scons build/RISCV/gem5.debug -j `nproc`
```

## Renode

To build Renode, use:
```
cd renode
./build.sh
```

### XLS

Then, build the gem5 and Renode XLS plugins and the RLE design:

```
cd xls
bazel build //xls/simulation/gem5:gem5_xls_plugin //xls/modules/rle:rle_enc_opt_ir
bazel build //xls/simulation/renode:renode_xls_peripheral_plugin
```

In the root of this project, create a symbolic link to the RLE IR file, and
renode plugin.


```
ln -s xls/bazel-bin/xls/modules/rle/rle_enc_opt_ir.opt.ir
ln -s xls/bazel-bin/xls/simulation/renode/librenode_xls_peripheral_plugin.so
```

### Firmware
Next, build the firmware:

```
cd firmware
source ./ci/get_toolchain.sh
make PLATFORM="demo-gem5" MAKE-CONFIG="DMA=none INTERRUPTS=no"
make PLATFORM="demo-renode" MAKE-CONFIG="DMA=none INTERRUPTS=no"
```

Refer to `firmware/README.md` to adjust build setting for the communication
method you want to test (stream/dma/axi-like-dma, polling/interrupts).

### Terminal

You need a tool to attach to the terminal exposed by gem5, capable of using
sockets exposed by gem5's serial devices. The `m5term` tool is available in the
gem5 utilities:

```
cd gem5/util/term
make
```

Alternatively, you can also use `socat`, which can be installed with APT.

## Run Gem5

To run gem5 co-simulation you need execute the `rv32.py` script. If you followed
this README, then the following arguments should work:

```
./gem5/build/RISCV/gem5.debug gem5/configs/rv32/rv32.py --firmware firmware/out/demo-gem5/fw_demo-gem5.elf \
                                                        --xls-plugin xls/./bazel-bin/xls/simulation/gem5/libgem5_xls_plugin.so \
                                                        --xls-config ci/test_data/config.textproto
```

In general, arguments of the `rv_32.py` script should be adjusted:
- `--firmware`, path to the firmware ELF file
- `--xls-plugin`, path to the XLS plugin shared object
- `--xls-config`, path to the `.textproto` configuration file stored in the `ci/test_data/` directory. There are currently 3 configurations, which correspond to 3 ways to build the firmware.

```
./gem5/build/RISCV/gem5.debug gem5/configs/rv32/rv32.py --firmware path/to/the/firmware.elf
                                                        --xls-plugin path/to/libgem5_xls_plugin.so
                                                        --xls-config path/to/config.textproto
```

If the run is successful, then you will see output with the following lines:

```
system.platform.terminal: Listening for connections on port 3456
```

Followed by simulation started prompt:

```
system.remote_gdb: Listening for connections on port 7000
Starting simulation
src/sim/simulate.cc:194: info: Entering event queue @ 0.  Starting simulation...
```

### Interactive prompt

Connect to the terminal:

If you are using m5term:
```
m5term 3456
```

If you are using socat:
```
socat STDIO,cfmakeraw tcp:localhost:3456,retry,forever
```

You will be greeted with an interactive prompt:

```
==== m5 terminal: Terminal 0 ====
check_init: Seems that we started cleanly.
RISC-V CSRs: MVENDORID=00000000, MARCHID=00000000, MIMPID=00000000, MHARTID=00000000, MSTATUS=00002000,
MISA=4014112d, MIE=00000000
[INFO] Input symbol size: 4 bytes
[INFO] Output symbol size: 5 bytes
Enter RLE input:
```

The prompt might differ slightly depending on the version of the firmware you
are using. Now you can provide input, e.g. "Hello" and the response will be:

```
RLE input: Hello
Running RLE...
[H, 1]
[e, 1]
[l, 2]
[o, 1] (last)
```

## Run Renode

To run the Renode simulation, execute the following commands:
```
RENODE="$(realpath renode/renode)"
RLE_IR_PATH="$(realpath rle_enc_opt_ir.opt.ir)"
RENODE_PLUGIN="$(realpath librenode_xls_peripheral_plugin.so)"
cd firmware
sed -i.bak 's|^path_to_ir_design: .*|path_to_ir_design: \"'"${RLE_IR_PATH}"'\"|g' rle_enc_sm.textproto
sed -i.bak 's|^\$xlsPeripheralLinux.*|\$xlsPeripheralLinux?=@'"${RENODE_PLUGIN}"'|g' vexriscv_rle.resc
${RENODE} --disable-xwt --console ./vexriscv_rle.resc
```

(There are 3 configurations for Renode available in the `firmware/` directory,
which correspond to different methods of communicating with the underlying
XLS peripheral. Each of them consist of the textproto file and a dedicated
platform file. If you want to check them, provide different files from
the `firmware/` directory in place of `rle_enc_sm.textproto` and `vexriscv_rle.resc`)

After that, the Renode will start and open an interactive console:
```
16:20:19.0742 [INFO] Loaded monitor commands from: /path/to/xls-cosimulation-demonstrator/renode/scripts/monitor.py
Renode, version 1.14.0.26712 (f6188f00-202402211450)

(monitor) i $CWD/./vexriscv_rle.resc
16:20:19.1991 [INFO] Including script: /path/to/xls-cosimulation-demonstrator/firmware/vexriscv_rle.resc
16:20:19.2061 [INFO] System bus created.
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
I0000 00:00:1708528820.696475 1680195 peripheral_factory.cc:66] Setting up simulation of the following design: "/home/user/.cache/bazel/bazel_user/83ddd7cf786fe1407362b8d7e02bd406/execroot/com_google_xls/bazel-out/k8-fastbuild/bin/xls/modules/rle/rle_enc_opt_ir.opt.ir"
16:20:20.6976 [INFO] xls0: Setting up simulation of the following design: "/home/user/.cache/bazel/bazel_user/83ddd7cf786fe1407362b8d7e02bd406/execroot/com_google_xls/bazel-out/k8-fastbuild/bin/xls/modules/rle/rle_enc_opt_ir.opt.ir"
I0000 00:00:1708528820.705300 1680195 xlsperipheral.cc:41] Creating generic::XlsPeripheral.
16:20:20.7054 [INFO] xls0: Creating generic::XlsPeripheral.
I0000 00:00:1708528820.705736 1680195 peripheral_factory.cc:138] Registering channel "rle_enc__input_r"
I0000 00:00:1708528820.705790 1680195 peripheral_factory.cc:138] Registering channel "rle_enc__output_s"
16:20:20.7058 [INFO] xls0: Registering channel "rle_enc__input_r"
16:20:20.7058 [INFO] xls0: Registering channel "rle_enc__output_s"
16:20:20.7059 [WARNING] xls0: The Verilated peripheral is already connected.
16:20:20.7795 [INFO] sysbus: Loading segment of 1149824 bytes length at 0x40000000.
16:20:20.7988 [INFO] cpu0: Setting PC value to 0x40000000.
16:20:20.8175 [INFO] Demo: GDB server with all CPUs started on port :3333
```

Then start your simulation using `start` command in the Renode prompt:
```
(Demo) start
Starting emulation...
16:20:24.4513 [INFO] Demo: Machine started.
16:20:24.5002 [INFO] uart0: [host: 3.79s (+3.79s)|virt: 0s (+0s)] check_init: Seems that we started cleanly.
16:20:24.5030 [INFO] uart0: [host: 3.79s (+2.79ms)|virt: 0.1ms (+0.1ms)] RISC-V CSRs: MVENDORID=00000000, MARCHID=00000000, MIMPID=00000000, MHARTID=00000000, MSTATUS=00000000, MISA=40041105, MIE=00000000
16:20:24.5032 [INFO] uart0: [host: 3.79s (+0.23ms)|virt:    0.1ms (+0s)] [INFO] Input symbol size: 5 bytes
16:20:24.5034 [INFO] uart0: [host: 3.79s (+0.15ms)|virt:    0.1ms (+0s)] [INFO] Output symbol size: 5 bytes
16:20:24.5034 [INFO] uart0: [host: 3.79s (+0.14ms)|virt:    0.1ms (+0s)] Enter RLE input:
```

To encode a word, for example "Hello", pass the word to the uart peripheral:
```
sysbus.uart0 WriteLine "Hello"
```

Then you should recive the following output from the simulated XLS peripheral:
```
(Demo) 16:30:39.0396 [INFO] uart0: [host:  0.62ks (+0.6ks)|virt:  33.74s (+33s)] Hello
16:30:39.0405 [INFO] uart0: [host:    0.62ks (+1ms)|virt:   33.74s (+0s)] RLE input: Hello
16:30:39.0407 [INFO] uart0: [host: 0.62ks (+0.17ms)|virt:   33.74s (+0s)] Running RLE...
16:30:39.0427 [INFO] uart0: [host: 0.62ks (+2.02ms)|virt: 33.74s (+0.1ms)] [H, 1]
16:30:39.0430 [INFO] uart0: [host: 0.62ks (+0.22ms)|virt:    33.74s (+0s)] [e, 1]
16:30:39.0431 [INFO] uart0: [host: 0.62ks (+0.19ms)|virt:    33.74s (+0s)] [l, 2]
16:30:39.0434 [INFO] uart0: [host: 0.62ks (+0.22ms)|virt:    33.74s (+0s)] [o, 1] (last)
16:30:39.2789 [INFO] uart0: [host:  0.62ks (+0.24s)|virt: 33.74s (+0.7ms)]
16:30:39.2790 [INFO] uart0: [host: 0.62ks (+0.16ms)|virt:    33.74s (+0s)] Enter RLE input:
```
