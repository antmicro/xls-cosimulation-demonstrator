#!/usr/bin/python3

import re
import os

def get_dma_irq_options():
    config = os.environ['MAKE_CONFIG']

    dma = re.findall('DMA=([a-zA-Z0-9]*)', config)[0];
    irq = re.findall('INTERRUPTS=([a-zA-Z0-9]*)', config)[0];

    return dma, irq


def generate_config_name():
    dma, _ = get_dma_irq_options()

    config = 'config'

    if dma != 'none':
        config += f'_{dma}'
    
    return config + '.textproto'

def generate_fw_name():
    platform = os.environ['PLATFORM']
    dma, irq = get_dma_irq_options()

    fw_name = f'fw_{platform}'
    if dma != 'none':
        fw_name += f'_{dma}'
    if irq == 'yes':
        fw_name += '_irq'

    return fw_name

def main():
    print(generate_fw_name())

if __name__ == '__main__':
    main()

