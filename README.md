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
sudo apt install -y build-essential gfortran libblas-dev libgoogle-perftools-dev liblapack-dev \
                    libtinfo5 m4 protobuf-compiler python-is-python3 python3-dev python3-distutils \
                    python3-pip scons wget
```

Don't forget to initialize and update the git submodules in this repository.

### gem5

Once dependencies are installed, build gem5:

```
cd gem5
scons build/RISCV/gem5.debug -j `nproc`
```

### XLS

Then, build the gem5 XLS plugin and the RLE design:

```
cd xls
bazel build //xls/simulation/gem5:gem5_xls_plugin //xls/modules/rle:rle_enc_opt_ir
```

In the root of this project, create a symbolic link to the RLE IR file:

```
ln -s xls/bazel-bin/xls/modules/rle/rle_enc_opt_ir.opt.ir
```

### Firmware
Next, build the firmware:

```
cd firmware
source ./ci/get_toolchain.sh
make PLATFORM="demo-gem5" MAKE-CONFIG="DMA=none INTERRUPTS=no"
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

## Run

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
