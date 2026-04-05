#!/bin/bash
# ============================================================
# VideoAI Auto-Editing Tool - 安装脚本
# ============================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  VideoAI Auto-Editing Tool 安装程序${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查 macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}错误: 此程序仅支持 macOS${NC}"
    exit 1
fi

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 检查是否通过 git 安装
if [ -d ".git" ]; then
    echo -e "${GREEN}[1/5]${NC} 通过 Git 克隆安装 ✓"
else
    echo -e "${YELLOW}[1/5]${NC} 检测到手动下载模式"
fi

# ---------------------------------------------
# 1. 安装 Python 依赖
# ---------------------------------------------
echo -e ""
echo -e "${GREEN}[2/5]${NC} 安装 Python 依赖..."

if command -v pip3 &> /dev/null; then
    pip3 install -r requirements.txt
    echo -e "${GREEN}    Python 依赖安装完成 ✓${NC}"
else
    echo -e "${RED}错误: 未找到 pip3，请先安装 Python${NC}"
    echo -e "${YELLOW}提示: brew install python${NC}"
    exit 1
fi

# ---------------------------------------------
# 2. 检查 FFmpeg
# ---------------------------------------------
echo -e ""
echo -e "${GREEN}[3/5]${NC} 检查 FFmpeg..."

if command -v ffmpeg &> /dev/null; then
    FFMPEG_VERSION=$(ffmpeg -version 2>&1 | head -n 1)
    echo -e "${GREEN}    FFmpeg 已安装: $FFMPEG_VERSION${NC}"
else
    echo -e "${YELLOW}    FFmpeg 未安装，正在安装...${NC}"
    if command -v brew &> /dev/null; then
        brew install ffmpeg
        echo -e "${GREEN}    FFmpeg 安装完成 ✓${NC}"
    else
        echo -e "${RED}错误: 未找到 Homebrew，请先安装${NC}"
        echo -e "${YELLOW}提示: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"${NC}"
        exit 1
    fi
fi

# ---------------------------------------------
# 3. 创建必要目录
# ---------------------------------------------
echo -e ""
echo -e "${GREEN}[4/5]${NC} 创建工作目录..."

mkdir -p ~/Desktop/Materials 2>/dev/null || true
mkdir -p ~/VideoAI/data/{projects,materials,exports,chroma_db} 2>/dev/null || true
mkdir -p ~/VideoAI/logs 2>/dev/null || true

echo -e "${GREEN}    目录创建完成 ✓${NC}"

# ---------------------------------------------
# 4. 下载 AI 模型 (首次运行自动下载)
# ---------------------------------------------
echo -e ""
echo -e "${GREEN}[5/5]${NC} 准备 AI 模型..."
echo -e "${YELLOW}    注意: 首次运行时会自动下载所需模型${NC}"
echo -e "${YELLOW}    Whisper 模型 (~800MB)${NC}"
echo -e "${YELLOW}    OCR 模型 (~100MB)${NC}"
echo -e "${YELLOW}    VAD 模型 (~9MB)${NC}"

# ---------------------------------------------
# 完成
# ---------------------------------------------
echo -e ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}  安装完成！${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}下一步:${NC}"
echo -e "  1. 在 ~/Desktop/Materials/ 放入 PNG/JPG 素材"
echo -e "  2. 运行: ${GREEN}python3 src/main.py${NC}"
echo ""
echo -e "${YELLOW}或创建桌面快捷方式:${NC}"
echo -e "  echo 'cd \"$SCRIPT_DIR\" && python3 src/main.py' > ~/Desktop/VideoAI.command"
echo -e "  chmod +x ~/Desktop/VideoAI.command"
echo ""
echo -e "${BLUE}========================================${NC}"
