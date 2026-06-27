class Assembler:
    def __init__(self):
        self.labels = {}
        self.opcodes = {
            # Data transfer
            'LDI': 0x00, 'TRA': 0x01, 'LDM': 0x02, 'LDZP': 0x03,
            'STM': 0x04, 'STZP': 0x05, 'LDIND': 0x06, 'STIND': 0x07,
            'PSH': 0x08, 'POP': 0x09,
            # Arithmetic
            'ADD': 0x10, 'SUB': 0x11, 'MUL': 0x12, 'DIV': 0x13,
            'MOD': 0x14, 'AND': 0x15, 'OR': 0x16, 'NOT': 0x17,
            'NAND': 0x18, 'NOR': 0x19, 'XOR': 0x1A, 'XNOR': 0x1B,
            'SHL': 0x1C, 'SHR': 0x1D,
            # Flow control
            'JMP': 0x20, 'JSR': 0x21, 'RTS': 0x22,
            'BEQ': 0x23, 'BNE': 0x24, 'BGT': 0x25, 'BLT': 0x26,
            'BGE': 0x27, 'BLE': 0x28, 'JMPI': 0x29,
            # Special
            'WPX': 0xF0, 'HLT': 0xFF
        }
        
    def _parse_reg(self, token):
        """Parse R0-R15 into integer 0-15"""
        if token.startswith('R') or token.startswith('r'):
            reg = int(token[1:])
            if 0 <= reg <= 15:
                return reg
        raise ValueError(f"Invalid register: {token}")
    
    def _parse_number(self, token):
        """Parse decimal, hex, or label reference"""
        token = token.strip()
        if token in self.labels:
            return self.labels[token]
        elif token.startswith('0x') or token.startswith('0X'):
            return int(token, 16)
        elif token.startswith('$'):
            return int(token[1:], 16)
        else:
            try:
                return int(token)
            except ValueError:
                raise ValueError(f"Undefined label or invalid number: {token}")
    
    def _instruction_size(self, line):
        """Return byte size of an instruction"""
        parts = line.replace(',', ' ').split()
        if not parts:
            return 0
        mnemonic = parts[0].upper()
        
        if mnemonic == 'HLT':
            return 1
        elif mnemonic == 'RTS':
            return 1
        elif mnemonic in ['TRA', 'NOT']:
            return 2
        elif mnemonic == 'LDI':
            return 3
        elif mnemonic in ['LDZP', 'STZP']:
            return 3
        elif mnemonic in ['LDIND', 'STIND', 'WPX']:
            return 3
        elif mnemonic in ['LDM', 'STM']:
            return 4
        elif mnemonic in ['ADD', 'SUB', 'MUL', 'DIV', 'MOD', 
                          'AND', 'OR', 'NAND', 'NOR', 'XOR', 'XNOR', 
                          'SHL', 'SHR']:
            return 3
        elif mnemonic in ['JMP', 'JSR']:
            return 3
        elif mnemonic in ['BEQ', 'BNE', 'BGT', 'BLT', 'BGE', 'BLE']:
            return 4
        elif mnemonic == 'JMPI':
            return 2
        elif mnemonic in ['PSH', 'POP']:
            return 2
        else:
            raise ValueError(f"Unknown instruction: {mnemonic}")
    
    def assemble(self, source, base_addr=0x2000):
        """Convert assembly source to machine code bytes"""
        # Clean and separate lines
        lines = []
        for line in source.strip().split('\n'):
            # Remove comments
            if ';' in line:
                line = line[:line.index(';')]
            line = line.strip()
            if line:
                lines.append(line)
        
        # Pass 1: Find labels
        addr = base_addr
        for line in lines:
            if line.endswith(':'):
                label = line[:-1]
                self.labels[label] = addr
            else:
                addr += self._instruction_size(line)
        
        addr = base_addr
        for line in lines:
            if line.endswith(':'):
                label = line[:-1]
                self.labels[label] = addr
                print(f"Label {label} at 0x{addr:04X}")
            else:
                size = self._instruction_size(line)
                print(f"  {line[:40]:40s} -> {size} bytes, addr 0x{addr:04X}")
                addr += size
        
        # Pass 2: Generate machine code
        addr = base_addr
        output = []
        
        for line in lines:
            if line.endswith(':'):
                continue  # Skip label-only lines
            
            parts = line.replace(',', ' ').split()
            mnemonic = parts[0].upper()
            try:
                if mnemonic == 'HLT':
                    output.append(0xFF)
                    addr += 1
                    
                elif mnemonic == 'RTS':
                    output.append(0x22)
                    addr += 1
                    
                elif mnemonic == 'LDI':
                    # LDI Rdst, imm
                    dst = self._parse_reg(parts[1])
                    imm = self._parse_number(parts[2])
                    output.append(0x00)
                    output.append((dst << 4) & 0xF0)
                    output.append(imm & 0xFF)
                    addr += 3
                    
                elif mnemonic == 'TRA':
                    # TRA Rdst, Rsrc
                    dst = self._parse_reg(parts[1])
                    src = self._parse_reg(parts[2])
                    output.append(0x01)
                    output.append(((dst << 4) & 0xF0) | (src & 0x0F))
                    addr += 2
                    
                elif mnemonic == 'LDM':
                    # LDM Rdst, addr
                    dst = self._parse_reg(parts[1])
                    target = self._parse_number(parts[2])
                    output.append(0x02)
                    output.append((dst << 4) & 0xF0)
                    output.append(target & 0xFF)
                    output.append((target >> 8) & 0xFF)
                    addr += 4
                    
                elif mnemonic == 'LDZP':
                    # LDZP Rdst, zp_addr
                    dst = self._parse_reg(parts[1])
                    zp = self._parse_number(parts[2])
                    output.append(0x03)
                    output.append((dst << 4) & 0xF0)
                    output.append(zp & 0xFF)
                    addr += 3
                    
                elif mnemonic == 'STM':
                    # STM Rsrc, addr
                    src = self._parse_reg(parts[1])
                    target = self._parse_number(parts[2])
                    output.append(0x04)
                    output.append(src & 0x0F)
                    output.append(target & 0xFF)
                    output.append((target >> 8) & 0xFF)
                    addr += 4
                    
                elif mnemonic == 'STZP':
                    # STZP Rsrc, zp_addr
                    src = self._parse_reg(parts[1])
                    zp = self._parse_number(parts[2])
                    output.append(0x05)
                    output.append(src & 0x0F)
                    output.append(zp & 0xFF)
                    addr += 3
            
                elif mnemonic == 'LDIND':
                    # LDIND Rdst, Raddr_high, Raddr_low
                    dst = self._parse_reg(parts[1])
                    reg_high = self._parse_reg(parts[2])
                    reg_low = self._parse_reg(parts[3])
                    output.append(0x06)
                    output.append(((dst << 4) & 0xF0) | (reg_high & 0x0F))
                    output.append(reg_low & 0x0F)
                    addr += 3
                    
                elif mnemonic == 'STIND':
                    # STIND Rsrc, Raddr_high, Raddr_low
                    src = self._parse_reg(parts[1])
                    reg_high = self._parse_reg(parts[2])
                    reg_low = self._parse_reg(parts[3])
                    output.append(0x07)
                    output.append(((src << 4) & 0xF0) | (reg_high & 0x0F))
                    output.append(reg_low & 0x0F)
                    addr += 3
                
                elif mnemonic == 'PSH':
                    reg = self._parse_reg(parts[1])
                    output.append(0x08)
                    output.append(reg & 0x0F)
                    addr += 2
                
                elif mnemonic == 'POP':
                    reg = self._parse_reg(parts[1])
                    output.append(0x09)
                    output.append(reg & 0x0F)
                    addr += 2
                    
                elif mnemonic in ['ADD', 'SUB', 'DIV', 'MOD',
                                  'AND', 'OR', 'NAND', 'NOR', 'XOR', 'XNOR']:
                    # OP Rdst, Rsrc1, Rsrc2
                    dst = self._parse_reg(parts[1])
                    src1 = self._parse_reg(parts[2])
                    src2 = self._parse_reg(parts[3])
                    output.append(self.opcodes[mnemonic])
                    output.append((dst << 4) & 0xF0)
                    output.append(((src2 << 4) & 0xF0) | (src1 & 0x0F))
                    addr += 3
            
                elif mnemonic == 'MUL':
                    # MUL Rdst_high, Rdst_low, Rsrc1, Rsrc2
                    dst1 = self._parse_reg(parts[1])
                    dst2 = self._parse_reg(parts[2])
                    src1 = self._parse_reg(parts[3])
                    src2 = self._parse_reg(parts[4])
                    output.append(self.opcodes[mnemonic])
                    output.append(((dst1 << 4) & 0xF0) | (dst2 & 0x0F))
                    output.append(((src2 << 4) & 0xF0) | (src1 & 0x0F))
                    addr += 3
                
                elif mnemonic in ['SHL', 'SHR']:
                    dst = self._parse_reg(parts[1])
                    src = self._parse_reg(parts[2])
                    amount = self._parse_reg(parts[3])
                    output.append(self.opcodes[mnemonic])
                    output.append((dst << 4) & 0xF0)
                    output.append(((amount << 4) & 0xF0) | (src & 0x0F))
                    addr += 3
                    
                elif mnemonic in ['JMP', 'JSR']:
                    # JMP/JSR addr
                    target = self._parse_number(parts[1])
                    output.append(self.opcodes[mnemonic])
                    output.append(target & 0xFF)
                    output.append((target >> 8) & 0xFF)
                    addr += 3
                    
                elif mnemonic in ['BEQ', 'BNE', 'BGT', 'BLT', 'BGE', 'BLE']:
                    # Bxx R1, R2, addr
                    reg1 = self._parse_reg(parts[1])
                    reg2 = self._parse_reg(parts[2])
                    target = self._parse_number(parts[3])
                    output.append(self.opcodes[mnemonic])
                    output.append(((reg1 << 4) & 0xF0) | (reg2 & 0x0F))
                    output.append(target & 0xFF)
                    output.append((target >> 8) & 0xFF)
                    addr += 4
                
                elif mnemonic == 'JMPI':
                    reg_high = self._parse_reg(parts[1])
                    reg_low = self._parse_reg(parts[2])
                    output.append(0x29)
                    output.append(((reg_high << 4) & 0xF0) | (reg_low & 0x0F))
                    addr += 2
                
                elif mnemonic == 'WPX':
                    color_reg = self._parse_reg(parts[1])
                    x_reg = self._parse_reg(parts[2])
                    y_reg = self._parse_reg(parts[3])
                    output.append(self.opcodes[mnemonic])
                    output.append(((color_reg << 4) & 0xF0) | (x_reg & 0x0F))
                    output.append((y_reg<<4) & 0xF0)
                    addr += 3
            except ValueError as ve:
                print("Value error raised. Contents:")
                print(ve)
                print(f"This happened at line {line}.")
        
        return output

