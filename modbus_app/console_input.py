from modbus_communication import bit_to_int, set_updated_bits_callback, write_to_register

def user_input():
    while True:
        user_input_value = input("Enter up to 16 bits (e.g. 1010101010101010): ")
        if not all(bit in '01' for bit in user_input_value) or len(user_input_value) > 16:
            print("Invalid input. Please enter a valid 16-bit binary number.")
            continue
        bin_list = [int(bit) for bit in user_input_value.zfill(16)]
        value = bit_to_int(bin_list)
        write_to_register(bin_list)
        print(f"{value} written.")
        print(f"{bin_list} written to the register 0.\n")

def display_updated_bits(bits):
    print(f"\nUpdated bits: {bits}")
    print("Enter Bits: ")

if __name__ == "__main__":
    set_updated_bits_callback(display_updated_bits)
    user_input()
