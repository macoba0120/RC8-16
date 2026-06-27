import sys

if len(sys.argv) < 3:
    print("Usage: python write.py input.bin base_hex output.bin")
    sys.exit(1)

input_file = sys.argv[1]
base_addr = int(sys.argv[2], 16)  # Parse hex address
output_file = sys.argv[3]

# Read the program bytes
with open(input_file, "rb") as f:
    program_bytes = f.read()

# Calculate ROM offset (ROM starts at 0x2000)
rom_offset = base_addr

# Read existing ROM
with open(output_file, "r+b") as f:
    f.seek(rom_offset)
    f.write(program_bytes)

print(f"Written {len(program_bytes)} bytes to {output_file} at offset 0x{rom_offset:04X} (address 0x{base_addr:04X})")
