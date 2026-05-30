# Use DaoCloud mirrored vllm image for China region for gpu with Ampere architecture and above (Compute Capability>=8.0)
# Compute Capability version query (https://developer.nvidia.com/cuda-gpus)
ARG VLLM_OPENAI_IMAGE=docker.m.daocloud.io/vllm/vllm-openai:v0.11.2
FROM ${VLLM_OPENAI_IMAGE}

# Use the official vllm image
# FROM vllm/vllm-openai:v0.9.2

# Use DaoCloud mirrored vllm image for China region for gpu with Turing architecture and below (Compute Capability<8.0)
# FROM docker.m.daocloud.io/vllm/vllm-openai:v0.10.2

# Use the official vllm image
# FROM vllm/vllm-openai:v0.10.2

# Install libgl for opencv support & Noto fonts for Chinese characters
RUN apt-get update && \
    apt-get install -y \
        fonts-noto-core \
        fonts-noto-cjk \
        fontconfig \
        libgl1 && \
    fc-cache -fv && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install mineru latest
RUN python3 -m pip install -U 'mineru[core]' -i https://mirrors.aliyun.com/pypi/simple --break-system-packages && \
    python3 -m pip cache purge

RUN python3 - <<'PY'
import pathlib
import re
import site

def patch_file(path: pathlib.Path) -> bool:
    content = path.read_text(encoding="utf-8")
    if "exist_ok=True" in content:
        return False
    pattern = r'AutoConfig\.register\(\s*["\']aimv2["\']\s*,\s*AIMv2Config\s*\)'
    if not re.search(pattern, content):
        return False
    content = re.sub(
        pattern,
        'AutoConfig.register("aimv2", AIMv2Config, exist_ok=True)',
        content,
        count=1,
    )
    path.write_text(content, encoding="utf-8")
    return True

for base in site.getsitepackages():
    candidate = pathlib.Path(base) / "vllm" / "transformers_utils" / "configs" / "ovis.py"
    if candidate.exists():
        patch_file(candidate)
raise SystemExit(0)
PY

# Download models and update the configuration file
RUN /bin/bash -c "mineru-models-download -s modelscope -m all"

# Set the entry point to activate the virtual environment and run the command line tool
ENTRYPOINT ["/bin/bash", "-c", "export MINERU_MODEL_SOURCE=local && exec \"$@\"", "--"]
