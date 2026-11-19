# -*- coding: utf-8 -*-
"""处理 Kenney 玻璃钟声：裁静音尾 + 重采样到 22.05kHz 单声道，输出紧凑 WAV。

纯标准库实现，无需 ffmpeg。
输入: build/vendor/audio/glass_XXX.wav (44100Hz 16bit mono)
输出: build/vendor/audio/chime_break.wav  (单轮结束，短促)
      build/vendor/audio/chime_done.wav   (全部完成，较长余韵)
"""
import os
import struct
import wave

AUDIO = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vendor', 'audio')
TARGET_SR = 22050


def load(path):
    w = wave.open(path, 'rb')
    sr = w.getframerate()
    n = w.getnframes()
    raw = w.readframes(n)
    w.close()
    samples = struct.unpack('<%dh' % n, raw)
    return samples, sr


def trim_tail(samples, tail_ratio=0.01):
    peak = max(abs(s) for s in samples)
    thr = peak * tail_ratio
    end = len(samples)
    for i in range(len(samples) - 1, -1, -1):
        if abs(samples[i]) > thr:
            end = i + 1
            break
    # 留一点点余量，避免切太狠
    return samples[:end + 50]


def resample(samples, src_sr, dst_sr):
    """线性插值重采样。"""
    if src_sr == dst_sr:
        return samples
    ratio = src_sr / dst_sr
    out = []
    n_out = int(len(samples) / ratio)
    for i in range(n_out):
        pos = i * ratio
        i0 = int(pos)
        i1 = min(i0 + 1, len(samples) - 1)
        frac = pos - i0
        out.append(int(samples[i0] * (1 - frac) + samples[i1] * frac))
    return out


def save(path, samples, sr):
    w = wave.open(path, 'wb')
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(sr)
    w.writeframes(struct.pack('<%dh' % len(samples), *samples))
    w.close()


def process(src_name, dst_name):
    src = os.path.join(AUDIO, src_name)
    dst = os.path.join(AUDIO, dst_name)
    samples, sr = load(src)
    samples = trim_tail(samples)
    samples = resample(samples, sr, TARGET_SR)
    save(dst, samples, TARGET_SR)
    print(f'{dst_name}: {len(samples)} 帧 @ {TARGET_SR}Hz = {len(samples)/TARGET_SR:.3f}s, '
          f'{os.path.getsize(dst)} 字节')


if __name__ == '__main__':
    process('glass_002.wav', 'chime_break.wav')
    process('glass_004.wav', 'chime_done.wav')
    print('完成。')