import sys

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python assembler.py program.asm [base_address] [output.bin]")
        print("  base_address: hex address (default 0x2000)")
        sys.exit(1)
    
    input_file = sys.argv[1]
    base_addr = 0x2000
    if len(sys.argv) > 2:
        base_addr = int(sys.argv[2], 16)  # Parse hex
    
    output_file = sys.argv[3] if len(sys.argv) > 3 else input_file.replace('.asm', '.bin')
    
    with open(input_file, 'r') as f:
        source = f.read()
    
    assembler = Assembler()
    binary = assembler.assemble(source, base_addr)  # Pass base_addr!
    
    # Print hex dump
    for i, byte in enumerate(binary):
        if i % 16 == 0:
            print(f"\n{i:04X}: ", end="")
        print(f"{byte:02X} ", end="")
    print(f"\n\nTotal bytes: {len(binary)}")
    
    # Print labels
    print("\nLabels:")
    for label, addr in sorted(assembler.labels.items()):
        print(f"  {label}: 0x{addr:04X}")
    
    # Save binary file
    with open(output_file, 'wb') as f:
        f.write(bytes(binary))
    print(f"\nSaved binary to {output_file}")
    
    # Also print paste-ready hex for Wozmon
    base = assembler.labels.get('start', 0x2000)
    print(f"\nPaste-ready for Wozmon (base 0x{base:04X}):")
    for i in range(0, len(binary), 16):
        chunk = binary[i:i+16]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        addr = base + i
        print(f"{hex_str}")
