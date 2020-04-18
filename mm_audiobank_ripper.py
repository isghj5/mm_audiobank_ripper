#!/usr/bin/env python3

# Apr 2020 Isghj

# This script reads a modified Majora's Mask U0 (decompressed) rom 
#  and extracts the individual instrument sets from the audiobank
# along with the metadata from the audiobank index table (instrument count, percussion, other data)
#  this was created because Seq64 only extracts instrument sets as xml to include both as one file
#  and I hate XML parsing, just shove the binary, its easier

# more info MMR discord: https://discord.gg/8qbreUM

import binascii
import sys
import os
from time import strftime

# ref: https://docs.google.com/spreadsheets/d/1J-4OwmZzOKEv2hZ7wrygOpMm0YcRnephEo3Q2FooF6E/edit#gid=56702767
audiobank_table_loc = 0xc776c0
audiobank_loc       = 0x20700
audiobank_table_len = 0x2a0     # currently seq64 cannot increase this, assume vanilla size
audioseq_table_loc  = 0xC77B70
audioseq_loc        = 0x46AF0
audioseq_table_len  = 0x810

vanilla_bank_sizes = [33216, 14032, 3296, 5584, 2912, 3040, 4032, 1776, 1376, 3264, 2720, 2656, 3056, 1216, 3072, 3552, 1632, 5328, 3152, 4432, 1312, 1904, 1280, 2368, 2112, 5184, 768, 2784, 1776, 1456, 2064, 1312, 4080, 5600, 208, 5296, 5136, 5440, 912, 1312, 1008]
vanilla_seq_sizes = [50848, 4032, 6912, 1696, 2688, 2832, 3120, 4800, 368, 416, 2192, 2320, 3584, 1648, 3072, 448, 3312, 3392, 2960, 3136, 3392, 3728, 2240, 2208, 1232, 912 , 5744, 7728, 2992, 1552, 3168, 1392, 432, 1584, 336, 0, 560, 2208, 2736, 2512, 0, 2560, 1280, 1104, 864, 1632, 4128, 9616, 2592, 1872, 384, 176, 368, 272, 4512, 656, 6960, 448, 1952, 320, 4752, 528, 2384, 592, 6784, 1632, 6864, 2752, 3776, 1824, 3600, 304, 224, 336, 368, 1920, 2400, 2304, 1568, 1040, 704, 208, 992, 800, 1392, 1152, 0, 3280, 352, 128, 144, 272, 272, 288, 208, 208, 0, 0, 320, 656, 1712, 3872, 4128, 16, 16, 7552, 4064, 4384, 288, 384, 576, 3712, 3520, 624, 4192, 1056, 9056, 3152, 6976, 704, 848, 1120, 16, 3440, 1888, 1552, 1728, 12896]

if len(sys.argv) < 2:
  print("usage: python3 mm_bankripper.py decompressed_majoramask_USA.z64")
  sys.exit(1)

# load mm rom input
try:
  rom = open(sys.argv[1], "rb")
except FileNotFoundError:
  print("could not find file")

# make new folder with timestamp sorting
output_dir = strftime("%Y-%m-%d_%H%M")
if not os.path.exists(output_dir):
  os.makedirs(output_dir)
output_dir += "/"

# load mm audiobanktable
rom.seek(audiobank_table_loc)
audiobank_table = rom.read(audiobank_table_len )  

# debugging: check to make sure the table is in the right place
hexified_table_data = binascii.hexlify(audiobank_table)
if hexified_table_data[0:8] == b'00290000':
  print("Bank index found at regular location, extracting...")
else:
  print("WARNING: good chance the audiobank index table was moved to a different location")

# extract banks and meta
# starting with 16 because the first line is just 00 29 00 00 and 00 padding to the end of line
# I don't think that modifies anything else, don't see anything in the xml about it
bank_index = 0
audiobank_table_dmaspaced = [audiobank_table[i:i+16] for i in range(16, len(audiobank_table), 16)]
for dma in audiobank_table_dmaspaced:
  # four words(4x4 bytes): index address, length, and two words of metadata
  address  = int.from_bytes(dma[0:4], byteorder="big")
  length   = int.from_bytes(dma[4:8], byteorder="big")
  if vanilla_bank_sizes[bank_index] != length:
    metadata = dma[8:16]
    bank_index_hex = hex(bank_index).lstrip("0x").zfill(2)
    file_name = output_dir + bank_index_hex
    print("Bank " + bank_index_hex + " is located at " + hex(audiobank_loc + address))
    print(" size: " + str(length))

    outfile = open(file_name + ".zbank", 'wb')
    rom.seek( audiobank_loc + address)
    outfile.write(rom.read(length))
    outfile.close()
    outfile = open(file_name + ".bankmeta", 'wb')
    outfile.write(metadata)
    outfile.close()
  bank_index += 1

# might as well extract the sequences too, that would make it one less step to extrac custom audiobanks
rom.seek(audioseq_table_loc)
audioseq_table = rom.read(audioseq_table_len)

# skipping the first two because we don't use them, and they shrink if we use compact in seq64, so they just add clutter
seq_index = 2
audioseq_table_dmaspaced = [audioseq_table[i:i+16] for i in range(48, len(audioseq_table), 16)]
for dma in audioseq_table_dmaspaced:
  address = int.from_bytes(dma[0:4], byteorder="big")
  length  = int.from_bytes(dma[4:8], byteorder="big")
  if vanilla_seq_sizes[seq_index] != length:
    seq_index_hex = hex(seq_index).lstrip("0x").zfill(2)
    file_name = output_dir + seq_index_hex
    print("Seq " + seq_index_hex + " is located at " + hex(audioseq_loc + address))
    print(" size: " + str(length))

    outfile = open(file_name + ".zseq", 'wb')
    rom.seek( audioseq_loc + address)
    outfile.write(rom.read(length))
    outfile.close()
  seq_index += 1


print("Extraction complete in folder " + output_dir + ".")
