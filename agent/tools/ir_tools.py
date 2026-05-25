def build_samsung_raw(hex_code: str) -> list[int]:
    code = int(hex_code, 16)

    def encode_frame():
        frame = [4500, 4500]
        for i in range(31, -1, -1):
            bit = (code >> i) & 1
            frame.append(560)
            frame.append(1690 if bit else 560)
        frame.append(560)
        return frame

    return encode_frame() + [46612] + encode_frame()
