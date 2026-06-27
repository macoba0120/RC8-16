start:
    ; Constants
    LDI R10, 1         ; One
    LDI R11, 0x08      ; Backspace
    LDI R12, 0x0A      ; LF
    LDI R13, 0x0D      ; CR
    LDI R14, 0x3A      ; ':'
    LDI R15, 0         ; Zero

reset:
    LDI R0, 0x4F       ; 'O'
    STZP R0, 0x05
    LDI R0, 0x4B       ; 'K'
    STZP R0, 0x05
    LDI R0, 0x0A
    STZP R0, 0x05
    LDI R0, 0x5C
    STZP R0, 0x05
    JSR read_line
    
    ; Parse first hex value
    JSR parse_first
    BEQ R0, R15, reset ; Empty line
    
    ; Check command type
    LDI R2, 0x80
    JSR skip_hex       ; Advance past 4 hex digits
    LDI R1, 0x00
    LDIND R3, R1, R2   ; Get delimiter
    
    ; Check for '.'
    LDI R4, 0x2E       ; '.'
    BEQ R3, R4, do_xam
    
    ; Check for ':'
    LDI R4, 0x3A       ; ':'
    BEQ R3, R4, do_stor
    
    ; Check for 'R'
    LDI R4, 0x52       ; 'R'
    BEQ R3, R4, do_run
    
    JMP reset

do_run:
    LDZP R0, 0x70      ; Low byte first
    LDZP R1, 0x71      ; High byte
    
    ; Print address for debugging
    PSH R1             ; Push high byte
    PSH R0             ; Push low byte
    TRA R3, R1
    JSR print_hex
    POP R3             ; Get low byte back
    JSR print_hex
    LDI R3, 0x0A
    STZP R3, 0x05
    ; R0 and R1 are already correct from the LDZP instructions
    
    JMPI R1, R0        ; Jump to (R1 << 8) | R0

do_stor:
    ; Set mode = STOR
    LDI R0, 1
    STZP R0, 0x74
    
    ; Copy parsed address to store pointer
    LDZP R0, 0x70
    LDZP R1, 0x71
    STZP R0, 0x72
    STZP R1, 0x73
    
    ; Parse and store bytes
    ADD R2, R2, R10    ; Skip ':'
    JSR parse_store_bytes
    JMP reset

do_xam:
    STZP R15, 0x74
    ADD R2, R2, R10
    JSR parse_hex4_at
    ; NO DEBUG - just store the result!
    STZP R1, 0x73
    STZP R0, 0x72
    JSR xam_display
    JMP reset

; ---- Read line into buffer at 0x80 ----
read_line:
    PSH R1
    PSH R2
    PSH R3
    PSH R4
    
    LDI R0, 0
    LDI R1, 0x00
    LDI R2, 0x80

read_loop:
    JSR get_char
    BEQ R3, R13, read_loop  ; CR
    BEQ R3, R12, read_done  ; LF
    BEQ R3, R11, read_bs
    
    LDI R4, 0x20
    BLT R3, R4, read_loop
    
    JSR put_char
    STIND R3, R1, R2
    ADD R2, R2, R10
    ADD R0, R0, R10
    JMP read_loop

read_bs:
    BEQ R0, R15, read_loop
    SUB R0, R0, R10
    SUB R2, R2, R10
    STZP R11, 0x05
    LDI R4, 0x20
    STZP R4, 0x05
    STZP R11, 0x05
    JMP read_loop

read_done:
    STIND R15, R1, R2   ; Null terminate
    STZP R12, 0x05
    POP R4
    POP R3
    POP R2
    POP R1
    RTS

; ---- Serial I/O ----
get_char:
    PSH R0
get_wait:
    LDZP R0, 0x04
    AND R0, R0, R10
    BEQ R0, R15, get_wait
    LDZP R3, 0x05
    POP R0
    RTS

put_char:
    STZP R3, 0x05
    RTS

