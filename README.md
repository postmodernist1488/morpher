# morpher
Morph one closed (filled) shape into another.

![example](https://github.com/postmodernist1488/morpher/assets/101038833/93748b50-5813-4e87-8154-54457e9b7782)

Inspired by my friend asking whether generation of [such images](https://www.reddit.com/r/MapPorn/comments/wlzqiz/from_iceland_to_ireland) could be automated.

You need to provide two png images like the examples:
```
$ ./morpher.py iceland.png ireland.png -o ice_to_ir.gif
```
You can change the number of frames generated and the duration of the GIF:
```
$ ./morpher.py iceland.png ireland.png -n50 --duration=3
```
You can also generate frames in PNG and JPEG formats:
```
$ ./morpher.py shape1.png shape2.png -n50 -fpng -o png/
$ ./morpher.py shape1.png shape2.png -n50 -fjpeg -o jpeg/ 
```
For more options check the `-h` flag
