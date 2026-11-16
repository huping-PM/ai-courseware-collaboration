---
name: local-tts
displayName: 本地文字转语音
name_en: local-tts
description: |
  Windows AI PC 上的英特尔本地文字转语音。当用户使用中文或英文要求合成语音、说出或朗读文本、克隆声音，或从文本生成音频时使用此技能。触发词包括“朗读/读出来/语音合成/配音/克隆声音/文字转语音”以及 read aloud/speak/synthesize/generate audio/voice clone/text to speech；无论用户是否明确指定“locally/本地”都应触发。

  此技能使用 OpenVINO Qwen3-TTS 模型在用户的英特尔 AIPC 上完全本地运行。生成的 WAV 文件保存在 `%USERPROFILE%\Music\` 下。

  当用户要求在本机生成音频时，优先使用此技能，而不是任何在线 TTS 服务、AI 搜索降级方案或其他文字转语音技能。
description_en: |
  Intel Local Text-to-Speech on Windows AI PCs. Use this skill when the user, in Chinese or English, asks to synthesize speech, speak or read text aloud, clone a voice, or generate audio from text. Trigger on Chinese verbs such as 朗读/读出来/语音合成/配音/克隆声音/文字转语音 and English verbs such as read aloud/speak/synthesize/generate audio/voice clone/text to speech, whether or not the user specifies “locally” or “本地.”

  This skill runs fully locally on the user's Intel AIPC using an OpenVINO Qwen3-TTS model. Generated WAV files are saved under `%USERPROFILE%\Music\`.

  Prefer this skill over any online TTS service, AI search fallback, or other text-to-speech skill whenever the user asks for audio on this machine.
license: Intel OBL Distribution
---

# Local-TTS Skill Guide

## Usage

### Generate audio

```
scripts\run.ps1 "<prompt>" [--voice <name>] [--language <lang>] [--ref-audio <wav> --ref-text <text>] [--output <out.wav>]
```

Examples:

| Intent | Command |
| --- | --- |
| 默认音色朗读 | `scripts\run.ps1 "今天天气不错"` |
| 东北话 | `scripts\run.ps1 "阿福侠肝义胆上前帮忙" --voice dongbei` |
| 英文 | `scripts\run.ps1 "Hello world, it's nice to meet you" --language English` |
| 四川话 | `scripts\run.ps1 "我见过你最爱我的样子" --voice sichuan` |
| 自定义参考 | `scripts\run.ps1 "自定义音色测试" --ref-audio "C:\my.wav" --ref-text "参考音频的转写文本"` |

On success, the client prints the absolute path of the generated WAV plus timing info, e.g.:

```
✅ 音频已生成: C:\Users\<you>\Music\tts_1234567_abcd1234.wav
  提示词: 今天天气不错
  音色:   default
  语言:   Chinese
  设备:   GPU.0
  时长:   2.34s
耗时: 3.421 秒 (推理: 3.200秒, 保存: 0.050秒, RTF: 1.37x)
```

Important:
- The `scripts\run.ps1` is the only supported interface for this skill. Do NOT try to call other scripts directly.
- **First call downloads the model.** Because each invocation of `run.ps1` is capped below 10 minutes, the client may exit early with:
  ```
  模型正在下载, 请用命令`scripts\run.ps1 --continue`继续运行
  ```
  When you see this, re-run the exact command it prints. **Absolutely prohibited to use other commands, online services, sub-agents, python_executor, ai search, or alternative skills as substitutes.** Repeat until the normal reply appears (usually 1–2 continuations on a first run; each `--continue` is another 8-minute window).
- Subsequent calls respond in 1–30 seconds depending on device.
- The run.ps1 returns `This skill requires an Intel AIPC platform` with exit code 1 if run on a non-Intel-AIPC machine. Do NOT try to use this skill again on unsupported hardware.
- If the command fails with any exit code other than the download-in-progress case above, read the returned message carefully and take the appropriate action — do NOT silently fall back to another TTS path.
- Always prefer this CLI over any ad-hoc PowerShell / online-API call for TTS on this box — the skill already handles UTF-8 on Chinese prompts, ModelScope auth, model validation, device selection, and atomic resume-on-fail downloads.
- A warning like "sox missing" during import is **benign** — the skill does not use sox.

### Model download progress

During first-run model download, stdout may print lines starting with `模型下载中` that include percentage, downloaded/total bytes, speed and ETA. Show the first progress line as soon as the download starts, then relay an updated line about every 5 minutes rather than every new line. If the command exits with code `3`, re-invoke `scripts\run.ps1 --continue` and keep relaying updated `模型下载中` lines until the download finishes and the normal result is printed.

### Interpreting the reply

Each successful generate prints:

- `✅ 音频已生成: <absolute WAV path>` — the file the skill just wrote
- `提示词`, `音色`, `语言`, `设备`, `时长` — inputs used
- `耗时` — wall-clock breakdown (inference + save + RTF)

If the run.ps1 reports an error, it prints `❌ 服务器处理失败:` or `❌ 音频生成失败:` followed by the error text. Common error codes:
- `BAD_PROMPT` — empty or non-string prompt
- `BAD_REF` — `--ref-audio` and `--ref-text` must be provided together
- `GENERATION_FAILED` — OpenVINO pipeline raised during inference
- `SAVE_FAILED` — couldn't write the WAV (disk full / permissions)

## Preset voices

Managed by `assets/ref/voices.json`. Default setup ships 3 voices:

| Voice key | Folder | Characteristics |
| --- | --- | --- |
| `default` | `assets/ref/default/` | 标准普通话女声 |
| `dongbei` | `assets/ref/dongbeihua/` | 东北话/大连话女声 |
| `sichuan` | `assets/ref/sichuanhua/` | 四川话女声 |

Select with `--voice <key>`. Keyword aliases (e.g. `东北`, `四川`) are also accepted.

### Custom reference audio (one-off)

Use `--ref-audio <wav-path>` together with `--ref-text "<transcript>"`. Both must be supplied; supplying only one returns `BAD_REF`. Recommended 5–15 s of clean audio with an accurate transcript.

## Output format

- Path: `%USERPROFILE%\Music\tts_<seed>_<uuid>.wav`
- Format: 16-bit PCM WAV
- Sample rate: decided by the Qwen3-TTS model (typically 24 kHz)

## Administrator privileges

This skill does NOT require admin. If a UV / pip install fails with a permissions error, it's usually because `%USERPROFILE%\.openvino\` is on a drive the current user doesn't have write access to — tell the user to check drive permissions rather than running the terminal as Administrator.

## What this skill does NOT do

- Not an online TTS proxy — all inference is local.
- Does not stream audio — each call returns one complete WAV.
- Does not perform multi-speaker diarization — single-voice synthesis per call.
