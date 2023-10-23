#!/usr/bin/env python3

# Copyright (C) 2024 Antmicro
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

import sys
import asyncio
import subprocess
import shlex
from pathlib import Path
from argparse import ArgumentParser
from contextlib import contextmanager

from generate_fw_name import generate_fw_name, generate_config_name

XLS = Path('xls')
GEM5 = Path('gem5')

def wait_for_gem5_socket(gem5_proc: subprocess.Popen):
    for line in gem5_proc.stderr:
        if len(line) == 0:
            continue
        print(line)
        if 'system.platform.terminal: Listening for connections on port 3456' in line:
            break

class Gem5Runner():
    gem5_proc: asyncio.subprocess.Process
    read_stderr_lines: bool

    def __init__(self):
        self.gem5_proc = None
        self.read_stderr_lines = False

    async def start_gem5(self, firmware, plugin, config):
        args = [
            '--debug-flags=XlsDev',
            '--listener-mode=on',
            str(GEM5 / 'configs/rv32/rv32.py'),
            '--firmware', str(firmware),
            '--xls-plugin', plugin,
            '--xls-config', str(config),
        ]
        cmd = shlex.join([str(GEM5 / 'build/RISCV/gem5.debug')] + args)

        print(f'RUNNING {cmd}')

        self.gem5_proc = await asyncio.create_subprocess_exec(
            str(GEM5 / 'build/RISCV/gem5.debug'),
            *[shlex.quote(arg) for arg in args],
            stderr=asyncio.subprocess.PIPE
        )

    def kill_gem5(self):
        if self.gem5_proc is not None:
            self.gem5_proc.kill()

    async def stderr_lines(self):
        self.read_stderr_lines = True
        while self.read_stderr_lines:
            line = await self.gem5_proc.stderr.readline()
            yield line.decode().rstrip()

    async def consume_stderr_lines(self):
        async for line in self.stderr_lines():
            continue

    def stop_stderr_lines(self):
        self.read_stderr_lines = False

    async def wait_for_gem5_socket(self):
        self.read_stderr_lines = True
        while self.read_stderr_lines:
            line = await self.gem5_proc.stderr.readline()
            line_decoded = line.decode()
            if len(line_decoded) == 0:
                continue
            sys.stderr.write(line_decoded)
            sys.stderr.flush()
            if 'system.platform.terminal: Listening for connections on port 3456' in line_decoded:
                break

@contextmanager
def run_gem5():
    try:
        gem5 = Gem5Runner()
        yield gem5
    finally:
        gem5.kill_gem5()

async def probe_gem5(gem5: Gem5Runner, stimuli: str, reference: str):
    test_result = subprocess.run([
        'ci/response_tester.py',
        '--stimuli', stimuli,
        '--reference', reference
    ])

    print(test_result.stdout)

    gem5.stop_stderr_lines()

    return test_result.returncode

async def test_gem5(gem5: Gem5Runner, firmware, plugin, config, stimuli, reference):
    await gem5.start_gem5(firmware, plugin, config)
    await gem5.wait_for_gem5_socket()
    print('Gem5 is ready!')
    gem5.stop_stderr_lines()

    _, retcode = await asyncio.gather(
        gem5.consume_stderr_lines(),
        probe_gem5(gem5, stimuli, reference)
    )

    return retcode

def main():
    parser = ArgumentParser()
    parser.add_argument('--simulator', type=str, required=True)
    parser.add_argument('--plugin', type=str, required=True)
    parser.add_argument('--firmware', type=str, required=True)
    args = parser.parse_args()

    fw_name = generate_fw_name()
    stimuli = f'ci/test_data/{fw_name}_stimuli'
    reference = f'ci/test_data/{fw_name}_response'
    config_name = f'ci/test_data/{generate_config_name()}'

    if args.simulator == 'gem5':
        #run_gem5(args.firmware, args.plugin, config_name, stimuli, reference)

        with run_gem5() as gem5:
            retcode = asyncio.run(
                test_gem5(
                    gem5,
                    args.firmware,
                    args.plugin,
                    config_name,
                    stimuli,
                    reference)
            )
        exit(retcode)


if __name__ == '__main__':
    main()
