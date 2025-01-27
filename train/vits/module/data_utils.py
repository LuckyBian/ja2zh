import time
import logging
import os
import random
import traceback
import numpy as np
import torch
import torch.utils.data
from tqdm import tqdm

from module import commons
from module.mel_processing import spectrogram_torch

from text import cleaned_text_to_sequence

from utils import load_wav_to_torch, load_filepaths_and_text
import torch.nn.functional as F
from functools import lru_cache
import requests
from scipy.io import wavfile
from io import BytesIO
from my_utils import load_audio



class TextAudioSpeakerLoader(torch.utils.data.Dataset):
    """
    1) loads 音频, speaker id, 文字： 导入的数据为 2, 4, 5
    2: 拼音标点文本.txt       4: hubert提取的音频的编码   5: 重构的音频
    2) normalizes text and converts them to sequences of integers
    3) computes spectrograms from audio files.
    """

    def __init__(self, hparams, val=False):
        exp_dir = hparams.exp_dir
        #print(exp_dir)
        self.path2 = exp_dir+"/2-name2text-0.txt"
        self.path4 = exp_dir+"/4-cnhubert"
        self.path5 = exp_dir+"/5-wav32k"
        
        # 查看是否存在
        assert os.path.exists(self.path2)
        assert os.path.exists(self.path4)
        assert os.path.exists(self.path5)

        # 让 4和 5的名字相互对应
        names4 = set([name[:-3] for name in list(os.listdir(self.path4))])
        names5 = set(os.listdir(self.path5))

        self.phoneme_data = {}

        # 读取每一行数据
        with open(self.path2, "r", encoding="utf8") as f:
            lines = f.read().strip("\n").split("\n")

        # 读取到字典里：文件名：拼音编码
        for line in lines:
            tmp = line.split("\t")
            if (len(tmp) != 4):
                continue
            self.phoneme_data[tmp[0]] = [tmp[1]]

        # 找到共同的文件名，存成一个list
        self.audiopaths_sid_text = list(set(self.phoneme_data) & names4 & names5)
        tmp = self.audiopaths_sid_text

        # 查看文件数量
        leng = len(tmp)
        min_num = 100

        # 如果数据不足，则进行扩充
        if (leng < min_num):
            self.audiopaths_sid_text = []
            for _ in range(max(2, int(min_num / leng))):
                self.audiopaths_sid_text += tmp

        # 设置一系列参数
        self.max_wav_value = hparams.max_wav_value
        self.sampling_rate = hparams.sampling_rate
        self.filter_length = hparams.filter_length
        self.hop_length = hparams.hop_length
        self.win_length = hparams.win_length
        self.sampling_rate = hparams.sampling_rate
        self.val = val

        random.seed(1234)
        random.shuffle(self.audiopaths_sid_text)

        # 输出文件数量
        print("phoneme_data_len:", len(self.phoneme_data.keys()))
        print("wav_data_len:", len(self.audiopaths_sid_text))

        audiopaths_sid_text_new = []
        lengths = []
        skipped_phone = 0
        skipped_dur = 0

        # 对每个文件进行处理，path为文件名
        for audiopath in tqdm(self.audiopaths_sid_text):
            try:
                # 获取拼音
                phoneme = self.phoneme_data[audiopath][0]
                
                # 对拼音进行拆分
                phoneme = phoneme.split(' ')

                # 将不同的拼音转换成编码
                phoneme_ids = cleaned_text_to_sequence(phoneme)
            except Exception:
                print(f"{audiopath} not in self.phoneme_data !")
                skipped_phone += 1
                continue

            # 计算文件大小
            size = os.path.getsize("%s/%s" % (self.path5, audiopath))
            duration = size / self.sampling_rate / 2

            # 如果为空，则直接跳过
            if duration == 0:
                print(f"Zero duration for {audiopath}, skipping...")
                skipped_dur += 1
                continue

            # 防止过长或者过短
            if 54 > duration > 0.6 or self.val:

                # 得到文件名和对应拼音的id
                audiopaths_sid_text_new.append([audiopath, phoneme_ids])
                lengths.append(size // (2 * self.hop_length))
            else:
                skipped_dur += 1
                continue

        print("skipped_phone: ", skipped_phone, ", skipped_dur: ", skipped_dur)
        print("total left: ", len(audiopaths_sid_text_new))

        assert len(audiopaths_sid_text_new) > 1  # 至少能凑够batch size，这里todo

        self.audiopaths_sid_text = audiopaths_sid_text_new
        self.lengths = lengths

    def get_audio_text_speaker_pair(self, audiopath_sid_text):

        # 得到一个文件的  文件名和对应的拼音id
        audiopath, phoneme_ids = audiopath_sid_text

        # 装换成张量
        text = torch.FloatTensor(phoneme_ids)

        try:
            # 拿到stft频谱和音频张量
            spec, wav = self.get_audio("%s/%s" % (self.path5, audiopath))

            with torch.no_grad():

                # 得到音频在潜在空间的编码
                ssl = torch.load("%s/%s.pt" % (self.path4, audiopath), map_location="cpu")

                # 如果维度不一样，则进行填充
                # 查看时间维度上是否一样
                if (ssl.shape[-1] != spec.shape[-1]):
                    typee = ssl.dtype
                    ssl = F.pad(ssl.float(), (0, 1), mode="replicate").to(typee)
                ssl.requires_grad = False
        except:
            traceback.print_exc()
            spec = torch.zeros(1025, 100)
            wav = torch.zeros(1, 100 * self.hop_length)
            ssl = torch.zeros(1, 768, 100)
            text = text[-1:]
            print("load audio or ssl error!!!!!!", audiopath)

            # 最后返回的是： 音频编码， stft图谱， 音频张量， 拼音张量
        return (ssl, spec, wav, text)

    def get_audio(self, filename):
        # 将音频导入
        audio_array = load_audio(filename, self.sampling_rate)

        # 转换成张量
        audio = torch.FloatTensor(audio_array)

        audio_norm = audio

        # 添加一个新的维度，批次维度
        audio_norm = audio_norm.unsqueeze(0)

        # 得到频谱
        spec = spectrogram_torch(audio_norm, self.filter_length, self.sampling_rate, self.hop_length, self.win_length,
                                  center=False)
        
        # 去除一个维度
        spec = torch.squeeze(spec, 0)

        # 返回频谱和audio张量
        return spec, audio_norm

    def get_sid(self, sid):
        sid = torch.LongTensor([int(sid)])
        return sid

    def __getitem__(self, index):
        # with torch.no_grad():
        return self.get_audio_text_speaker_pair(self.audiopaths_sid_text[index])

    def __len__(self):
        return len(self.audiopaths_sid_text)

    def random_slice(self, ssl, wav, mel):
        assert abs(ssl.shape[-1] - wav.shape[-1] // self.hop_length) < 3, (
        "first", ssl.shape, wav.shape)

        len_mel = mel.shape[1]
        if self.val:
            reference_mel = mel[:, :len_mel // 3]
            return reference_mel, ssl, wav, mel
        dir = random.randint(0, 1)
        sep_point = random.randint(int(len_mel // 3), int(len_mel // 3 * 2))

        if dir == 0:
            reference_mel = mel[:, :sep_point]
            ssl = ssl[:, :, sep_point:]
            wav2 = wav[:, sep_point * self.hop_length:]
            mel = mel[:, sep_point:]
        else:
            reference_mel = mel[:, sep_point:]
            ssl = ssl[:, :, :sep_point]
            wav2 = wav[:, :sep_point * self.hop_length]
            mel = mel[:, :sep_point]

        assert abs(ssl.shape[-1] - wav2.shape[-1] // self.hop_length) < 3, (
        ssl.shape, wav.shape, wav2.shape, mel.shape, sep_point, self.hop_length, sep_point * self.hop_length, dir)
        return reference_mel, ssl, wav2, mel


class TextAudioSpeakerCollate():
    """ Zero-pads model inputs and targets
    """

    def __init__(self, return_ids=False):
        self.return_ids = return_ids

    def __call__(self, batch):
        """Collate's training batch from normalized text, audio and speaker identities
        PARAMS
        ------
        batch: [text_normalized, spec_normalized, wav_normalized, sid]
        """
        # Right zero-pad all one-hot text sequences to max input length
        _, ids_sorted_decreasing = torch.sort(
            torch.LongTensor([x[1].size(1) for x in batch]),
            dim=0, descending=True)

        max_ssl_len = max([x[0].size(2) for x in batch])
        max_ssl_len = int(2 * ((max_ssl_len // 2) + 1))
        max_spec_len = max([x[1].size(1) for x in batch])
        max_spec_len = int(2 * ((max_spec_len // 2) + 1))
        max_wav_len = max([x[2].size(1) for x in batch])
        max_text_len = max([x[3].size(0) for x in batch])

        ssl_lengths = torch.LongTensor(len(batch))
        spec_lengths = torch.LongTensor(len(batch))
        wav_lengths = torch.LongTensor(len(batch))
        text_lengths = torch.LongTensor(len(batch))

        spec_padded = torch.FloatTensor(len(batch), batch[0][1].size(0), max_spec_len)
        wav_padded = torch.FloatTensor(len(batch), 1, max_wav_len)
        ssl_padded = torch.FloatTensor(len(batch), batch[0][0].size(1), max_ssl_len)
        text_padded = torch.LongTensor(len(batch), max_text_len)

        spec_padded.zero_()
        wav_padded.zero_()
        ssl_padded.zero_()
        text_padded.zero_()

        for i in range(len(ids_sorted_decreasing)):
            row = batch[ids_sorted_decreasing[i]]

            ssl = row[0]
            ssl_padded[i, :, :ssl.size(2)] = ssl[0, :, :]
            ssl_lengths[i] = ssl.size(2)

            spec = row[1]
            spec_padded[i, :, :spec.size(1)] = spec
            spec_lengths[i] = spec.size(1)

            wav = row[2]
            wav_padded[i, :, :wav.size(1)] = wav
            wav_lengths[i] = wav.size(1)

            text = row[3]
            text_padded[i, :text.size(0)] = text
            text_lengths[i] = text.size(0)

        return ssl_padded, ssl_lengths, spec_padded, spec_lengths, wav_padded, wav_lengths, text_padded, text_lengths


class DistributedBucketSampler(torch.utils.data.distributed.DistributedSampler):

    def __init__(self, dataset, batch_size, boundaries, num_replicas=None, rank=None, shuffle=True):
        super().__init__(dataset, num_replicas=num_replicas, rank=rank, shuffle=shuffle)
        self.lengths = dataset.lengths
        self.batch_size = batch_size
        self.boundaries = boundaries

        self.buckets, self.num_samples_per_bucket = self._create_buckets()
        self.total_size = sum(self.num_samples_per_bucket)
        self.num_samples = self.total_size // self.num_replicas

    def _create_buckets(self):
        buckets = [[] for _ in range(len(self.boundaries) - 1)]
        for i in range(len(self.lengths)):
            length = self.lengths[i]
            idx_bucket = self._bisect(length)
            if idx_bucket != -1:
                buckets[idx_bucket].append(i)

        i = len(buckets) - 1
        while i >= 0:
            if len(buckets[i]) == 0:
                buckets.pop(i)
                self.boundaries.pop(i + 1)
            i -= 1

        num_samples_per_bucket = []
        for i in range(len(buckets)):
            len_bucket = len(buckets[i])
            total_batch_size = self.num_replicas * self.batch_size
            rem = (total_batch_size - (len_bucket % total_batch_size)) % total_batch_size
            num_samples_per_bucket.append(len_bucket + rem)
        return buckets, num_samples_per_bucket

    def __iter__(self):
        g = torch.Generator()
        g.manual_seed(self.epoch)

        indices = []
        if self.shuffle:
            for bucket in self.buckets:
                indices.append(torch.randperm(len(bucket), generator=g).tolist())
        else:
            for bucket in self.buckets:
                indices.append(list(range(len(bucket))))

        batches = []
        for i in range(len(self.buckets)):
            bucket = self.buckets[i]
            len_bucket = len(bucket)
            ids_bucket = indices[i]
            num_samples_bucket = self.num_samples_per_bucket[i]

            rem = num_samples_bucket - len_bucket
            ids_bucket = ids_bucket + ids_bucket * (rem // len_bucket) + ids_bucket[:(rem % len_bucket)]

            ids_bucket = ids_bucket[self.rank::self.num_replicas]

            for j in range(len(ids_bucket) // self.batch_size):
                batch = [bucket[idx] for idx in ids_bucket[j * self.batch_size:(j + 1) * self.batch_size]]
                batches.append(batch)

        if self.shuffle:
            batch_ids = torch.randperm(len(batches), generator=g).tolist()
            batches = [batches[i] for i in batch_ids]
        self.batches = batches

        assert len(self.batches) * self.batch_size == self.num_samples
        return iter(self.batches)

    def _bisect(self, x, lo=0, hi=None):
        if hi is None:
            hi = len(self.boundaries) - 1

        if hi > lo:
            mid = (hi + lo) // 2
            if self.boundaries[mid] < x and x <= self.boundaries[mid + 1]:
                return mid
            elif x <= self.boundaries[mid]:
                return self._bisect(x, lo, mid)
            else:
                return self._bisect(x, mid + 1, hi)
        else:
            return -1

    def __len__(self):
        return self.num_samples // self.batch_size