; ---- Parse first hex value from buffer, store in 0x70-0x71 ----
; Returns R0 = 0 if empty, 1 if value parsed
parse_first:
    LDZP R3, 0x80
    LDI R4, 0x20
    BLT R3, R4, parse_empty
    
    JSR parse_hex4
    ; Debug: print R1:R0
    PSH R0
    TRA R3, R1
    JSR print_hex
    POP R3
    JSR print_hex
    LDI R3, 0x0A
    STZP R3, 0x05
    ; End debug
    STZP R1, 0x71
    STZP R0, 0x70
    LDI R0, 1
    RTS

parse_empty:
    LDI R0, 0
    RTS

; ---- Parse 4 hex digits from buffer start into R1:R0 ----
parse_hex4:
    PSH R2
    LDI R2, 0x80
    JSR parse_hex4_at
    POP R2
    RTS

; ---- Parse 4 hex digits from buffer[R2] into R1:R0 ----
; Advances R2 by 4
parse_hex4_at:
    PSH R3
    PSH R4
    PSH R5
    PSH R6
    PSH R8
    
    LDI R1, 0          ; Result high
    LDI R0, 0          ; Result low
    LDI R5, 4          ; Shift amount
    LDI R6, 0x00       ; Buffer high
    LDI R8, 4

hex4_loop:
    LDIND R3, R6, R2
    JSR hex_to_nibble
    LDI R4, 16
    BGE R3, R4, hex4_done   ; If R3 >= 16, not valid hex - stop!
    
    ; R1:R0 = (R1:R0 << 4) | R3
    SHR R4, R0, R5     ; R4 = old high nibble of R0
    LDI R7, 0x0F
    AND R4, R4, R7     ; Mask
    SHL R1, R1, R5     ; R1 <<= 4
    OR R1, R1, R4      ; R1 gets old high nibble of R0
    SHL R0, R0, R5     ; R0 <<= 4
    OR R0, R0, R3      ; R0 gets new digit
    
    ADD R2, R2, R10
    SUB R8, R8, R10
    BGT R8, R15, hex4_loop

hex4_done:
    POP R8
    POP R6
    POP R5
    POP R4
    POP R3
    RTS

; ---- Parse 2 hex digits at buffer[R2] into R0 ----
; Advances R2 by 2
parse_hex2:
    PSH R1
    PSH R3
    PSH R4
    PSH R5
    
    LDI R5, 4          ; Shift amount
    
    LDIND R3, R1, R2
    JSR hex_to_nibble
    SHL R0, R3, R5     ; R0 = nibble << 4
    
    ADD R2, R2, R10
    LDIND R3, R1, R2
    JSR hex_to_nibble
    OR R0, R0, R3
    
    ADD R2, R2, R10
    
    POP R5
    POP R4
    POP R3
    POP R1
    RTS

; ---- Convert ASCII hex to nibble ----
hex_to_nibble:
    ; Check if digit '0'-'9'
    LDI R4, 0x30
    BLT R3, R4, hex_bad
    LDI R4, 0x3A       ; '9' + 1
    BLT R3, R4, hex_digit
    
    ; Check if uppercase 'A'-'F'
    LDI R4, 0x41
    BLT R3, R4, hex_bad
    LDI R4, 0x47       ; 'F' + 1
    BLT R3, R4, hex_alpha
    
hex_bad:
    LDI R3, 0xFF       ; Return invalid marker
    RTS

hex_digit:
    LDI R4, 0x30
    SUB R3, R3, R4
    RTS

hex_alpha:
    LDI R4, 0x37
    SUB R3, R3, R4
    RTS

; ---- Skip 4 hex digits (advance R2 by 4) ----
skip_hex:
    ADD R2, R2, R10
    ADD R2, R2, R10
    ADD R2, R2, R10
    ADD R2, R2, R10
    RTS

; ---- Parse and store bytes: "XX XX XX..." ----
parse_store_bytes:
    PSH R0
    PSH R1
    PSH R2
    PSH R3
    PSH R4
    PSH R5
    PSH R6
    
    LDI R1, 0x00       ; Buffer high
    
