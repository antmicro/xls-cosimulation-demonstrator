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


import socket
import difflib
from argparse import ArgumentParser

def load_ioref(path):
    with open(path) as f:
        ref = f.read()
    return ref.replace('\n', '\r')

def print_diff(a, b):
    diff = difflib.ndiff(a, b)
    for i, dstr in enumerate(diff):
        if (dstr[0] == ' '):
            continue
        print('byte {}: {}'.format(i, dstr.encode()))

def main():
    parser = ArgumentParser()
    parser.add_argument('--stimuli', type=str, help='Stimuli source')
    parser.add_argument('--reference', type=str, required=True,
                        help='Reference text to compare output with')
    parser.add_argument('-P', '--port', type=str, default='3456',
                        help='Port for terminal socket')
    args = parser.parse_args()

    stimuli = load_ioref(args.stimuli)
    reference = load_ioref(args.reference)

    line_count = reference.count('\r')
    print(f'Found {line_count} lines in the reference file')

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(('127.0.0.1', 3456))
        print(f'Sending stimuli: {stimuli}')
        sock.sendall(stimuli.encode())

        recvd: bytes = b''

        lines_read = 0
        while lines_read < line_count:
            byte = sock.recv(1)
            if (byte == b'\r'):
                lines_read += 1
            recvd += byte

        decoded = recvd.decode()
        decoded_normalized = decoded.strip().replace('\r\n', '\r')

        print('Received the following output:\n')
        print(decoded)
        print('\n')

        if decoded_normalized == reference.strip():
            print('The output matches the reference!')
            exit(0)
        else:
            print('The output does not match the reference!')
            print_diff(reference.strip(), decoded_normalized)
            exit(1)



if __name__ == '__main__':
    main()