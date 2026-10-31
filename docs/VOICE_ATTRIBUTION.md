# Offline voice provenance

Optional local narration uses [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M), whose official model card identifies the weights as Apache-2.0, through [kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx), MIT, copyright 2025 github.com/thewh1teagle. The installed Python package includes its license. Model and package licenses are separate from source artwork permissions.

Pinned public [model-files-v1.1 release](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.1):

| File | Bytes | SHA-256 |
|---|---:|---|
| kokoro-v1.0.onnx | 325505369 | beb0d1848dee9a49da392cc3df26958d46cfa35d321edf434f52949153f0df3a |
| voices-v1.0.bin | 28214398 | bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d |

Profiles: am_michael, bm_george, af_heart. No voice cloning or inference API is used. Runtime checks the pinned bytes and fails closed when absent/changed. Public model downloading is an explicit setup command; rendering never downloads assets. Models and generated media remain ignored by Git. Voice quality and names still need human listening review; technical audio checks do not establish pronunciation accuracy.
