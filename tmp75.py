import smbus


class TMP75:
    i2c_ch = 1

    # TMP102 address on the I2C bus
    i2c_address = 0x48

    # Register addresses
    reg_temp = 0x00
    reg_config = 0x01

    def __init__(self):
        self.bus = smbus.SMBus(self.i2c_ch)

        val = self.bus.read_i2c_block_data(self.i2c_address, self.reg_config, 2)

        # Set to 4 Hz sampling (CR1, CR0 = 0b10)
        val[1] = val[1] & 0b00111111
        val[1] = val[1] | (0b10 << 6)

        # Write 4 Hz sampling back to CONFIG
        self.bus.write_i2c_block_data(self.i2c_address, self.reg_config, val)

        # Read CONFIG to verify that we changed it
        val = self.bus.read_i2c_block_data(self.i2c_address, self.reg_config, 2)

    # Calculate the 2's complement of a number
    @staticmethod
    def twos_comp(val, bits):
        if (val & (1 << (bits - 1))) != 0:
            val = val - (1 << bits)
        return val

    # Read temperature registers and calculate Celsius
    def read_temp(self):
        # Read temperature registers
        val = self.bus.read_i2c_block_data(self.i2c_address, self.reg_temp, 2)
        # NOTE: val[0] = MSB byte 1, val [1] = LSB byte 2
        # print ("!shifted val[0] = ", bin(val[0]), "val[1] = ", bin(val[1]))

        temp_c = (val[0] << 4) | (val[1] >> 4)
        # print (" shifted val[0] = ", bin(val[0] << 4), "val[1] = ", bin(val[1] >> 4))
        # print (bin(temp_c))

        # Convert to 2s complement (temperatures can be negative)
        temp_c = self.twos_comp(temp_c, 12)

        # Convert registers value to temperature (C)
        temp_c = temp_c * 0.0625

        return temp_c
