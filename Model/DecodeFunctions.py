__author__ = 'benradosevich'


def decode_obd_data(command, response_list):
    return {
        '010D': speed,
        '0110': maf
    }[command](response_list)


def speed(response_list):
    a = int(response_list[0], 16)
    return float(a)


def maf(response_list):
    a = int(response_list[0], 16)
    b = int(response_list[1], 16)
    return ((a * 256) + b)/100.0

