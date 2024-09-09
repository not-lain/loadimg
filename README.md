# loadimg

[![Downloads](https://static.pepy.tech/badge/loadimg)](https://pepy.tech/project/loadimg)

A python package for loading images

## How to use
Installation
```
pip install loadimg
```
Usage
```python
from loadimg import load_img
load_img(any_img_type_here,output_type="pil",input_type="auto") 
```
Supported types
- Currently supported input types - numpy, pillow, str(both path and url), base64, **auto**
- Currently supported output types - numpy, pillow, str, base64

![loadimg](https://github.com/not-lain/loadimg/blob/main/loadimg.png?raw=true)

## Contributions

- [x] thanks to [@KingNish24](https://github.com/KingNish24) for improving base64 support and adding the `input_type` parameter
- [x] thanks to [@Saptarshi-Bandopadhyay](https://github.com/Saptarshi-Bandopadhyay) for supporting base64 and improving the docstrings
- [x] thanks to [@Abbhiishek](https://github.com/Abbhiishek) for improving image naming

<a href="https://github.com/not-lain/loadimg/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=not-lain/loadimg" />
</a>
