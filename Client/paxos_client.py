from PIL import Image


def __average_hash__(image_path, hash_size=8):
        """ Compute the average hash of the given image. """
        # print(image_path)
        with open(image_path, 'rb') as f:
            # Open the image, resize it and convert it to black & white.
            image = Image.open(f).resize((hash_size, hash_size), Image.ANTIALIAS).convert('L')
            pixels = list(image.getdata())

        avg = sum(pixels) / len(pixels)

        # Compute the hash based on each pixels value compared to the average.
        bits = "".join(map(lambda pixel: '1' if pixel > avg else '0', pixels))
        hashformat = "0{hashlength}x".format(hashlength=hash_size ** 2 // 4)
        return int(bits, 2).__format__(hashformat)


while True:
    inp = input(">> ")
    if inp=="quit":
        break
    elif (inp.split(" ")[0]=="iget") or (inp.split(" ")[0]=="iset"):
        a=inp.split(" ")
        a[1]=__average_hash__(a[1])
        command=" ".join(a[1:])
    else:
        command=" ".join(inp.split(" ")[1:])
    print(command)
