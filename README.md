# ja2zh
A single-person Japanese video can be translated into Chinese and automatically aligned according to sentences while maintaining the original tone.

### Create the Env:
```
conda create --name envname python=3.10
conda activate envname
```

### Install Package
```
conda install -y -c pytorch -c nvidia cudatoolkit
conda install -y -c conda-forge gcc gxx ffmpeg cmake -c pytorch -c nvidia
pip install -r requirements.txt
```

### Download Pre-trained Model

1. Download the [model1](https://drive.google.com/file/d/187AqdBqSEhr44cLfiV1FNxJsVEwr4GIm/view?usp=sharing) and [model2](https://drive.google.com/file/d/1OqqJj3Qo5hcfopyxtkdRhsc1Y7oEIugF/view?usp=drive_link), and then put them to the '/preprocessing/denoiseuvr5_weights'

2. Download the pre-trained model from [here](https://drive.google.com/file/d/1wTg0rchyW_WhWCrbVSKargXFf2GsllIk/view?usp=drive_link) and unzip it and put it in the pretrain folder.

### Translate the Video

1. Put the japnese video to 'product/inputvideo'

2. Run bash conversion.sh