store_loop:
    ; Skip spaces
    LDIND R3, R1, R2
    LDI R4, 0x20
    BNE R3, R4, store_check
    ADD R2, R2, R10
    JMP store_loop

store_check:
    ; End if non-hex
    LDI R4, 0x30
    BLT R3, R4, store_done
    
    ; Parse byte
    JSR parse_hex2
    ; R0 = byte value
    
    ; Store to memory
    LDZP R5, 0x73      ; High
    LDZP R6, 0x72      ; Low
    STIND R0, R5, R6
    
    ; Increment address
    ADD R6, R6, R10
    STZP R6, 0x72
    ; Assume no carry
    
    JMP store_loop

store_done:
    POP R6
    POP R5
    POP R4
    POP R3
    POP R2
    POP R1
    POP R0
    RTS

; ---- Display memory from (0x70) to (0x72) ----
xam_display:
    PSH R0
    PSH R1
    PSH R2
    PSH R3
    PSH R4
    PSH R5
    PSH R6
    PSH R7
    LDZP R6, 0x70
    LDZP R7, 0x71
    LDZP R4, 0x72
    LDZP R5, 0x73
    
    ; Debug: print R7:R6 and R5:R4
    TRA R3, R7
    JSR print_hex
    TRA R3, R6
    JSR print_hex
    LDI R3, 0x2D       ; '-'
    STZP R3, 0x05
    TRA R3, R5
    JSR print_hex
    TRA R3, R4
    JSR print_hex
    LDI R3, 0x0A
    STZP R3, 0x05

dump_line:
    ; Print address
    TRA R3, R7
    JSR print_hex
    TRA R3, R6
    JSR print_hex
    LDI R3, 0x3A       ; ':'
    STZP R3, 0x05
    
    LDI R2, 0          ; Reset column counter

dump_byte:
    ; Check if done
    BGT R7, R5, dump_done
    BEQ R7, R5, check_low_dump
    JMP dump_read

check_low_dump:
    ; BGT R6, R4, dump_done
    JMP dump_read

dump_read:
    ; Read byte at (R7:R6)
    LDI R0, 0x00
    LDIND R3, R7, R6   ; R3 = memory value
    
    ; Print byte
    PSH R6
    PSH R7
    JSR print_hex
    POP R7
    POP R6
    
    ; Increment address
    ADD R6, R6, R10
    BEQ R6, R15, inc_high
    JMP next_byte

inc_high:
    ADD R7, R7, R10

next_byte:
    ; Check if we need a newline
    ADD R2, R2, R10
    LDI R3, 16
    BEQ R2, R3, newline
    LDI R3, 0x20       ; Space
    STZP R3, 0x05
    JMP dump_byte

newline:
    LDI R3, 0x0A
    STZP R3, 0x05
    JMP dump_line

dump_done:
    LDI R3, 0x0A
    STZP R3, 0x05
    
    POP R7
    POP R6
    POP R5
    POP R4
    POP R3
    POP R2
    POP R1
    POP R0
    RTS

; ---- Print byte in R3 as 2 hex digits ----
print_hex:
    PSH R0
    PSH R1
    PSH R3
    PSH R4
    
    LDI R4, 4
    SHR R0, R3, R4     ; R0 = high nibble
    TRA R1, R0         ; R1 = high nibble
    JSR print_nibble   ; Prints R1
    
    LDI R4, 0x0F
    AND R1, R3, R4     ; R1 = low nibble
    JSR print_nibble   ; Prints R1
    
    POP R4
    POP R3
    POP R1
    POP R0
    RTS

print_nibble:
    PSH R1
    PSH R4
    
    LDI R4, 10
    BLT R1, R4, is_digit
    LDI R4, 7
    ADD R1, R1, R4     ; 'A' - 10 = 0x37 - 0x30 = 7
    
is_digit:
    LDI R4, 0x30
    ADD R1, R1, R4     ; + '0'
    STZP R1, 0x05
    
    POP R4
    POP R1
    RTS
