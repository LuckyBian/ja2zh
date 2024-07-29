declare -A dictionary
dictionary[0]="jj"

for key in "${!dictionary[@]}"; do
    mkdir -p 'product/clean'
    mkdir -p 'product/track'
    base_path1="product/track"
    base_path2="product/onlywav"
    base_path3="product/cut"
    mkdir -p "$base_path1/$key"
    mkdir -p "$base_path2/$key"
    mkdir -p "$base_path3/$key"
done

item_count=${#dictionary[@]}

stage=13

if [ $stage -le 0 ]; then
    mkdir -p 'product/nonwav_video'
    mkdir -p 'product/tmpwav'
    python product/depart.py 'product/inputvideo' 'product/nonwav_video/nonwav.mp4' 'product/tmpwav/all.wav'
fi

if [ $stage -le 1 ]; then
    mkdir -p 'product/bgm'
    mkdir -p 'product/tmpvocal'
    mkdir -p 'product/useless'
    python preprocessing/denoise/get_voice.py --model_name 'HP2-人声vocals+非人声instrumentals' --inp_root './product/tmpwav' --save_root_vocal './product/tmpvocal' --save_root_ins './product/bgm'
    python preprocessing/denoise/get_voice.py --model_name 'DeEchoAggressive' --inp_root 'product/tmpvocal' --save_root_vocal 'product/clean' --save_root_ins 'product/useless'
    folder_to_check1="/home/weizhenbian/ja2zh/product/clean"
    folder_to_check2="/home/weizhenbian/ja2zh/product/bgm"


    if [ "$(find "$folder_to_check1" -mindepth 1 | head -n 1)" ] && [ "$(find "$folder_to_check2" -mindepth 1 | head -n 1)" ]; then
        rm -rf "product/tmpvocal"
        rm -rf "product/tmpwav"
        rm -rf "product/useless"
        mv "product/bgm/instrument_all.wav.reformatted.wav_10.wav" "product/bgm/bgm.wav"
        mv "product/clean/vocal_vocal_all.wav.reformatted.wav_10.wav_10.wav" "product/clean/clean.wav"
    fi
fi

if [ $stage -le 2 ]; then   
    if [ "$item_count" -eq 1 ]; then
        cp -r product/clean/clean.wav "product/track/0/clean.wav"
        cp -r product/clean/clean.wav "product/onlywav/0/clean.wav"
        python product/one.py "product/onlywav/0/clean.wav" 5
        python preprocessing/cut/slicer.py --inp "product/onlywav/0" --opt_root "product/cut/0"
    else
        echo "以后再开发"
    fi
fi

if [ $stage -le 3 ]; then
    if [ "$item_count" -eq 1 ]; then
        for key in "${!dictionary[@]}"; do
            mkdir -p "features/$key"
        done   
        python preprocessing/asr/asr.py --asr_inp_dir 'product/cut/0' --asr_opt_dir 'features/0/asr' --asr_lang 'ja'

    else
        echo "以后再开发"
    fi
fi

if [ $stage -le 4 ]; then
    if [ "$item_count" -eq 1 ]; then   
        python features/get_text/sst.py --inp_text 'features/0/asr/0.list' --inp_wav_dir '/home/weizhenbian/ja2zh/product/cut/0' --exp_name ${dictionary[0]} --bert_pretrained_dir 'pretrain/chinese-roberta-wwm-ext-large' --exp_root 'features/0' --gpu_numbers '1,3,7'
        python features/get_audio/get_feature.py --inp_text 'features/0/asr/0.list' --inp_wav_dir '/home/weizhenbian/ja2zh/product/cut/0' --exp_name ${dictionary[0]} --ssl_pretrained_dir 'pretrain/chinese-hubert-base' --exp_root "features/0/${dictionary[0]}" --gpu_numbers '1,3,7'
        python features/get_emo/lan.py --inp_text 'features/0/asr/0.list' --exp_name ${dictionary[0]} --pretrained_s2G 'pretrain/s2G488k.pth' --s2config_path 'features/get_emo/s2.json' --exp_root 'features/0' --gpu_numbers '1,3,7'

    else
        echo "以后再开发"
    fi
fi

if [ $stage -le 5 ]; then
    if [ "$item_count" -eq 1 ]; then   
       mkdir -p 'model'
        python train/vits/train_sovit.py --exp_name ${dictionary[0]} --pretrained_s2G 'pretrain/s2G488k.pth' --pretrained_s2D 'pretrain/s2D488k.pth' --exp_root 'features/0' --sovits_weight_root 'model/0' --tmp 'train/vits/temp' 
        #python train/gpt/train_gpt.py --pretrained_s1 'pretrain/s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt' --exp_name ${dictionary[0]} --exp_root 'features/0' --config_path 'train/gpt/s1longer.yaml'

    else
        echo "以后再开发"
    fi
fi

if [ $stage -le 6 ]; then
    if [ "$item_count" -eq 1 ]; then    
        python train/gpt/train_gpt.py --pretrained_s1 'pretrain/s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt' --exp_name ${dictionary[0]} --exp_root 'features/0' --config_path 'train/gpt/s1longer.yaml'
    else
        echo "以后再开发"
    fi
fi

if [ $stage -le 7 ]; then
    if [ "$item_count" -eq 1 ]; then    
        python inf/inf.py --prompt_text '書類仕事には頭を使うから、当分が欲しくてね。お礼は仕事で返すよ。' --ref_wav_path 'product/cut/0/clean.wav_0002971520_0003179520.wav' --text '即使在室内也能补充水分和盐分。不要忘记经常休息。偶尔，我想我会忘记工作的忙碌，花点时间抬头看看月亮。我想如果我错过了我会后悔的。我想我会去训练室跑一会儿，增强体力。'
    else
        echo "以后再开发"
    fi
fi

if [ $stage -le 8 ]; then
    if [ "$item_count" -eq 1 ]; then
        #mkdir -p 'product/output'    
        rm -rf "features/0"
        #for key in "${!dictionary[@]}"; do
            #mkdir -p model/${dictionary[$key]}
            #mv model/${dictionary[$key]}* model/${dictionary[$key]}/
        #done
        rm -rf 'gweight.txt'
        rm -rf 'sweight.txt'
        rm -rf 'product/onlywav'
        rm -rf 'product/cut'
    else
        echo "以后再开发"
    fi
fi


if [ $stage -le 9 ]; then
    if [ "$item_count" -eq 1 ]; then    
        python product/cut.py 'product/track/0/clean.wav' "product/cut"
        python preprocessing/asr/asr.py --asr_inp_dir 'product/cut' --asr_opt_dir 'product/text' --asr_lang 'ja' 
    else
        echo "以后再开发"
    fi
fi

if [ $stage -le 10 ]; then
    if [ "$item_count" -eq 1 ]; then
        python product/trans.py product/text/cut.list product/text/cut2.list         
    else
        echo "以后再开发"
    fi
fi

if [ $stage -le 11 ]; then
    if [ "$item_count" -eq 1 ]; then
        python product/getref.py product/text/cut.list           
    else
        echo "以后再开发"
    fi
fi

if [ $stage -le 12 ]; then
    if [ "$item_count" -eq 1 ]; then
        python product/gettime.py product/text/cut2.list product/text/cut3.list
        python product/alltime.py product/text/cut3.list              
    else
        echo "以后再开发"
    fi
fi

if [ $stage -le 13 ]; then
    if [ "$item_count" -eq 1 ]; then
        mkdir -p 'product/output'
        python product/infer.py
                    
    else
        echo "以后再开发"
    fi
fi

if [ $stage -le 14 ]; then
    if [ "$item_count" -eq 1 ]; then
        mkdir -p 'product/final'
        python product/final.py product/output product/bgm/bgm.wav product/nonwav_video/nonwav.mp4 product/final/final.mp4
                    
    else
        echo "以后再开发"
    fi
fi


