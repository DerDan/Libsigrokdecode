##
## This file is part of the libsigrokdecode project.
##
## Copyright (C) 2012 Bert Vermeulen <bert@biot.com>
## Copyright (C) 2012 Uwe Hermann <uwe@hermann-uwe.de>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, see <http://www.gnu.org/licenses/>.
##

import sigrokdecode as srd


class Decoder(srd.Decoder):
    api_version = 3
    id = 'uart_trace'
    name = 'Uart Trace'
    longname = 'Uart Tracing'
    desc = 'Collect Bytes to strings'
    license = 'gplv3+'
    inputs = ['uart']
    outputs = []
    tags = ['Util']
    annotations = (
        ('rx_txt', 'Receive Text'),
        ('tx_txt', 'Transmit Text'),
    )
    annotation_rows = (
        ('rx', 'RX Trace', (0,)),
        ('tx', 'TX Trace', (1,)),
    )
    options = (
        {
            'id': 'line_separator', 'desc': 'Line Separator',
            'default': 'CR + LF',
            'values': ('CR + LF', 'Carriage Return', 'Line Feed', 'LF + CR')
        },
    )

    def __init__(self):
        self.reset()

    def reset(self):
        self.line_separator = ''
        self.text = ['', '']
        self.text_start = [None, None]
        self.separator_idx = [0, 0]
        self.separators = 0

    def start(self):
        if self.options['line_separator'] == 'Carriage Return':
            self.line_separator = [13]
            self.separators = 1
        elif self.options['line_separator'] == 'Line Feed':
            self.line_separator = [10]
            self.separators = 1
        elif self.options['line_separator'] == 'CR + LF':
            self.line_separator = [13, 10]
            self.separators = 2
        else:
            self.line_separator = [10, 13]
            self.separators = 2

        self.out_ann = self.register(srd.OUTPUT_ANN)

    def format_value(self, v):
        if v in range(32, 126 + 1):
            return chr(v)
        return "<{:02X}>".format(v)

    def putw(self, ss, es, rxtx):
        ann = rxtx
        message = self.text[rxtx]
        self.put(ss, es, self.out_ann, [ann, [message]])

    # This is the list of <ptype>s and their respective <pdata> values:
    # - 'STARTBIT': The data is the (integer) value of the start bit (0/1).
    # - 'DATA': This is always a tuple containing two items:
    # - 1st item: the (integer) value of the UART data. Valid values
    # range from 0 to 511 (as the data can be up to 9 bits in size).
    # - 2nd item: the list of individual data bits and their ss/es numbers.
    # - 'PARITYBIT': The data is the (integer) value of the parity bit (0/1).
    # - 'STOPBIT': The data is the (integer) value of the stop bit (0 or 1).
    # - 'INVALID STARTBIT': The data is the (integer) value of the start bit (0/1).
    # - 'INVALID STOPBIT': The data is the (integer) value of the stop bit (0/1).
    # - 'PARITY ERROR': The data is a tuple with two entries. The first one is
    # the expected parity value, the second is the actual parity value.
    # - 'BREAK': The data is always 0.
    # - 'FRAME': The data is always a tuple containing two items: The (integer)
    # value of the UART data, and a boolean which reflects the validity of the
    # UART frame.
    def decode(self, ss, es, data):
        ptype, rxtx, pdata = data

        if ptype == 'FRAME':
            value, valid = pdata
            # self.put(ss, es, self.out_ann,
            #          # [0, ["%s %d %s %d" % (ptype, value, self.text[rxtx], self.separator_idx[rxtx])]])
            #          [0, ["%s %d" % (ptype, value)]])
            if (self.text[rxtx] == "") and (self.separator_idx[rxtx] == 0):
                # self.put(ss, es, self.out_ann, [0, ["SSS"]])
                self.text_start[rxtx] = ss
            if value == self.line_separator[self.separator_idx[rxtx]]:
                self.separator_idx[rxtx] += 1
                if self.separator_idx[rxtx] == self.separators:
                    self.putw(self.text_start[rxtx], es, rxtx)
                    self.text[rxtx] = ""
                    self.separator_idx[rxtx] = 0
            else:
                if self.separator_idx[rxtx] > 0:
                    self.text[rxtx] = self.text[rxtx] + self.format_value(self.line_separator[0])
                    self.separator_idx[rxtx] = 0
                self.text[rxtx] = self.text[rxtx] + self.format_value(value)
        # else:
        #     self.put(ss, es, self.out_ann, [0, [ptype]])
